import threading
import time
from typing import List
from display import DisplayDriver, DisplayItem

# Эталон: 320×240 px ~ 64×24 символа
INNER_W = 32
INNER_H = 12

class ConsoleDisplayDriver(DisplayDriver):
    def __init__(self):
        self._items: List[DisplayItem] = []
        self._lock = threading.Lock()
        threading.Thread(target=self._live_thread, daemon=True).start()

    def draw(self, item: DisplayItem) -> None:
        with self._lock:
            # заменяем предыдущий такой же kind
            self._items = [i for i in self._items if i.kind != item.kind]
            self._items.append(item)

    def process_events(self) -> None:
        pass

    def _live_thread(self) -> None:
        # фоновый цикл рендера
        while True:
            panel = self._render_panel()
            print(panel, end="\r")  # обновляем один и тот же участок
            time.sleep(0.5)

    def _render_panel(self) -> str:
        # ищем нужные элементы
        time_item    = next((i for i in self._items if i.kind=="time"), None)
        weather_item = next((i for i in self._items if i.kind=="weather"), None)
        text_item    = next((i for i in self._items if i.kind=="text"), None)
        emotion_item = next((i for i in self._items if i.kind=="emotion"), None)

        # Формируем пустую «матрицу» строк
        lines = []
        # 1) Верхняя граница
        lines.append("┌" + "─"*INNER_W + "┐")

        # 2) Шапка: время слева, погода справа
        left = time_item.payload if time_item else ""
        right = weather_item.payload if weather_item else ""
        # если строка слишком длинная — обрезаем
        header = (left + right.rjust(INNER_W - len(left)))[:INNER_W]
        lines.append("│" + header + "│")

        # 3) Тело на втором ряду
        body = ""
        if text_item:
            body = text_item.payload
        elif emotion_item:
            body = emotion_item.payload
        # центрируем по INNER_W
        b = body.center(INNER_W)[:INNER_W]
        lines.append("│" + b + "│")

        # 4) Оставшиеся строки — пустые
        for _ in range(INNER_H - 2):
            lines.append("│" + " "*INNER_W + "│")

        # 5) Нижняя граница
        lines.append("└" + "─"*INNER_W + "┘")

        # Собираем в одну строку с новыми строками
        return "\n".join(lines) + "\n"
