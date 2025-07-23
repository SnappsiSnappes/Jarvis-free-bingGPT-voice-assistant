# skills/hello_world.py
from display import get_driver, DisplayItem

PATTERNS = ["привет мир", "hello world", "скажи привет"]


def handle(text):
    driver = get_driver()

    driver.draw(DisplayItem(
        kind="text",
        payload=f"Привет-привет!"
    ))
    return "Привет-привет!"
