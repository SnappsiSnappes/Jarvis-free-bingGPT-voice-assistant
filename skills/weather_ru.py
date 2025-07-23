# skills/weather_ru.py
"""
Мини-скилл «Погода» с резервированием

Алгоритм:
1. Сначала пытаемся получить прогноз с wttr.in (таймаут 1 с).
2. Если wttr.in не отвечает или отдаёт ошибку → берём данные из Open‑Meteo.
3. Формат и набор паттернов остались прежними: «погода», «погода завтра» и т.д.

Переменные окружения
--------------------
WTTR_LAT, WTTR_LON   — координаты для обоих сервисов
JARVIS_CITY          — название города в родительном падеже («в Магнитогорске»)
"""

from __future__ import annotations
import os, re, requests, datetime
from typing import Dict

from display import get_driver, DisplayItem

# ─── Настройки ────────────────────────────────────────────────────────────
LAT: str = os.getenv("WTTR_LAT", "53.37977235908946")
LON: str = os.getenv("WTTR_LON", "58.990413992217746")
CITY: str = os.getenv("JARVIS_CITY", "Магнитогорске")

WTTR_TIMEOUT: int = 1   # секунда — как попросил пользователь
OPENMETEO_TIMEOUT: int = 4
FORECAST_DAYS: int = 3

AUTO_UPDATE_INTERVAL = 1800
# ──────────────────────────────────────────────────────────────────────────
_ICON = {
    0: "☀️", 1: "⛅", 2: "☁️",
    62: "🌧️", 73: "🌨️", 45: "🌫️",
}

# WMO weather codes → русские описания (для Open‑Meteо)
WEATHER_CODES_RU: Dict[int, str] = {
    0: "ясно",
    1: "малооблачно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман", 48: "сильный туман",
    51: "легкая морось", 53: "морось", 55: "сильная морось",
    56: "ледяная морось", 57: "сильная ледяная морось",
    61: "небольшой дождь", 63: "умеренный дождь", 65: "сильный дождь",
    66: "ледяной дождь", 67: "сильный ледяной дождь",
    71: "небольшой снег", 73: "снег", 75: "сильный снег",
    77: "снежная крупа",
    80: "ливень", 81: "сильный ливень", 82: "очень сильный ливень",
    85: "снежный заряд", 86: "сильный снежный заряд",
    95: "гроза", 96: "гроза с градом", 99: "сильная гроза с градом",
}

WEEKDAYS_RU = ["понедельник","вторник","среда","четверг","пятница","суббота","воскресенье"]

# ─── PATTERNS (оставляем те же) ───────────────────────────────────────────
BASE_PATTERNS = [
    "какая погода", "погода", "погода на улице",
    "что там с погодой", "какая температура", "прогноз погоды",
]
EXTRA = ["завтра", "послезавтра"] + WEEKDAYS_RU
PATTERNS = BASE_PATTERNS + \
    [f"погода {w}" for w in EXTRA] + \
    [f"какая погода {w}" for w in EXTRA] + \
    [f"погода в {d}" for d in WEEKDAYS_RU] + \
    [f"какая погода в {d}" for d in WEEKDAYS_RU]

# ─── Вспомогалка для склонения «градус/градуса/градусов» ────────────────
def _plural(n: int, forms: tuple[str,str,str]) -> str:
    n = abs(n) % 100
    if 11 <= n <= 19: return forms[2]
    i = n % 10
    if i == 1: return forms[0]
    if 2 <= i <= 4: return forms[1]
    return forms[2]

# ─── Определяем, какой день спросили ─────────────────────────────────────
def _detect_offset(text: str) -> int:
    t = text.lower()
    today = datetime.date.today()
    if "послезавтра" in t: return 2
    if "завтра" in t: return 1
    for delta in range(1, FORECAST_DAYS):
        if WEEKDAYS_RU[(today + datetime.timedelta(days=delta)).weekday()] in t:
            return delta
    m = re.search(r"(\d{1,2})[.\s](\d{1,2})", t)  # простая дата 12.07
    if m:
        day, month = map(int, m.groups())
        try:
            target = datetime.date(today.year, month, day)
            delta = (target - today).days
            if 0 <= delta < FORECAST_DAYS: return delta
        except ValueError:
            pass
    return 0

# ─── Запрос к wttr.in ────────────────────────────────────────────────────

