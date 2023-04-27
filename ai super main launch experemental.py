import asyncio
import re
import vosk
import json
import os
import queue
import random
import struct
import subprocess
import time
from ctypes import POINTER, cast
import re
import pvporcupine
import simpleaudio as sa
import vosk
import yaml
from comtypes import CLSCTX_ALL
from fuzzywuzzy import fuzz
from pvrecorder import PvRecorder
from pycaw.pycaw import (
    AudioUtilities,
    IAudioEndpointVolume
)
from rich import print
from working_tts import working_tts
from pydub import playback
import speech_recognition as sr
from EdgeGPT import Chatbot, ConversationStyle
import datetime
from num2words import num2words
from transliterate import translit, get_available_language_codes

from multiprocess_bing import working_chat
# from working_edge_update_cookies import working_edge_update_cookies
# working_edge_update_cookies()
from multiprocessing import Process, Pipe
from multiprocess_wake_word_recogintion import wake_word_recognition

import configparser


# play(f'{CDIR}\\sound\\ok{random.choice([1, 2, 3, 4])}.wav')
async def play(phrase, wait_done=True):
    global recorder
    recorder.stop()
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

        #?filename += f"run{random.choice([1, 2, 3])}.wav"
    elif phrase == "stupid":
        filename += 'stupid.wav'
    elif phrase == "ready":
        filename += 'ready.wav'
    elif phrase == "off":
        filename += 'off.wav'
    elif phrase == 'internet':
        filename += f'internet{random.choice([1, 2, 3])}.wav'
    elif phrase == 'off_internet':
        filename += f'off_internet{random.choice([1, 2, 3])}.wav'
    elif phrase == 'reload':
        filename += f'reload{random.choice([1, 2, 3])}.wav'


    wave_obj = sa.WaveObject.from_wave_file(filename)
    play_obj = wave_obj.play()

    if wait_done:
        play_obj.wait_done()
        # time.sleep((len(wave_obj.audio_data) / wave_obj.sample_rate) + 0.5)
        # print("END")
        # time.sleep(0.5)
        recorder.start()


async def execute_cmd(cmd: str, voice: str):
    recorder.stop()
    if cmd == 'open_browser':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run browser.exe'])
        await play("ok")

    elif cmd == 'open_youtube':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run youtube.exe'])
        await play("ok")

    elif cmd == 'open_google':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run google.exe'])
        await play("ok")

    elif cmd == 'music':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run music.exe'])
        await play("ok")

    elif cmd == 'music_off':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Stop music.exe'])
        time.sleep(0.2)
        await play("ok")

    elif cmd == 'music_save':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Save music.exe'])
        time.sleep(0.2)
        await play("ok")

    elif cmd == 'music_next':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Next music.exe'])
        time.sleep(0.2)
        await play("ok")

    elif cmd == 'music_prev':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Prev music.exe'])
        time.sleep(0.2)
        await play("ok")

    elif cmd == 'sound_off':
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

    elif cmd == 'gaming_mode_on':
        await play("ok")
        subprocess.check_call([f'{CDIR}\\custom-commands\\Switch to gaming mode.exe'])
        await play("ready")

    elif cmd == 'gaming_mode_off':
        await play("ok")
        subprocess.check_call([f'{CDIR}\\custom-commands\\Switch back to workspace.exe'])
        await play("ready")

    elif cmd == 'switch_to_headphones':
        await play("ok")
        subprocess.check_call([f'{CDIR}\\custom-commands\\Switch to headphones.exe'])
        time.sleep(0.5)
        await play("ready")

    elif cmd == 'switch_to_dynamics':
        await play("ok")
        subprocess.check_call([f'{CDIR}\\custom-commands\\Switch to dynamics.exe'])
        time.sleep(0.5)
        await play("ready")

    elif cmd == 'off':
        await play("off", True)

        porcupine.delete()
        exit(0)



def replace_numbers_with_words(text):
    # Находим все числа в тексте с помощью регулярного выражения
    pattern = re.compile(r'\d+')
    numbers = pattern.findall(text)
    
    # Заменяем числа на слова с помощью num2words
    for number in numbers:
        word = num2words(int(number), lang='ru')
        text = text.replace(number, word)
    return text


