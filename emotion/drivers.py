from events.broker import EventBroker
from display import get_driver, DisplayItem
from emotion.state import Emotion

class EmotionDisplayDriver:
    """
    Драйвер, подписывается на смену эмоции и
    отображает её на дисплее через базовый DisplayDriver.
    """
    def __init__(self, broker: EventBroker):
        self._broker = broker
        # получаем базовый драйвер (Websocket, Windows, etc.)
        self._driver = get_driver()
        # подписываемся на событие
        self._broker.subscribe('emotion_changed', self._on_emotion_changed)

    def _on_emotion_changed(self, emotion: Emotion):
        """
        Callback: рисуем иконку текущей эмоции.
        """
        print(f"[EMO][Driver] Received emotion_changed → drawing: {emotion.value}")
        item = DisplayItem(
            kind="emotion",
            payload=emotion.value   # строковый ключ, например "happy"
        )
        self._driver.draw(item)
