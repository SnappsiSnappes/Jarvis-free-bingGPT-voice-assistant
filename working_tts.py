# -*- coding: utf-8 -*-
"""
Piper‑TTS adapter for Jarvis.
Совместим со всеми релизами piper‑tts ≥ 1.2.0 (включая 1.3+ и nightly).

Изменения (2025‑07‑11):
• Логирование разделено на время генерации и время воспроизведения для каждой части.
• Разбиение длинного текста: сохраняем предел 180 символов, но теперь режем по законченной фразе (., !, ?, …) — это уменьшает задержки и делает озвучку более естественной.
"""

import array
import inspect
import os
import time
import re
from typing import List, Iterable

import keyboard
import numpy as np
import sounddevice as sd

from piper import PiperVoice
from transliterate import translit

from working_numbers_to_words import numbers_to_wards
from working_remove_space_in_numbers import remove_spaces_in_numbers

# ────────────────────────── 1. LOAD VOICE ──────────────────────────
VOICE_ID = "ru-RU-irina-medium" # ru_RU-denis-medium, ru-RU-irina-medium
SEARCH_DIRS: List[str] = ["./models//piper"]


def _find_voice() -> str:
    """Ищет *.onnx модель по стандартным каталогам."""
    for base in SEARCH_DIRS:
        onnx = os.path.join(base, f"{VOICE_ID}.onnx")
        if os.path.isfile(onnx):
            return onnx
    raise FileNotFoundError(
        f"{VOICE_ID}.onnx(.json) не найден. Скопируйте оба файла в:\n  "
        + "\n  ".join(SEARCH_DIRS)
    )


VOICE: PiperVoice = PiperVoice.load(_find_voice(), use_cuda=False)
_SAMPLE_RATE: int = VOICE.config.sample_rate

# заранее проверяем, поддерживает ли метод атрибут «audio_streaming»
_SIG_HAS_AUDIO_STREAMING: bool = "audio_streaming" in inspect.signature(VOICE.synthesize).parameters


# ─────────────────────── 2. HELPERS ────────────────────────────────

def _wait_until_play_done():
    """Блокирует поток, пока sd.play() не закончит играть или не нажата ESC."""
    while sd.get_stream().active:
        if keyboard.is_pressed("esc"):
            sd.stop()
            break
        time.sleep(0.05)


def _to_int16(arr: np.ndarray) -> np.ndarray:
    """Возвращает массив *exactly* np.int16.

    Если на входе float*/int* другого размера — конвертирует с масштабированием.
    """
    if arr.dtype == np.int16:
        return arr
    if arr.dtype.kind == "f":  # float‑массив в диапазоне [‑1 … 1]
        arr = np.clip(arr * 32767.0, -32768, 32767)
        return arr.astype(np.int16)
    # всё остальное → через astype
    return arr.astype(np.int16, copy=False)


def _chunk_to_ndarray(chunk) -> np.ndarray:
    """Извлекает PCM из разных форматов (bytes/array/AudioChunk/…) в np.int16."""
    # 1. Готовый np.ndarray
    if isinstance(chunk, np.ndarray):
        return _to_int16(chunk)

    # 2. bytes/bytearray/memoryview (уже int16‑поток)
    if isinstance(chunk, (bytes, bytearray, memoryview)):
        return np.frombuffer(chunk, dtype=np.int16)

    # 3. AudioChunk: ищем массивы внутри объекта
    for name in dir(chunk):
        if name.startswith("_"):
            continue
        try:
            val = getattr(chunk, name)
        except Exception:
            continue
        if isinstance(val, array.array):
            if val.typecode in ("h", "H"):
                return np.frombuffer(val, dtype=np.int16)
            return np.asarray(val, dtype=np.int16)
        if isinstance(val, np.ndarray):
            return _to_int16(val)
        if isinstance(val, (bytes, bytearray, memoryview)):
            return np.frombuffer(val, dtype=np.int16)
        if isinstance(val, (list, tuple)) and val and isinstance(val[0], (int, float)):
            return np.asarray(val, dtype=np.int16)

    # 4. Итерабельный из чисел
    try:
        return np.asarray(list(chunk), dtype=np.int16)
    except Exception:
        pass

    # 5. Не удалось распознать → тишина
    return np.zeros(0, dtype=np.int16)


# ─────────────────────── 2a. SPLITTING ─────────────────────────────
_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+")


def _split_by_sentences(text: str, max_len: int = 180) -> Iterable[str]:
    """Разбивает *text* на части ≤ *max_len* символов, но только по границам предложений.
    Предложения детектируются простым регэкспом: после любой из [. ! ? …] и затем пробела.
    """
    sentences = _SENTENCE_RE.split(text)
    chunk = ""
    for sent in sentences:
        if not sent:
            continue
        if len(chunk) + len(sent) + 1 <= max_len:
            chunk = (chunk + " " + sent).strip()
        else:
            if chunk:
                yield chunk
            chunk = sent
    if chunk:
        yield chunk


# ───────────────────── 3. SYNTHESIS BACKEND ───────────────────────

def _synthesize(text: str) -> np.ndarray:
    """Возвращает аудио int16 одним массивом независимо от версии piper‑tts."""
    if _SIG_HAS_AUDIO_STREAMING:
        # >= 1.3: можно сразу получить весь трек
        audio = VOICE.synthesize(text, audio_streaming=False)
        return _to_int16(audio)

    # 1.2.x: только поток → собираем вручную
    frames = (_chunk_to_ndarray(chunk) for chunk in VOICE.synthesize(text))
    audio = np.concatenate(list(frames)) if text else np.zeros(0, dtype=np.int16)
    return audio


# ─────────────────────── 4. MAIN ENTRY ────────────────────────────

def working_tts(text: str):
    """Озвучивает *text*, разбивая по 180 символов (граница — конец предложения)."""
    # 4.1 нормализация текста
    text = translit(remove_spaces_in_numbers(numbers_to_wards(text)), "ru")
    print(f"[TTS] {text}")
    # 4.2 синтез + воспроизведение по частям
    for idx, chunk in enumerate(_split_by_sentences(text, 180), 1):
        # ───── генерация ─────
        t_gen_start = time.perf_counter()
        audio = _synthesize(chunk)
        t_gen = time.perf_counter() - t_gen_start
        if not audio.size:
            continue  # иногда piper возвращает пустой массив

        # piper выдаёт int16; а sd.play охотнее играет float32
        audio_f32 = audio.astype(np.float32) / 32767.0

        # ───── воспроизведение ─────
        t_play_start = time.perf_counter()
        sd.play(audio_f32, _SAMPLE_RATE)
        _wait_until_play_done()
        sd.stop()
        t_play = time.perf_counter() - t_play_start

        # DEBUG‑лог
        print(
            f"[TTS] gen {t_gen:.2f}s  play {t_play:.2f}s  part {idx}  max={int(audio.max())} min={int(audio.min())} len={len(audio)}"
        )