async def listen_for_cancel():
    global canceled

    recorder.stop()
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    print('Listening for cancel keyword...')
    
    while not canceled:
        recorder.stop()
        with microphone as source:
            audio = recognizer.listen(source)
            await asyncio.sleep(4)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"Recognized text: {text}")
            if "отмена" in text.lower():
                
                canceled = True
                print("Cancel keyword detected. Cancelling all tasks.")
                await play('internet_off')
                return
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Request error: {e}")


async def vosk_listen_for_cancel():
    global canceled
    recorder.stop()
    import vosk
    import pyaudio
    import json

    MICROPHONE_INDEX  = -1 # Индекс микрофона, -1 чтобы выбрать по умолчанию
    BUFFER_SIZE       = 2048 # Количество байт в буфере записи
    SAMPLE_RATE       = 16000 # Частота дискретизации

    # Загружаем модель и создаем распознаватель
    model = vosk.Model("model_small")
    rec   = vosk.KaldiRecognizer(model, SAMPLE_RATE)

    # Создаем объект pyaudio для записи аудио
    p = pyaudio.PyAudio()

    # Открываем поток для чтения аудио из микрофона
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True,
                    frames_per_buffer=BUFFER_SIZE, input_device_index=MICROPHONE_INDEX)

    # Цикл записи и распознавания аудио
    while canceled == False:
        
        # Считываем аудиоданные из потока
        data = stream.read(BUFFER_SIZE)
        if len(data) == 0:
            break

        # Передаем данные в распознаватель
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())["text"]
            print(result)
            print('можно сказать ОТМЕНА')
            await asyncio.sleep(4)

            if 'отмен' in result:
                canceled = True
                print("Cancel keyword detected. Cancelling all tasks.")
                bot = Chatbot(cookie_path='cookies.json')
                await bot.close()
                await play('off_internet')
                

                # Останавливаем поток и освобождаем ресурсы
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                return

def split_string(s):
    return [s[i:i+1000] for i in range(0, len(s), 1000)]

