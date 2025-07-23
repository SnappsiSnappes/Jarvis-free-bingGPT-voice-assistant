# -*- coding: utf-8 -*-
"""
Скилл «Напоминания» (RU)
========================

Понимает фразы вида
-------------------
• «Напомни через две минуты попить чай»
• «Напомни через десять минут выключить суп»
• «Напомни мне завтра в 14:00 позвонить в больницу»
• «Напомни в 18:30 выключить духовку» (сегодня или завтра, если время уже прошло)
• «Напомни завтра в 9 сходить к врачу»
• «Напомни мне **в двадцать три тридцать пять** позвонить» ✅ (слова‑числа)
• «Какие напоминания запущены» / «Что запланировано»

Напоминания хранятся в виде threading.Timer. По срабатыванию озвучивают
фразу «Вы просили напомнить: …».
"""

from __future__ import annotations
import datetime as _dt
import re, threading, time
from typing import List, Tuple, Dict

# ---------------------------------------------------------------------------
# 1. CONSTANTS & HELPERS
# ---------------------------------------------------------------------------

PATTERNS: List[str] = [
    "напомни", "напомни мне", "какие напоминания", "что запланировано",
]

# слова‑числа → int
_NUM_WORDS: Dict[str, int] = {
    "ноль": 0, "ноля": 0,
    "один": 1, "одна": 1, "одну": 1, "одной": 1,
    "два": 2, "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
    "двадцать": 20,
    "тридцать": 30,
    "сорок": 40,
    "пятьдесят": 50,
}

_UNIT_SECONDS = {
    "сек": 1, "секунд": 1, "секунду": 1, "секунды": 1,
    "мин": 60, "минута": 60, "минут": 60, "минуты": 60,
    "час": 3600, "часа": 3600, "часов": 3600,
}

_SPECIAL = {
    "полчаса": 30 * 60,
    "пол часа": 30 * 60,
    "полтора часа": int(1.5 * 3600),
    "полтора": int(1.5 * 60),
}

_REMINDERS: List[Tuple[threading.Timer, float, str]] = []  # timer, when_ts, text

# ---------------------------------------------------------------------------
# 2. UTILITIES
# ---------------------------------------------------------------------------

def _word_to_num(tok: str) -> int | None:
    tok = tok.lower()
    if tok.isdigit():
        return int(tok)
    return _NUM_WORDS.get(tok)


def _words_sequence_to_numbers(chunk: str) -> List[int]:
    """Конвертирует кусок "двадцать три тридцать пять" → [23, 35]."""
    numbers: List[int] = []
    acc: int | None = None

    for w in chunk.lower().split():
        if w.isdigit():
            # цифрой
            numbers.append(int(w))
            acc = None
            continue
        val = _NUM_WORDS.get(w)
        if val is None:
            # не число — обнуляем накопитель, игнорируем
            if acc is not None:
                numbers.append(acc)
                acc = None
            continue
        if val < 10 and acc is not None and acc >= 20:
            # «двадцать три»
            numbers.append(acc + val)
            acc = None
        elif val % 10 == 0 and val >= 20:
            # начало составного «двадцать ...»
            acc = val
        else:
            numbers.append(val)
            acc = None
    if acc is not None:
        numbers.append(acc)
    return numbers


def _format_remaining(sec: int) -> str:
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h} ч {m} мин"
    if m:
        return f"{m} мин"
    return f"{s} сек"


def _speak(msg: str):
    from working_tts import working_tts
    working_tts(msg)

# ---------------------------------------------------------------------------
# 3. SCHEDULING
# ---------------------------------------------------------------------------

def _schedule(sec: int, text: str):
    when = time.time() + sec
    def _fire():
        _speak(f"Вы просили напомнить: {text}.")
    t = threading.Timer(sec, _fire)
    _REMINDERS.append((t, when, text))
    t.start()

# ---------------------------------------------------------------------------
# 4. PARSERS
# ---------------------------------------------------------------------------

