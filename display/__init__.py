"""
Модуль дисплея с поддержкой динамической загрузки драйверов.
Структура проекта:

 display/           # пакет дисплея
 ├── __init__.py    # загрузчик драйверов и базовый класс
 └── drivers/       # папка с драйверами
     ├── __init__.py
     └── windows.py # пример драйвера для Windows (tkinter)
"""
from abc import ABC, abstractmethod
import importlib


from dataclasses import dataclass
from typing import Literal, Union

@dataclass
class DisplayItem:
    kind:    Literal["text", "icon", "image", "rect", "line", "weather", "time", "emotion", "servo", "frame"]
    payload: Union[str, bytes, dict]     # для text — строка, для icon — ключ в наборе


class DisplayDriver(ABC):
    """Абстрактный базовый класс для драйверов дисплея."""

    @abstractmethod
    def draw(self, item: DisplayItem) -> None:
        """
        Получает DisplayItem — абстракцию, описывающую,
        *что* рисовать и *где* (координаты или проценты).
        """
        ...

    @abstractmethod
    def process_events(self) -> None:
        """
        Вызывается в цикле asyncio для обработки GUI-событий (tkinter).
        """
        ...

# Внутренний экземпляр текущего драйвера
_driver: DisplayDriver | None = None


def init_driver(name: str = "windows", driver: DisplayDriver | None = None) -> None:
    """
    Инициализировать драйвер дисплея:
      - name: имя модуля внутри display.drivers (без .py)
      - driver: объект драйвера (приоритет выше name)

    Пример: init_driver("windows")
    """
    global _driver
    if _driver is not None:
        return
    if driver is not None:
        _driver = driver
        return

    # динамический импорт по имени
    module_path = f"display.drivers.{name}"
    print(f"[LOG] Display module {module_path}")
    module = importlib.import_module(module_path)
    # ожидаем, что класс называется <Name>DisplayDriver
    class_name = name.capitalize() + "DisplayDriver"
    driver_cls = getattr(module, class_name)
    _driver = driver_cls()
    try:
        _driver.process_events()
    except Exception:
        pass

def get_driver() -> DisplayDriver:
    """Получить текущий драйвер, инициализировать по умолчанию, если не задан."""
    global _driver
    if _driver is None:
        init_driver()
    return _driver
