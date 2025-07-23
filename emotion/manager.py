import threading
import time
from events.broker import EventBroker
from emotion.state import EmotionState, Emotion


class EmotionManager:
    """
    Управляет сменой эмоций робота и взаимодействием с EventBroker.
    """
    def __init__(self, broker: EventBroker, idle_interval: float = 5.0):
        self._broker = broker
        self._state = EmotionState()
        self._idle_interval = idle_interval
        self._stop_event = threading.Event()
        self._idle_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self._busy_event = threading.Event()

        # Подписываемся на события
        self._broker.subscribe('user_query_started', self._on_query_started)
        self._broker.subscribe('user_query_ended', self._on_query_ended)
        # Будем слушать сенсорные события по мере добавления
        # self._broker.subscribe('sensor_event', self._on_sensor_event)

    def start(self):
        """Опубликовать начальное состояние и запустить фоновый цикл."""
        # сразу отрисовать текущее (NEUTRAL)
        self._publish_emotion(self._state.current)
        # а затем — запустить idle-цикл
        self._idle_thread.start()

    def stop(self):
        """Остановить фоновый цикл (если нужно)."""
        self._stop_event.set()
        self._idle_thread.join()

    def _idle_loop(self):
        """Фоновый цикл: каждые idle_interval сек публикует новую эмоцию из idle-режима."""
        while not self._stop_event.is_set():
            if self._busy_event.is_set():
                time.sleep(0.1)
                continue
            next_emotion = self._state.get_next_idle()
            print(f"[EMO][Manager] Idle → new emotion: {next_emotion.value}")
            self._publish_emotion(next_emotion)
            # Ожидаем или прерываем
            waited = 0.0
            step = 0.1
            while waited < self._idle_interval:
                if self._stop_event.is_set() or self._busy_event.is_set():
                    return
                time.sleep(step)
                waited += step

    def _on_query_started(self, **kwargs):
        """При начале обработки пользовательского запроса — эмоция THINKING."""
        self._busy_event.set()
        emo = self._state.get_thinking()
        print(f"[EMO][Manager] Event user_query_started → emotion: {emo.value}")
        self._publish_emotion(emo)

    def _on_query_ended(self, **kwargs):
        """При завершении обработки запроса — вернуться в режим простоя, но с паузой."""
        # Немного подождём, чтобы у пользователя было время заметить
        print("[EMO][Manager] Event user_query_ended → waiting 1s before idle")
        time.sleep(1)
        self._busy_event.clear()
        emo = self._state.get_next_idle()
        print(f"[EMO][Manager] Post-query idle → emotion: {emo.value}")
        self._publish_emotion(emo)

    # Пример заготовки для расширения на сенсоры
    # def _on_sensor_event(self, sensor_type: str, value=None):
    #     """Переключить эмоцию на основе данных сенсора"""
    #     # Логика обработки разных сенсоров
    #     emo = Emotion.ANGRY if sensor_type == 'heat' and value > 50 else Emotion.NEUTRAL
    #     self._publish_emotion(emo)

    def _publish_emotion(self, emotion: Emotion):
        """Публикует событие смены эмоции."""
        print(f"[EMO][Manager] Publishing emotion_changed({emotion.value})")
        self._broker.publish('emotion_changed', emotion=emotion)
