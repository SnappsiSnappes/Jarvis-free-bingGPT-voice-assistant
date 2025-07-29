from __future__ import annotations

import array
import asyncio
import configparser
import json
import signal
import sys
from multiprocessing import Pipe, Process
from typing import Any, Dict, List

import vosk
import yaml
from mic_adapter import get_mic_stream
from rapidfuzz import fuzz

from display import get_driver, init_driver
from emotion.manager import EmotionManager
from events.broker import EventBroker
from jarvis_skills import handle_utterance, load_all, start_skill_reloader
from logging_config import setup_logging
from working_tts import speak_async

# ────────────────────────── LOGGING ──────────────────────────────
log = setup_logging(__name__)

# ────────────────────────── CONSTANTS ────────────────────────────
VA_ALIAS = ('джарвис',)
VA_TBR = (
    'скажи', 'покажи', 'ответь', 'произнеси', 'расскажи', 'сколько', 'слушай'
)
CMD_CONFIDENCE_THRESHOLD = 70

# ────────────────────────── STATE ────────────────────────────────
wake_worder: bool = False
listening: bool = False
child_processes: List[Process] = []

# ────────────────────────── SIGNALS ──────────────────────────────

def _shutdown(signum: int, frame: Any):
    """Корректное завершение по Ctrl‑C/SIGTERM."""
    log.info("Получен сигнал %s, завершаюсь…", signum)
    for p in child_processes:
        if p.is_alive():
            p.terminate()
    try:
        loop = asyncio.get_running_loop()
        loop.stop()
    except RuntimeError:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

# ────────────────────────── HELPERS ──────────────────────────────

async def execute_cmd(cmd: str, voice: str) -> bool:
    global wake_worder, listening
    if cmd == 'thanks':
        await speak_async("Пожалуйста")
    elif cmd == 'stupid':
        await speak_async("Мне неприятно это слышать")
    elif cmd == 'offf':
        await speak_async("Переходим в спящий режим")
        wake_worder = listening = False
    else:
        return False
    return True

async def recognize_cmd(raw: str) -> Dict[str, Any]:
    best = {'cmd': '', 'percent': 0}
    for key, variants in VA_CMD_LIST.items():
        for alias in variants:
            score = fuzz.ratio(raw, alias)
            if score > best['percent']:
                best = {'cmd': key, 'percent': score}
    return best

async def filter_cmd(raw: str) -> str:
    text = raw.lower()
    for stop in (*VA_ALIAS, *VA_TBR):
        text = text.replace(stop, '').strip()
    return text

async def va_respond(voice: str):
    log.info("Распознано: %s", voice)
    if handle_utterance(voice):
        return True
    raw = await filter_cmd(voice)
    cmd_info = await recognize_cmd(raw)
    log.debug("Cmd match: %s", cmd_info)
    if not cmd_info['cmd'] or cmd_info['percent'] < CMD_CONFIDENCE_THRESHOLD:
        # await speak_async("Команда не распознана")
        return False
    return await execute_cmd(cmd_info['cmd'], voice)

# ────────────────────────── MAIN LOOP ────────────────────────────

async def main(_conn=None):
    global wake_worder, listening, VA_CMD_LIST

    # 1. Config & skills
    VA_CMD_LIST = yaml.safe_load(open('commands.yaml', 'rt', encoding='utf-8'))
    cfg = configparser.ConfigParser()
    cfg.read('config.ini', encoding='utf-8')
    mic_idx = cfg.getint('MIC', 'microphone_index')

    init_driver('websocket')
    load_all()
    broker = EventBroker()
    EmotionManager(broker, 30).start()
    start_skill_reloader()

    # 2. Speech recogniser
    model = vosk.Model('models/model_small')
    kaldi = vosk.KaldiRecognizer(model, 16000)


    # 3. Приветственное сообщение (не блокирует)
    await speak_async("Джарвис запущен")

    wake_worder = listening = False

    # 4. GUI pump task
    async def gui_loop():
        drv = get_driver()
        while True:
            drv.process_events()
            await asyncio.sleep(0.05)
    asyncio.create_task(gui_loop())

    log.info("Произнесите ключевую фразу: %s", ", ".join(VA_ALIAS))

    async for raw_data in get_mic_stream():
        pcm = raw_data
        # Слушаем команду
        if listening:
            if kaldi.AcceptWaveform(pcm):
                result = json.loads(kaldi.Result()).get('text', '')
                if result:
                    log.info("[CMD] %s", result)
                    broker.publish("user_query_started")
                    await va_respond(result)
                    broker.publish("user_query_ended")
                    kaldi.Reset()
            continue

        # Ждём ключевую фразу
        if kaldi.AcceptWaveform(pcm):
            txt = json.loads(kaldi.Result()).get('text', '')
            if any(w in txt for w in VA_ALIAS):
                wake_worder = True
        else:
            part = json.loads(kaldi.PartialResult()).get('partial', '')
            if any(w in part for w in ('джар', 'жар', 'jarv')):
                wake_worder = True

        if wake_worder:
            wake_worder = False
            listening = True
            kaldi.Reset()
            await speak_async("Слушаю")
            log.info("Здравствуйте.")

# ────────────────────────── ENTRYPOINT ───────────────────────────

def start_jarvis(conn):
    asyncio.run(main(conn))

if __name__ == '__main__':
    parent_conn, _ = Pipe()
    p = Process(target=start_jarvis, args=(parent_conn,), daemon=True)
    p.start()
    p.join()
