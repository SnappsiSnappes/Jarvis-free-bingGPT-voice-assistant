import asyncio
import json
import logging
import threading
import traceback
import websockets

from display import DisplayDriver, DisplayItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebsocketDisplayDriver(DisplayDriver):
    """
    WebSocket-драйвер с хранением последнего состояния по kind,
    и рассылкой его новому клиенту сразу после подключения.
    """

    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        # храним последнее DisplayItem по его kind
        self._last_items: dict[str, DisplayItem] = {}

        logger.info("[INIT] Starting WS server thread")
        self._thread = threading.Thread(
            target=self._run_server_loop,
            name="WS-Server-Thread",
            daemon=True
        )
        self._thread.start()

    def _run_server_loop(self):
        try:
            asyncio.run(self._server_main())
        except Exception as e:
            logger.error(f"[SRV][ERROR] asyncio.run failure: {e}")
            logger.error(traceback.format_exc())

    async def _server_main(self):
        """
        Поднимаем WebSocket-сервер и ждём навсегда.
        """
        # С 12-й версии websockets на Windows есть баг с двойным write_eof().
        # Поэтому принудительно понижаем до 11.0 **или** ловим исключение ниже.
        import websockets
        logger.info("[INFO] websockets %s", websockets.__version__)
        async with websockets.serve(
                self._handler,
                self.host, self.port,
                subprotocols=["arduino"],
                # Большие таймауты помогают понять, кто первый закрыл соединение
                ping_interval=4,
                ping_timeout=2,
        ):
            logger.info(f"[SRV] WebSocket server started on {self.host}:{self.port}")
            await asyncio.Future()

    async def _handler(self, ws: websockets.WebSocketServerProtocol):
        # Новый клиент подключился
        logger.info(f"[WS] Client connected: {ws.remote_address}")
        self.clients.add(ws)

        # Отправляем ему всё хранимое состояние
        for item in self._last_items.values():
            try:
                await ws.send(json.dumps({
                    "kind": item.kind,
                    "payload": item.payload
                }))
                logger.debug(f"[WS] sent cached {item.kind} to {ws.remote_address}")
            except Exception:
                logger.exception(f"[WS] failed to send cached {item.kind}")

        try:
            await ws.wait_closed()
        finally:
            self.clients.remove(ws)
            logger.info(f"[WS] Client disconnected: {ws.remote_address}")

    def draw(self, item: DisplayItem) -> None:
        # Сохраняем состояние
        self._last_items[item.kind] = item

        # Готовим JSON
        msg = {
            "kind":    item.kind,
            "payload": item.payload,
        }
        data = json.dumps(msg)

        logger.info("[WS→CLIENT] %s", data)

        # Рассылаем всем клиентам
        async def _send_all():
            if not self.clients:
                logger.debug("[DRAW] No WS clients — skipping send")
                return
            await asyncio.gather(*(ws.send(data) for ws in self.clients),
                                  return_exceptions=True)

        # Планируем отправку в loop сервера
        # Берём loop из любого ws, если есть
        if self.clients:
            server_loop = next(iter(self.clients)).loop
            asyncio.run_coroutine_threadsafe(_send_all(), server_loop)
        else:
            logger.debug("[DRAW] No clients connected yet")

    def process_events(self) -> None:
        # не нужно в основном loop
        return

    def close(self):
        # При необходимости можно добавить корректную остановку сервера
        pass