async def gpt_answer(text: str,conn):
    global dd
    global d
    global recorder, ltc
    global canceled
    recorder.stop()
    global list_of_text

    await play('internet')

    parent_conn, child_conn = Pipe()
    p1 = Process(target=wake_word_recognition, args=(child_conn,))
    p1.start()
    

    def check_for_cancel():
        recorder.stop()
        global canceled
        if parent_conn.poll():
            canceled = parent_conn.recv()
            return True
        return canceled

    while not canceled:

        print('Jarvis зашел в интернет')        
        #!!
        # bot = Chatbot(cookie_path='cookies.json')
        # print('gpt_answer passed bot , before await')
        # await asyncio.sleep(2)
        # response = await bot.ask(prompt=text, conversation_style=ConversationStyle.creative)
        # #print(response)
        # for message in response["item"]["messages"]:
        #     if message["author"] == "user":
        #         global test
        #         test = str(message['text'])
        #         print('я тест',test)
        #         print('я текст',text)
        #!!
        # Select only the bot response from the response dictionary
        #отправляем запрос в working 
        canceled = check_for_cancel()
        if canceled == True:break
        conn.send(text)
        while True:
            canceled = check_for_cancel()
            if canceled == True:break
                
            if conn.poll():
                canceled = check_for_cancel()
                if canceled == True:break
                response = conn.recv()
                response = f'{response[0]}'
                print('response- ',response)
                #?
                # for message in response["item"]["messages"]: 
                #     if message["author"] == "bot":
                #         bot_response = message["text"]
                #?
                # Remove [^#^] citations in response
                bot_response = response
                bot_response = re.sub('\[\^\d+\^\]', '', bot_response)
                bot_response = bot_response.replace('привет, это Bing',' вот что я нашел в интернете ')
                bot_response = bot_response.replace('Здравствуйте, это Bing','вот что я нашел ')
                bot_response = bot_response.replace('Здравствуйте',' ')
                bot_response = bot_response.replace('Привет',' ')
                bot_response = bot_response.replace('Привет,',' ')
                bot_response = bot_response.replace('это Bing',' ')
                bot_response = translit(bot_response, 'ru')
                
                pogoda = ['погода','градус', "погоду","градусов","градус","погод"]
                for word in pogoda:
                    if word in text:
                        bot_response = bot_response.replace('+','плюс ')
                        bot_response = bot_response.replace('-','минус ')
                        bot_response = bot_response.replace('°',' ')

                replaced_numbers = replace_numbers_with_words(bot_response)

                """
                фикс бага. суть бага = озвучивал запрос, говорил отмена, на следующий запрос
                джарвис озвучивает - ответ на старый запрос который был отменен, а через некоторое время
                озвучивает ответ на последний запрос. я создал счетчики и словарь
                решение с джарвисом алгоритм -
                -
                делаем счетчик запросов начинающийся с еденицы
                делаем словарь с запрос-ответ
                обновляется счетчик например 2 запроса = читаем второй элемент, если его нет ждем его
                -
                d = словарь
                dd = счетчик

                """

                len_of_texts=len(list_of_text)

                
                dd = dd+1
                d.update({dd: [text,replaced_numbers]})

                # len_of_d = len(d)
                # print(len_of_texts)
                # print(d)
                # print(dd)
                # print(len_of_d)
                #!result = split_string(d[len_of_texts][1])

                #?Speech_it = d[len_of_texts][1]
                #?print('я Speech_it=',Speech_it)
                canceled = check_for_cancel()
                if canceled == True:break
                try:
                    
                    Speech_it = d[len_of_texts][1] #!ddd
                            
                    if Speech_it:
                        result = split_string(d[len_of_texts][1])
                        for i in result:
                            working_tts(i)
                        # print(Speech_it)
                        # working_tts(result) устарело
                        canceled = True
                        p1.terminate()
                    else:
                        print('что то пошло не так...')
                        canceled = True
                        p1.join()
                        p1.terminate()
                        
                except:pass
            await asyncio.sleep(5)
            recorder.stop()
            
            continue
        
async def recognize_cmd(cmd: str):
    rc = {'cmd': '', 'percent': 0}
    for c, v in VA_CMD_LIST.items():

        for x in v:
            vrt = fuzz.ratio(cmd, x)
            if vrt > rc['percent']:
                rc['cmd'] = c
                rc['percent'] = vrt

    return rc


async def filter_cmd(raw_voice: str):
    cmd = raw_voice

    for x in VA_ALIAS:
        cmd = cmd.replace(x, "").strip()

    for x in VA_TBR:
        cmd = cmd.replace(x, "").strip()

    return cmd

async def va_respond(voice: str,conn):
    global recorder
    global message_log
    global first_request
    global dd
    print(f"Распознано: {voice}")
    recorder.stop()
    

    cmd = await recognize_cmd(await filter_cmd(voice))

    print(cmd)

    if len(cmd['cmd'].strip()) <= 0:
        recorder.start()
        return False
#TODO fix/add comands
    elif cmd['percent'] < 70 or cmd['cmd'] not in VA_CMD_LIST.keys():
        # play("not_found")
        # tts.va_speak("Что?")
        if fuzz.ratio(voice.join(voice.split()[:1]).strip(), "скажи") > 75:

            if first_request:
                message_log.append({"role": "user", "content": voice})
                first_request = False

            global canceled
            global list_of_text
            # Создаем и запускаем поток для функции gpt_answer
            canceled = False
            # создаем счетчик для алгоритма - корректного озвучивания
            list_of_text.append(voice)
            
            print('list_of_text=',list_of_text)
            # создаем задачи

            await gpt_answer(voice,conn)

            # !answer_task = asyncio.create_task(gpt_answer(voice,conn))
            #########?cancel_task = asyncio.create_task(listen_for_cancel()) #медленная версия
            #cancel_task = asyncio.create_task(vosk_listen_for_cancel())
            # ждем, пока хотя бы одна из задач не завершится
            #?await asyncio.gather(answer_task, cancel_task, return_exceptions=True)
            # !done, _ = await asyncio.wait([answer_task, cancel_task], return_when=asyncio.FIRST_COMPLETED,timeout=120)
            # # отменяем оставшуюся задачу
            # !for task in done:
            # !    task.cancel(
            
            # устанавливаем флаг отмены
            #canceled = True
            # ждем завершения оставшихся задач
            
            #? await gpt_answer(voice)
            
            # time.sleep(0.5)
            recorder.start()
            await play('reload')
            return False
        else:
            await play("not_found")
            time.sleep(1)

        return False
    else:
        await execute_cmd(cmd['cmd'], voice)
        return True
    

