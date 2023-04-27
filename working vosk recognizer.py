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
while True:
    # Считываем аудиоданные из потока
    data = stream.read(BUFFER_SIZE)
    if len(data) == 0:
        break

    # Передаем данные в распознаватель
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())["text"]
        print(result)
        

# Останавливаем поток и освобождаем ресурсы
stream.stop_stream()
stream.close()
p.terminate()
