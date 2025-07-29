from __future__ import annotations

import array as _array
import inspect
import os
import re
import time
import wave
from typing import Iterable, List

import keyboard  # type: ignore — requires native build on Win
import numpy as np
import sounddevice as sd  # type: ignore
from piper import PiperVoice  # type: ignore — external lib
from transliterate import translit  # type: ignore

from working_numbers_to_words import numbers_to_wards
from working_remove_space_in_numbers import remove_spaces_in_numbers

# ────────────────────────── 0. LOGGING ────────────────────────────
from logging_config import setup_logging
log = setup_logging(__name__)

# ────────────────────────── 1. CONFIG ─────────────────────────────
VOICE_ID: str = "ru_RU-ruslan-medium" #"ru-RU-irina-medium"  # default voice ID
SEARCH_DIRS: List[str] = ["./models/piper"]  # where *.onnx lives
MAX_CHARS: int = 180  # split size per chunk
TAIL_PAD_SEC: float = 0.3
USE_CUDA: bool = False  # toggle when GPU available

# ────────────────────────── 2. LOAD VOICE ─────────────────────────

def _find_voice() -> str:
    """Return absolute path to <VOICE_ID>.onnx model (raise if not found)."""
    for base in SEARCH_DIRS:
        model_path = os.path.join(base, f"{VOICE_ID}.onnx")
        if os.path.isfile(model_path):
            return model_path
    raise FileNotFoundError(
        f"{VOICE_ID}.onnx(.json) not found. Expected in: \n  "
        + "\n  ".join(os.path.abspath(p) for p in SEARCH_DIRS)
    )

VOICE: PiperVoice = PiperVoice.load(_find_voice(), use_cuda=USE_CUDA)
SAMPLE_RATE: int = VOICE.config.sample_rate
_SIG_HAS_AUDIO_STREAMING: bool = "audio_streaming" in inspect.signature(
    VOICE.synthesize
).parameters
log.info("Voice '%s' loaded (sr=%d, streaming=%s)", VOICE_ID, SAMPLE_RATE, _SIG_HAS_AUDIO_STREAMING)

# ────────────────────────── 3. HELPERS ────────────────────────────
_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s+")

def _split_by_sentences(text: str, max_len: int = MAX_CHARS) -> Iterable[str]:
    """Yield *chunks* of text ≤ *max_len*, split on sentence boundaries."""
    sentences = _SENTENCE_RE.split(text)
    chunk: str = ""
    for sent in sentences:
        if not sent:
            continue
        if len(chunk) + len(sent) + 1 <= max_len:
            chunk = f"{chunk} {sent}".strip()
        else:
            if chunk:
                yield chunk
            chunk = sent
    if chunk:
        yield chunk

def _to_int16(arr: np.ndarray) -> np.ndarray:  # noqa: N802 (library helper)
    """Ensure ndarray is exactly int16."""
    if arr.dtype == np.int16:
        return arr
    if arr.dtype.kind == "f":  # float32/64 in [-1..1]
        arr = np.clip(arr * 32767.0, -32768, 32767)
        return arr.astype(np.int16)
    return arr.astype(np.int16, copy=False)

def _chunk_to_ndarray(chunk) -> np.ndarray:
    """Extract PCM int16 from any Piper iterator chunk."""
    if isinstance(chunk, np.ndarray):
        return _to_int16(chunk)
    if isinstance(chunk, (bytes, bytearray, memoryview)):
        return np.frombuffer(chunk, dtype=np.int16)
    for name in dir(chunk):
        if name.startswith("_"):
            continue
        try:
            val = getattr(chunk, name)
        except Exception:
            continue
        if isinstance(val, _array.array):
            return np.frombuffer(val, dtype=np.int16)
        if isinstance(val, np.ndarray):
            return _to_int16(val)
        if isinstance(val, (bytes, bytearray, memoryview)):
            return np.frombuffer(val, dtype=np.int16)
        if isinstance(val, (list, tuple)) and val and isinstance(val[0], (int, float)):
            return np.asarray(val, dtype=np.int16)
    try:
        return np.asarray(list(chunk), dtype=np.int16)
    except Exception:
        return np.zeros(0, dtype=np.int16)