async def main(conn):
    
    global ltc
    
    global canceled
    global list_of_text
    # some consts
    global CDIR,VA_ALIAS,VA_CMD, recognizer,VA_NAME
    global VA_VER,VA_TBR , VA_CMD_LIST,icrophone_index, model, samplerate, device, kaldi_rec, q, recorder, CHROME_PATH, message_log, first_request, dd
    global hour, porcupine
    CDIR              = os.getcwd()
    VA_CMD_LIST       = yaml.safe_load(
        open('commands.yaml', 'rt', encoding='utf8'),
    )
    # Create a recognizer object and wake word variables
    recognizer        = sr.Recognizer()

    # Конфигурация
    VA_NAME           = 'Jarvis'
    VA_VER            = "3.0"
    VA_ALIAS          = ('джарвис',)
    VA_TBR            = ('скажи', 'покажи', 'ответь', 'произнеси', 'расскажи', 'сколько', 'слушай')
    #TODO сделать requirements.txt
    # PORCUPINE
    # Токен Picovoice
    config = configparser.ConfigParser()
    config.read('config.ini')

    PICOVOICE_TOKEN   = config.get('PICOVOICE_TOKEN','token')
    porcupine         = pvporcupine.create(
        access_key    = PICOVOICE_TOKEN,
        keywords      = ['jarvis'],
        sensitivities = [1]
    )

    # Путь к браузеру Google Chrome
    CHROME_PATH       = r'C:\Program Files (x86)\Google\Chrome\Application'
    # VOSK
    MICROPHONE_INDEX  = int(config.get('MIC','microphone_index'))
    model             = vosk.Model("model_small")
    samplerate        = 16000
    device            = MICROPHONE_INDEX
    kaldi_rec         = vosk.KaldiRecognizer(model, samplerate)
    q                 = queue.Queue()
    recorder          = PvRecorder(device_index=MICROPHONE_INDEX, frame_length=porcupine.frame_length)
    # ChatGPT vars
    message_log = [
        {"role": "system", "content": "Ты голосовой ассистент из железного человека."}
    ]

    #body
    now = datetime.datetime.now()
    hour = now.hour

    global canceled
    canceled = False
    global list_of_text
    list_of_text = []
    global d
    global dd
    d = {}
    dd = 0

    recorder.start()
    time.sleep(0.5)
    ltc = time.time() - 1000
    first_request = True
    print('Using device: %s' % recorder.selected_device)

    await play('run')
    
    while True:
        try:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            
            

            if keyword_index == 0:
                recorder.stop()
                await play('greet',True)
                print("Здравствуйте.")
                recorder.start()  # prevent self recording
                ltc = time.time()
            #! while True делает бесконечный цикл и он не спит
            #!while time.time() - ltc <= 10: 
            while time.time() - ltc <= 20: 

                pcm = recorder.read()
                sp = struct.pack("h" * len(pcm), *pcm)

                if kaldi_rec.AcceptWaveform(sp):
                    if await va_respond(json.loads(kaldi_rec.Result())["text"],conn):
                        ltc = time.time()

                    break

        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

def working_chat_starter(conn):
    asyncio.run(working_chat(conn))

def main_starter(conn):
    asyncio.run(main(conn))

if __name__ == "__main__":
    parent_conn, child_conn = Pipe()
    p1 = Process(target=main_starter, args=(parent_conn,))
    p2 = Process(target=working_chat_starter, args=(child_conn,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

