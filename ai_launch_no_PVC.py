# -*- coding: utf-8 -*-
import array
import json
import os
import queue
import random
import time
from ctypes import POINTER, cast
import simpleaudio as sa
import vosk
import yaml
from comtypes import CLSCTX_ALL
from rapidfuzz import fuzz
from pvrecorder import PvRecorder
from pycaw.pycaw import (
    AudioUtilities,
    IAudioEndpointVolume
)
from rich import print

from display import init_driver, get_driver
from emotion.drivers import EmotionDisplayDriver
from emotion.manager import EmotionManager
from events.broker import EventBroker
from jarvis_skills import load_all, handle_utterance, start_skill_reloader
import speech_recognition as sr
import datetime
import configparser
import click
from multiprocessing import Process, Pipe
import threading

# ! внизу мои модули
from working_getter_from_db import working_getter_from_db

##################################################################
import signal, sys, asyncio, multiprocessing as mp

# Список фоновых процессов Jarvis
child_processes: list[mp.Process] = []

_SND_CACHE: dict[str, sa.WaveObject] = {}


def start_process(target, *args) -> mp.Process:
    """
    Вспомогательная обёртка, чтобы все дочерние процессы
    автоматически попадали в child_processes.
    """
    p = mp.Process(target=target, args=args, daemon=True)
    p.start()
    child_processes.append(p)
    return p


def _shutdown(signum, frame):
    print("\n[Jarvis] Получен сигнал завершения, выключаюсь...")
    # Корректно гасим дочерние процессы
    for p in child_processes:
        if p.is_alive():
            p.terminate()  # или p.join(timeout=3)
    # Завершаем asyncio-цикл (если он ещё крутится)
    try:
        loop = asyncio.get_running_loop()
        loop.stop()
    except RuntimeError:
        pass
    sys.exit(0)


# Регистрируем SIGINT (Ctrl+C) и SIGTERM
signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


##################################################################


# play(f'{CDIR}\\sound\\ok{random.choice([1, 2, 3, 4])}.wav')
async def play(phrase, wait_done=True):
    global recorder
    # recorder.stop()
    # try:
    #     recorder.stop()
    # except:
    #     pass
    filename = f"{CDIR}\\sound\\"

    if phrase == "greet":  # for py 3.8
        filename += f"greet{random.choice([1, 2, 3])}.wav"
    elif phrase == "ok":
        filename += f"ok{random.choice([1, 2, 3])}.wav"
    elif phrase == "not_found":
        filename += 'not_found.wav'
    elif phrase == "thanks":
        filename += 'thanks.wav'
    elif phrase == "run":
        if 5 <= hour < 12:
            # Ваш код для утренней проверки здесь
            filename += f"run{random.choice([1, 2, 3])}.wav"
        elif 12 <= hour < 19:
            # Ваш код для дневной проверки здесь
            filename += f"run{random.choice([1, 2, 4])}.wav"
        else:
            # Ваш код для вечерней/ночной проверки здесь
            filename += f"run{random.choice([1, 2, 5])}.wav"

        # ?filename += f"run{random.choice([1, 2, 3])}.wav"
    elif phrase == "stupid":
        filename += 'stupid.wav'
    elif phrase == "reload":
        filename += f'reload{random.choice([1, 2, 3])}.wav'
    elif phrase == "off":
        filename += 'off.wav'
    elif phrase == 'internet':
        filename += f'internet{random.choice([1, 2, 3])}.wav'
    elif phrase == 'off_internet':
        filename += f'off_internet{random.choice([1, 2, 3])}.wav'
    elif phrase == 'reload':
        filename += f'reload{random.choice([1, 2, 3])}.wav'

    wave_obj = _SND_CACHE.get(filename)
    if wave_obj is None:
        wave_obj = sa.WaveObject.from_wave_file(filename)
    _SND_CACHE[filename] = wave_obj
    play_obj = wave_obj.play()

    if wait_done:
        play_obj.wait_done()


async def custum_command(voice):
    if 'скажи' in voice: return False

    data = f"{working_getter_from_db(text=voice)}"
    if data != 'None':
        await play('ok')
        click.launch(data)

        return True
    else:
        return False