def _synthesize(text: str) -> np.ndarray:
    """Return single int16 array for *text* regardless of Piper version."""
    if not text:
        return np.zeros(0, dtype=np.int16)

    if _SIG_HAS_AUDIO_STREAMING:  # piper‑tts ≥ 1.3
        return _to_int16(VOICE.synthesize(text, audio_streaming=False))

    # piper‑tts 1.2.x — stream, need to concat
    frames = (_chunk_to_ndarray(c) for c in VOICE.synthesize(text))
    return np.concatenate(list(frames))

def _ndarray_to_float32(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32, copy=False) / 32767.0 if audio.size else audio

# ────────────────────────── 4. PUBLIC API ─────────────────────────

def _save_wav(path: str, pcm_i16: np.ndarray) -> None:
    """Пишет mono-PCM-16 bit в .wav (для отладки)."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)              # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_i16.tobytes())
    log.info("WAV-debug: saved %s (%.2f s)", path, pcm_i16.size / SAMPLE_RATE)


def working_tts(
    text: str,
    *,
    max_chars: int = MAX_CHARS,
    save_wav: str | None = None,        # ← новый арг.
) -> None:
    """Озвучивает *text*; при *save_wav* пишет итоговый WAV-файл."""
    norm = translit(remove_spaces_in_numbers(numbers_to_wards(text)), "ru")
    log.info("Speak %d chars", len(norm))

    parts: list[np.ndarray] = []        # накапливаем для WAV

    for i, chunk in enumerate(_split_by_sentences(norm, max_chars), 1):
        t0 = time.perf_counter()
        pcm_i16 = _synthesize(chunk)           # int16 от Piper
        t_gen = time.perf_counter() - t0
        if not pcm_i16.size:
            log.warning("Part %d: empty audio", i)
            continue

        parts.append(pcm_i16)                  # до «хвоста»!

        # ── добавляем тишину и сразу в float32 ──────────────────
        tail = np.zeros(int(SAMPLE_RATE * TAIL_PAD_SEC), np.int16)
        pcm_i16_pad = np.concatenate([pcm_i16, tail])
        audio_f32 = pcm_i16_pad.astype(np.float32) / 32767.0

        # ── воспроизведение (без sd.stop!) ──────────────────────
        t1 = time.perf_counter()
        sd.play(audio_f32, SAMPLE_RATE)
        t_play = time.perf_counter() - t1

        rms = float(np.sqrt(np.mean(audio_f32 ** 2)))
        log.info(
            "part %2d | gen %.2fs | play %.2fs | len %6d | rms %.3f",
            i, t_gen, t_play, pcm_i16.size, rms,
        )

    # ── запись WAV, если просили ───────────────────────────────
    if save_wav:
        _save_wav(save_wav, np.concatenate(parts) if parts else np.zeros(0, np.int16))

# ────────────────────────── 5. ASYNC WRAPPER ─────────────────────

async def speak_async(text: str, *, loop: asyncio.AbstractEventLoop | None = None) -> None:  # type: ignore[name-defined]
    """Async helper: run `working_tts` in executor to avoid blocking."""
    global in_tts
    in_tts = True
    import asyncio  # local to avoid unconditional asyncio import in sync context
    try:
        loop = loop or asyncio.get_running_loop()
        await loop.run_in_executor(None, working_tts, text)
    finally:
        in_tts = False

# ────────────────────────── 6. CLI TEST ──────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Piper‑TTS playback")
    parser.add_argument("text", nargs="*", help="Text to speak")
    parser.add_argument("--chars", "-c", type=int, default=MAX_CHARS, help="Chunk size")
    args = parser.parse_args()

    if args.text:
        working_tts(" ".join(args.text), max_chars=args.chars)
    else:
        working_tts("Привет! Я Джарвис, ваш голосовой ассистент.")