def _fetch_wttr(lat: str, lon: str):
    url = f"https://wttr.in/{lat},{lon}?format=j1"
    r = requests.get(url, timeout=WTTR_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _build_answer_wttr(city: str, data, offset: int) -> str:
    """Формируем фразу, основываясь на JSON от wttr.in"""
    if offset == 0:
        cur = data["current_condition"][0]
        temp = round(float(cur["temp_C"]))
        cond_ru = _wttr_desc(cur)
        prefix = "Сейчас"
    else:
        daily = data["weather"][offset]
        tmax = round(float(daily["maxtempC"]))
        tmin = round(float(daily["mintempC"]))
        temp = round((tmax + tmin) / 2)
        # Берём описание из середины дня (hourly[4] ≈ 12:00)
        cond_ru = _wttr_desc(daily["hourly"][4] if len(daily["hourly"]) > 4 else daily["hourly"][0])
        prefix = ["Сегодня","Завтра","Послезавтра"][offset] if offset < 3 \
                 else f"В {WEEKDAYS_RU[(datetime.date.today()+datetime.timedelta(days=offset)).weekday()]}"
    degree = _plural(temp, ("градус","градуса","градусов"))
    sign   = "тепла" if temp > 0 else ("мороза" if temp < 0 else "")
    return f"{prefix} в {city} {abs(temp)} {degree} {sign}, {cond_ru}.".strip()


def _wttr_desc(obj) -> str:
    """Возвращает русское описание явления (если есть) или английское"""
    if "lang_ru" in obj and obj["lang_ru"]:
        return obj["lang_ru"][0]["value"].lower()
    return obj["weatherDesc"][0]["value"].lower()

# ─── Запрос к Open‑Meteо ────────────────────────────────────────────────

def _fetch_openmeteo(lat: str, lon: str):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        f"&forecast_days={FORECAST_DAYS}&timezone=auto"
    )
    r = requests.get(url, timeout=OPENMETEO_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _build_answer_openmeteo(city: str, data, offset: int) -> str:
    if offset == 0:
        temp = round(data["current"]["temperature_2m"])
        code = data["current"]["weather_code"]
        prefix = "Сейчас"
    else:
        idx = offset
        tmax = data["daily"]["temperature_2m_max"][idx]
        tmin = data["daily"]["temperature_2m_min"][idx]
        temp = round((tmax + tmin) / 2)
        code = data["daily"]["weather_code"][idx]
        prefix = ["Сегодня","Завтра","Послезавтра"][offset] if offset < 3 \
                 else f"В {WEEKDAYS_RU[(datetime.date.today()+datetime.timedelta(days=offset)).weekday()]}"
    cond_ru = WEATHER_CODES_RU.get(code, "")
    degree = _plural(temp, ("градус","градуса","градусов"))
    sign   = "тепла" if temp > 0 else ("мороза" if temp < 0 else "")
    return f"{prefix} в {city} {abs(temp)} {degree} {sign}, {cond_ru}.".strip()

# ─── Точка входа ─────────────────────────────────────────────────────────

def handle(text: str) -> str:
    offset = _detect_offset(text)
    return _build_answer(offset)


def auto_update():
    """Обновляем погоду на дисплее."""
    t, icon = _current_for_display()
    print(f"[LOG] t{t} icon{icon}")
    driver = get_driver()

    # Температура+иконка — в правом верхнем
    driver.draw(DisplayItem(
        kind="weather",
        payload=f"{t:02d} C {icon}"
    ))

def _current_for_display() -> tuple[int, str]:
    """Температура, иконка и фраза для TTS."""
    # Сначала пробуем wttr.in
    try:
        wttr = _fetch_wttr(LAT, LON)
        cur = wttr["current_condition"][0]
        temp = round(float(cur["temp_C"]))
        code = int(cur.get("weatherCode", 0))
        icon = '' #_ICON[code]
        return temp, icon
    except Exception:
        # Фоллбэк на Open-Meteo
        data = _fetch_openmeteo(LAT, LON)
        cw = data.get("current", {})
        print(f"cw {cw}")
        temp = round(float(cw["temperature_2m"]))
        print(f"temp {temp}")
        # Open-Meteo может использовать ключ 'weathercode' или 'weather_code'
        code = int(cw.get("weathercode", cw.get("weather_code", 0)))
        icon = ''#_ICON[code]
        return temp, icon

def _build_answer(offset: int = 0) -> str:
    try:
        data = _fetch_wttr(LAT, LON)
        return _build_answer_wttr(CITY, data, offset)
    except Exception:
        data = _fetch_openmeteo(LAT, LON)
        return _build_answer_openmeteo(CITY, data, offset)