async def execute_cmd(cmd: str, voice: str):
    if cmd == 'sound_off':
        await play("ok", True)

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)

    elif cmd == 'sound_on':
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)

        await play("ok")

    elif cmd == 'thanks':
        await play("thanks")

    elif cmd == 'stupid':
        await play("stupid")

    elif cmd == 'offf':
        global ltc
        await play("off", True)
        # recorder.stop()
        print('заморожен на 30 секунд')
        time.sleep(30)


async def recognize_cmd(cmd: str):
    """
    берет значения(не ключи) из yaml и
    фильтрует через fuzz.raio.
    фильтрует их на совпадение с запросом,
    если хоть что то совпадает больше чем на 0%
    то ключи этого значения
    вставляет в кастомный
    словарь, с командой с
    наимбольшим процентом и с значением
    процента совпадения
    например на запрос -
    "открыть браузер" будет:
    {'cmd': 'open_browser', 'percent': 100}
    """
    rc = {'cmd': '', 'percent': 0}
    for c, v in VA_CMD_LIST.items():

        for x in v:
            vrt = fuzz.ratio(cmd, x)
            if vrt > rc['percent']:
                rc['cmd'] = c
                rc['percent'] = vrt

    return rc


async def filter_cmd(raw_voice: str):
    """
    удаляет слова из запроса:
    'джарвис', 'скажи', 'покажи', 'ответь', 'произнеси', 'расскажи', 'сколько', 'слушай'
    """
    cmd = raw_voice

    for x in VA_ALIAS:
        cmd = cmd.replace(x, "").strip()

    for x in VA_TBR:
        cmd = cmd.replace(x, "").strip()

    return cmd


async def va_respond(voice: str, conn):
    global first_request
    global dd
    print(f"Распознано: {voice}")
    if handle_utterance(voice):
        return True  # скилл ответил, выходим
    voice = str(voice)

    if await custum_command(voice):
        return True

    cmd = await recognize_cmd(await filter_cmd(voice))

    print(cmd)
    # если тишина
    if len(cmd['cmd'].strip()) <= 0:
        # recorder.start()
        return False
    elif cmd['percent'] < 70 or cmd['cmd'] not in VA_CMD_LIST.keys():
        if fuzz.ratio(voice.join(voice.split()[:1]).strip(), "скажи") > 75:

            if first_request:
                first_request = False

            global canceled
            # Создаем и запускаем поток для функции gpt_answer
            canceled = False

            await play('reload')
            return False

        else:
            await play("not_found")

        return False
    else:
        if not await execute_cmd(cmd['cmd'], voice):

            return False
        else:

            return True


