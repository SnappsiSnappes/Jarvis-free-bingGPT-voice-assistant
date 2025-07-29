from __future__ import annotations

import atexit
import json
import threading
import time
from queue import Empty, Queue
from typing import Optional

import serial
from serial.tools import list_ports

from logging_config import setup_logging

from display import DisplayDriver, DisplayItem

log = setup_logging(__name__)

# -----------------------------------------------------------------------------
# Helper – autodetect serial port
# -----------------------------------------------------------------------------

def _find_default_port() -> str:
    """Return the first serial port that looks like an M5Stack bridge."""
    from sys import platform

    if platform.startswith("linux"):
        return "/dev/ttyUSB0"
    if platform.startswith("darwin"):
        return "/dev/cu.SLAB_USBtoUART"

    # Windows: choose first COM port with known VID/PID
    VIDS_PIDS = {(0x10C4, 0xEA60), (0x1A86, 0x7523), (0x1A86, 0x55D4)}
    for p in list_ports.comports():
        if (p.vid, p.pid) in VIDS_PIDS:
            return p.device  # pragma: no cover
    log.error("M5Stack USB‑UART bridge not found. Please specify port explicitly.")
    raise RuntimeError("M5Stack USB‑UART not found")

# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

class SerialDisplayDriver(DisplayDriver):
    """Display driver that communicates with M5Stack over USB serial."""

    def __init__(
        self,
        port: Optional[str] = None,
        baud: int = 921_600,
        reconnect_delay: float = 2.0,
    ) -> None:
        self.port = port or _find_default_port()
        self.baud = baud
        self.reconnect_delay = reconnect_delay
        self._last: dict[str, DisplayItem] = {}
        self._inq: Queue[tuple[str, str]] = Queue()
        self._running = threading.Event()
        self._running.set()
        self.ser: Optional[serial.Serial] = None
        self._open_serial()  # blocks until port is opened
        atexit.register(self.close)

    def draw(self, item: DisplayItem) -> None:
        """Transmit *item* to display and cache it for reconnect."""
        self._last[item.kind] = item
        self._send_item(item)

    def process_events(self) -> None:
        """Process incoming events from M5Stack."""
        try:
            while True:
                kind, payload = self._inq.get_nowait()
                self.on_event(kind, payload)
        except Empty:
            pass

    def _push_cache(self) -> None:
        """Resend all cached frames after reconnect."""
        log.info("Resending %d cached frames", len(self._last))
        for it in self._last.values():
            self._send_item(it)

    def on_event(self, kind: str, payload: str) -> None:
        """Handle events from M5Stack. Override as needed."""
        log.debug("Event received kind=%s payload=%s", kind, payload)
        if kind == "hello":
            self._push_cache()

    def _open_serial(self) -> None:
        """Open serial connection and start reader thread."""
        while self._running.is_set():
            try:
                self.ser = serial.Serial(
                    self.port,
                    self.baud,
                    timeout=1,
                    dsrdtr=False,
                    rtscts=False,
                )
                log.info("Serial opened %s @%d", self.port, self.baud)
                break
            except serial.SerialException as exc:
                log.warning(
                    "Serial open failed: %s. Retrying in %.1fs", exc, self.reconnect_delay
                )
                time.sleep(self.reconnect_delay)

        # Spawn reader thread
        self._rx = threading.Thread(target=self._reader, daemon=True)
        self._rx.start()

        # Give device time to boot and push cache
        time.sleep(0.1)
        for it in self._last.values():
            self._send_item(it)

    def _send_item(self, item: DisplayItem) -> None:
        """Serialize item as JSON and write to serial port."""
        if not self.ser or not self.ser.is_open:
            log.debug("Serial port not open, dropping frame kind=%s", item.kind)
            return
        msg = json.dumps({"kind": item.kind, "payload": item.payload})
        log.debug("SER→M5 %s", msg)
        try:
            self.ser.write(msg.encode() + b"\n")
        except serial.SerialException as exc:
            log.error("Write error: %s", exc)

    def _reader(self) -> None:
        """Background thread: read lines, parse JSON, enqueue events."""
        buf = b""
        while self._running.is_set():
            try:
                chunk = self.ser.read(self.ser.in_waiting or 1)
                if not chunk:
                    continue
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="replace").strip()
                    log.debug("M5→SER %s", line)
                    if "=== Device booting ===" in line or line.startswith("rst:"):
                        log.info("Board reboot detected, pushing cache")
                        self._push_cache()
                    if not line.startswith("{"):
                        continue
                    try:
                        msg = json.loads(line)
                        kind = msg.get("kind", "")
                        payload = msg.get("payload", "")
                        self._inq.put((kind, payload))
                        self.on_event(kind, payload)
                    except json.JSONDecodeError:
                        log.error("Bad JSON from M5: %s", line)
            except (serial.SerialException, AttributeError) as exc:
                if not self._running.is_set():
                    break
                log.warning("Connection lost: %s", exc)
                try:
                    if self.ser and self.ser.is_open:
                        self.ser.close()
                finally:
                    time.sleep(self.reconnect_delay)
                    self._open_serial()
                    buf = b""

    def close(self) -> None:
        """Clean up serial connection and reader thread."""
        if not self._running.is_set():
            return
        self._running.clear()
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            log.exception("Error closing serial port")
        if hasattr(self, "_rx") and self._rx.is_alive():
            self._rx.join(timeout=1)
        log.info("Serial closed %s", self.port)
