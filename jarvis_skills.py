# jarvis_skills.py
"""
Мини-фреймворк плагинов для Jarvis-Pi.
Скилл = .py-файл в ./skills c двумя атрибутами:

    PATTERNS = ["привет", "как дела"]
    def handle(text: str) -> str

PATTERNS сравниваются по fuzzy-ratio; handle(text) вызывается,
если совпадение > THRESHOLD.
"""

import sys
import time
import types
import importlib
import importlib.util
import threading
import asyncio
from pathlib import Path

from rapidfuzz import fuzz   # уже есть в requirements.txt

# ──────────────────────────────────────────────────────────────────────────
SKILLS_DIR    = Path(__file__).parent / "skills"
POLL_INTERVAL = 1.0   # частота проверки изменений (сек.)
THRESHOLD     = 70    # минимальный % совпадения для вызова handle()

_loaded: list[tuple[list[str], callable]] = []  # [(PATTERNS, handle), …]
_scheduled: dict[str, asyncio.Task] = {}

# ─── Делаем пакет «skills», если его ещё нет ──────────────────────────────
if "skills" not in sys.modules:
    pkg = types.ModuleType("skills")
    pkg.__path__ = [str(SKILLS_DIR)]   # чтобы импорт мог находить файлы
    sys.modules["skills"] = pkg

# ─── Вспомогательные функции ─────────────────────────────────────────────
def _path_to_module(path: Path) -> str:
    """skills/weather_ru.py → skills.weather_ru"""
    rel = path.relative_to(SKILLS_DIR.parent).with_suffix("")
    return ".".join(rel.parts)  # 'skills', 'weather_ru' → 'skills.weather_ru'

def _register(mod):
    """Кладёт PATTERNS/handle из *mod* в список _loaded."""
    pats = getattr(mod, "PATTERNS", [])
    func = getattr(mod, "handle",   None)
    if pats and callable(func):
        _loaded.append((pats, func))

def _load_file(py_file: Path):
    """Импортирует (или пере-импортирует) файл-скилл и регистрирует его."""
    mod_name = _path_to_module(py_file)          # skills.weather_ru
    # убираем старые таймеры этого модуля
    for t in _scheduled.pop(mod_name, []):
        t.cancel()
    if mod_name in sys.modules:                  # 🔄 reload
        mod = importlib.reload(sys.modules[mod_name])
    else:                                        # ➕ первый импорт
        spec = importlib.util.spec_from_file_location(mod_name, py_file)
        mod  = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod              # важно: единое имя!
        spec.loader.exec_module(mod)             # type: ignore[arg-type]
    _register(mod)
    _schedule_autoupdate(mod)

# ─── Слежение за изменениями .py-файлов ───────────────────────────────────
def _watch_skills():
    mtimes: dict[Path, float] = {}
    while True:
        for f in SKILLS_DIR.glob("*.py"):
            mtime = f.stat().st_mtime
            if mtimes.get(f) != mtime:
                mtimes[f] = mtime
                mod_name = _path_to_module(f)

                # 1) убираем устаревшие записи этого модуля
                _loaded[:] = [
                    (p, h) for (p, h) in _loaded
                    if h.__module__ != mod_name
                ]
                # 2) загружаем свежий код и регистрируем
                _load_file(f)

                print(f"[Jarvis] 🔄 перезагрузил {mod_name}")
        time.sleep(POLL_INTERVAL)

def start_skill_reloader() -> None:
    """Запускает фоновый поток-наблюдатель."""
    threading.Thread(target=_watch_skills, daemon=True).start()

# ─── Начальная загрузка всех скиллов ─────────────────────────────────────
def load_all() -> None:
    """Сканирует папку ./skills и загружает все файлы."""
    _loaded.clear()
    SKILLS_DIR.mkdir(exist_ok=True)
    for f in SKILLS_DIR.glob("*.py"):
        _load_file(f)

# ─── Маршрутизация пользовательской реплики ──────────────────────────────
def handle_utterance(text: str) -> bool:
    """Возвращает True, если какой-то скилл обработал реплику."""
    text_low = text.lower()
    best_func, best_score = None, 0

    for patterns, func in _loaded:
        for p in patterns:
            p_low = p.lower()
            score = max(
                fuzz.ratio(text_low, p_low),           # полная строка
                fuzz.token_set_ratio(text_low, p_low)  # порядок слов не важен
            )
            if score > best_score:
                best_score, best_func = score, func

    if best_score >= THRESHOLD and best_func:
        try:
            reply = best_func(text)
            if isinstance(reply, str) and reply.strip():
                from working_tts import working_tts
                working_tts(reply)
                return True
        except Exception as e:
            print(f"[Skill error] {e}")

    return False

def _schedule_autoupdate(mod):
    """
    Если в модуле есть AUTO_UPDATE_INTERVAL и функция auto_update(),
    запускает повторяющийся таймер.  Результат НЕ передаётся в TTS.
    """
    interval = getattr(mod, "AUTO_UPDATE_INTERVAL", None)
    update_fn = getattr(mod, "auto_update", None)
    if not (isinstance(interval, (int, float)) and callable(update_fn)):
        return                     # у скилла нет авто-режима

    def _runner():
        try:
            res = update_fn()  # сам скилл выводит на дисплей
            if asyncio.iscoroutine(res):
                asyncio.run(res)  # поддержка async auto_update()
        except Exception as e:
            print(f"[AutoUpdate] ❌ {mod.__name__}: {e}")
        finally:  # перезапускаем себя
            t = threading.Timer(interval, _runner)
            t.daemon = True
            _scheduled.setdefault(mod.__name__, []).append(t)
            t.start()
    _runner()  # первый запуск