async def main(conn):
    print(f"[LOG] Зашли в main")
    global ltc
    global canceled
    global list_of_text
    global CDIR, VA_ALIAS, VA_CMD, recognizer, VA_NAME
    global VA_VER, VA_TBR, VA_CMD_LIST, icrophone_index, model, samplerate, device, kaldi_rec, q, first_request, dd
    global hour, porcupine
    CDIR = os.getcwd()
    VA_CMD_LIST = yaml.safe_load(
        open('commands.yaml', 'rt', encoding='utf8'), )

    init_driver("websocket")
    load_all()

    broker = EventBroker()
    # создаём драйвер эмоций — он подпишется на события
    emo_display = EmotionDisplayDriver(broker)
    # создаём менеджер, запускам фоновые задачи
    emo_manager = EmotionManager(broker, 30)
    emo_manager.start()

    async def _tk_update_loop():
        drv = get_driver()
        while True:
            try:
                drv.process_events()
            except Exception:
                pass
            await asyncio.sleep(0.05)

    asyncio.create_task(_tk_update_loop())

    start_skill_reloader()
    print(f"[LOG] Прошли загрузку скилов")
    # Create a recognizer object and wake word variables
    recognizer = sr.Recognizer()

    # Конфигурация
    VA_NAME = 'Jarvis'
    VA_VER = "3.0"
    VA_ALIAS = ('джарвис',)
    VA_TBR = ('скажи', 'покажи', 'ответь', 'произнеси', 'расскажи', 'сколько', 'слушай')

    # PORCUPINE
    # Токен Picovoice
    global config
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    print(f"[LOG] Прочитали конфиг")
    # VOSK
    MICROPHONE_INDEX = int(config.get('MIC', 'microphone_index'))
    print(f"[LOG] MICROPHONE_INDEX")
    model = vosk.Model("models/model_small")
    print(f"[LOG] Инициализировали модель")
    samplerate = 16000
    print(f"[LOG] samplerate = {samplerate}")
    kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
    print(f"[LOG] Инициализировали sst")
    q = queue.Queue()
    recorder = PvRecorder(device_index=MICROPHONE_INDEX, frame_length=512)
    print(f"[LOG] Инициализировали микрофон")

    # body
    now = datetime.datetime.now()
    hour = now.hour

    global canceled
    canceled = False
    global d
    global dd
    d = {}
    dd = 0

    time.sleep(0.5)
    ltc = time.time() - 1000
    first_request = True
    print('Произнесите команду Джарвис', flush=True)
    await play('run')
    recorder.start()

    counter = 0

    def set_to_false():
        nonlocal wake_worder, counter
        while True:
            wake_worder = False
            time.sleep(30)
            counter = 0

    t = threading.Thread(target=set_to_false, daemon=True)
    t.start()
    wake_worder = False
    listening = False

    while True:
        try:
            pcm = recorder.read()
            pcm_bytes = array.array('h', pcm).tobytes()

            # ── 1) если мы УЖЕ слушаем команду ───────────────────────
            if listening:
                if kaldi_rec.AcceptWaveform(pcm_bytes):
                    cmd = json.loads(kaldi_rec.Result()).get('text', '')
                    if cmd:
                        print("[CMD] :", cmd)
                        # Мьютим микрофон, чтобы не услышать свой же голос
                        recorder.stop()
                        # здесь вызываем skills / TTS:
                        broker.publish("user_query_started")
                        await va_respond(cmd, conn)
                        broker.publish("user_query_ended")
                        # Убираем мьют и рестартуем запись
                        recorder.start()
                        # возвращаемся к режиму «ждём Джарвиса»
                        # listening = False
                        # wake_worder = False
                        kaldi_rec.Reset()
                        # await play('run', False)  # «Произнесите…»

                continue  # пропускаем дальнейшую часть цикла

            # ── 2) обычный режим: ищём wake-word ─────────────────────
            if kaldi_rec.AcceptWaveform(pcm_bytes):
                txt = json.loads(kaldi_rec.Result()).get('text', '')
                if any(w in txt for w in ('джарвис', 'jarvis')):
                    wake_worder = True
            else:
                part = json.loads(kaldi_rec.PartialResult()).get('partial', '')
                if any(w in part for w in ('джар', 'жар', 'jarv')):
                    wake_worder = True

            # ── 3) если поймали имя ─────────────────────────────────
            if wake_worder:
                wake_worder = False  # гасим флаг
                listening = True  # переходим к приёму команды
                kaldi_rec.Reset()  # чистим буфер
                await play('greet', False)
                print("Здравствуйте.")
                ltc = time.time()
                counter = 1  # (если временной сброс нужен)

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise


def main_starter(conn):
    asyncio.run(main(conn))


def ollama_starter(conn):
    while True:
        if conn.poll():
            try:
                prompt = conn.recv()
                from skills.ollama import ollama_ask
                response = ollama_ask(prompt)
                conn.send([response])
            except Exception as e:
                conn.send(["[Ошибка Ollama] %s" % e])


if __name__ == "__main__":
    parent_conn, child_conn = Pipe()
    p1 = Process(target=main_starter, args=(parent_conn,))
    # p2 = Process(target=ollama_starter, args=(child_conn,))
    p1.start()
    # p2.start()
    p1.join()
    # p2.join()

    try:
        p1.join()
        # p2.join()
    except KeyboardInterrupt:
        print("\n[Jarvis] Ctrl+C (главный) – завершаю процессы…")
        # for p in (p1):
        if p1.is_alive():
            p1.terminate()  # мгновенно убивает
            p1.join(3)  # ждём ≤ 3 с для надёжности
        print("[Jarvis] Готово, можно вводить команды.")