def _parse_relative(fragment: str) -> int | None:
    """Извлекает секунды из «через пять минут», «через 2 часа», «полчаса» …"""
    frag = fragment.lower()
    for special, sec in _SPECIAL.items():
        if special in frag:
            return sec

    m = re.search(r"(?P<num>[\dа-яё]+)\s*(?P<unit>секунд[а-я]*|минут[а-я]*|час[а-я]*)", frag)
    if not m:
        return None
    num_token = m.group("num")
    unit_token = m.group("unit")

    sec_per_unit = None
    for key, val in _UNIT_SECONDS.items():
        if unit_token.startswith(key):
            sec_per_unit = val
            break
    if sec_per_unit is None:
        return None

    num = _word_to_num(num_token)
    if num is None:
        return None
    return num * sec_per_unit


def _parse_absolute(fragment: str) -> _dt.datetime | None:
    """Парсит «завтра в 14:00», «в 18:30», «завтра в девять» …"""
    frag = fragment.lower().strip()
    today = _dt.datetime.now()
    date = today.date()

    # завтра / сегодня
    if frag.startswith("завтра"):
        date = today.date() + _dt.timedelta(days=1)
        frag = frag[6:].strip()
    elif frag.startswith("сегодня"):
        frag = frag[7:].strip()

    # ищем «в …»
    m = re.search(r"в\s+([\d:]+)", frag)
    if m:
        time_part = m.group(1)
        if ":" in time_part:
            h, mnt = map(int, time_part.split(":"))
        else:
            h = int(time_part)
            mnt = 0
        dt = _dt.datetime.combine(date, _dt.time(hour=h % 24, minute=mnt % 60))
        if dt <= today:
            dt += _dt.timedelta(days=1)
        return dt

    # слова‑числа «в двадцать три тридцать пять»
    m2 = re.search(r"в\s+([а-яё\s]+)", frag)
    if m2:
        words = m2.group(1)
        nums = _words_sequence_to_numbers(words)
        if not nums:
            return None
        h = nums[0] % 24
        mnt = nums[1] % 60 if len(nums) >= 2 else 0
        dt = _dt.datetime.combine(date, _dt.time(hour=h, minute=mnt))
        if dt <= today:
            dt += _dt.timedelta(days=1)
        return dt

    return None

# ---------------------------------------------------------------------------
# 5. MAIN HANDLE
# ---------------------------------------------------------------------------

def handle(text: str) -> str:
    t = text.lower()

    # список активных
    if re.search(r"какие\s+напоминани[яея]|что\s+запланировано", t):
        now = time.time()
        if not _REMINDERS:
            return "У вас нет активных напоминаний."
        parts = [f"{_format_remaining(int(when - now))} – {txt}" for _, when, txt in _REMINDERS]
        return "; ".join(parts) + "."

    # ----- относительные «через …»
    m = re.search(r"напомни(?:\s+мне)?\s*(?P<todo>.*?)\s*через\s+(?P<rest>.+)", t)
    if m:
        todo = m.group("todo").strip() or ""
        rest = m.group("rest")
        sec = _parse_relative(rest)
        if sec is None:
            return "Не понял, через сколько напомнить."
        _schedule(sec, todo)
        return f"Напоминание через {_format_remaining(sec)} установлено."

    # ----- абсолютные «завтра в 14:00» / «в 18:30» / слова‑числа
    m = re.search(r"напомни(?:\s+мне)?\s*(?P<todo>.*?)\s*(завтра\s+|сегодня\s+)?в\s+(.+)", t)
    if m:
        todo = m.group("todo").strip() or ""
        dt = _parse_absolute(t[m.span():])
        if dt is None:
            return "Не понял время напоминания."
        sec = int((dt - _dt.datetime.now()).total_seconds())
        _schedule(sec, todo)
        when_str = dt.strftime("%d.%m %H:%M")
        return f"Напоминание на {when_str} установлено."

    return "Извините, не смог обработать запрос."
