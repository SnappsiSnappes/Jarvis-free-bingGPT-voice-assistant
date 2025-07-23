import threading
from collections import defaultdict


class EventBroker:
    """
    Простая реализация паттерна pub/sub для обмена событиями между модулями.
    """

    def __init__(self):
        # _subscribers хранит список обратных вызовов для каждого события
        self._subscribers = defaultdict(list)
        # блокировка для потокобезопасности
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback):
        """
        Подписаться на событие.
        :param event_name: строковое имя события
        :param callback: функция, которую вызовут при публикации
        """
        with self._lock:
            self._subscribers[event_name].append(callback)

    def publish(self, event_name: str, **kwargs):
        """
        Опубликовать событие и передать параметры всем подписчикам.
        :param event_name: строковое имя события
        :param kwargs: данные события
        """
        # Копируем список подписчиков под блокировкой
        with self._lock:
            callbacks = list(self._subscribers.get(event_name, []))

        # Вне блокировки вызываем все подписки
        for callback in callbacks:
            try:
                callback(**kwargs)
            except Exception as e:
                # TODO: заменить print на логгер
                print(f"Error in subscriber for '{event_name}': {e}")
