"""
Единый интерфейс к микрофону: .read() → bytes (16-бит, 16 kHz, mono)
На Android работает через Audiostream, на desktop — через sounddevice.
Логи максимально подробные: smicro.debug() пишет размер пришедшего чанка.
"""
import asyncio, os, platform, logging, shutil, subprocess, sys
from typing import AsyncGenerator

log = logging.getLogger("mic")

def is_termux() -> bool:
    return os.environ.get("PREFIX", "").startswith("/data/data/com.termux")

async def termux_stream():
    """
    Захват 16 kHz 16-bit mono через PulseAudio → parec.
    Требует: `pulseaudio`, `pulseaudio-tools`.
    """
    # 1) гарантируем запущенный демон
    if shutil.which("pulseaudio") is None:
        raise RuntimeError("pkg install pulseaudio pulseaudio-tools")
    subprocess.run(["pulseaudio", "--start", "--exit-idle-time=-1"],
                   stdout=subprocess.DEVNULL)
    # 2) загружаем модуль микрофона (выдаст запрос прав)
    subprocess.run(["pactl", "load-module", "module-sles-source"],
                   check=False)
    # 3) читаем поток
    proc = await asyncio.create_subprocess_exec(
        "parec", "--format=s16le", "--rate=16000", "--channels=1",
        stdout=asyncio.subprocess.PIPE)
    try:
        while True:
            data = await proc.stdout.read(2048)      # 1024 frames
            if not data:
                break
            log.debug("Mic chunk %d bytes", len(data))
            yield data
    finally:
        proc.terminate()

def is_android() -> bool:
    return "ANDROID_ARGUMENT" in sys.argv or platform.system() == "Android"

async def android_stream() -> AsyncGenerator[bytes, None]:
    from audiostream import get_input
    q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=50)

    def _cb(buf: bytes):
        if not q.full():
            q.put_nowait(buf)
        log.debug("Mic chunk %d bytes queued", len(buf))

    mic = get_input(callback=_cb, rate=16_000, channels=1,
                    encoding=16, buffersize=512)
    mic.start()
    try:
        while True:
            yield await q.get()
    finally:
        mic.stop()

async def desktop_stream() -> AsyncGenerator[bytes, None]:
    import sounddevice as sd, numpy as np
    q: asyncio.Queue[bytes] = asyncio.Queue(maxsize=50)

    def _cb(indata, _frames, _time, _status):
        if _status:
            log.warning("sounddevice status: %s", _status)
        q.put_nowait(indata.tobytes())
        log.debug("Mic chunk %d bytes queued", indata.nbytes)

    with sd.RawInputStream(samplerate=16_000, blocksize=512,
                           channels=1, dtype="int16", callback=_cb):
        while True:
            yield await q.get()


def get_mic_stream():
    if is_termux():
        return termux_stream()
    elif platform.system() == "Android":
        return android_stream()
    else:
        return desktop_stream()
