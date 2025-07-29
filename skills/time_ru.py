# -*- coding: utf-8 -*-
"""
Скилл «Текущее время» (RU)
==========================

Отвечает на вопросы:
• «Который час?»
• «Сколько времени?» / «Сколько время?»
• «Сейчас времени?» / «Текущее время»

Произносит время словами:
• «двадцать три часа пятнадцать минут»
• «восемнадцать часов одна минута»
• «два часа ровно»
• «один час двадцать пять минут»
• «один час тридцать две минуты»
"""

from __future__ import annotations
import datetime as _dt
from typing import List

from display import get_driver, DisplayItem

# Фразы‑активаторы для jarvis_skills.py
PATTERNS: List[str] = [
    "который час", "сколько времени", "сколько время", "текущее время",
    "сейчас времени", "сколько сейчас времени",
]

_NUM_1_19 = [
    "ноль", "один", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять",
    "десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать",
    "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать",
]

_TENS = {
    20: "двадцать",
    30: "тридцать",
    40: "сорок",
    50: "пятьдесят",
}

AUTO_UPDATE_INTERVAL = 30

def _num_to_words(n: int) -> str:
    """0‑59 → «двадцать пять»"""
    if 0 <= n < 20:
        return _NUM_1_19[n]
    if 20 <= n < 60:
        tens, ones = divmod(n, 10)
        phrase = _TENS[tens * 10]
        if ones:
            phrase += f" {_NUM_1_19[ones]}"
        return phrase
    raise ValueError("n must be between 0 and 59")


def _hours_decl(h: int) -> str:
    if h % 10 == 1 and h != 11:
        return "час"
    if 2 <= h % 10 <= 4 and not 12 <= h <= 14:
        return "часа"
    return "часов"


def _minutes_decl(m: int) -> str:
    if m % 10 == 1 and m != 11:
        return "минута"
    if 2 <= m % 10 <= 4 and not 12 <= m <= 14:
        return "минуты"
    return "минут"


def _format_time(now: _dt.datetime) -> str:
    h, m = now.hour, now.minute
    h_words = _num_to_words(h)
    h_word = _hours_decl(h)
    if m == 0:
        return f"{h_words} {h_word} ровно"
    m_words = _num_to_words(m)
    m_word = _minutes_decl(m)
    return f"{h_words} {h_word} {m_words} {m_word}"

def _format_time_display(now: _dt.datetime) -> str:
    return now.strftime("%d-%m %H:%M")

def handle(_: str) -> str:
    now = _dt.datetime.now()
    return _format_time(now)

def auto_update():
    """Вызывается планировщиком — обновляем время на дисплее."""
    now = _dt.datetime.now()
    disp_str = _format_time_display(now)
    driver = get_driver()
    driver.draw(DisplayItem(
        kind="time",
        payload=disp_str
    ))
