# Используя модуль pvporcupine этот скрипт слушает микрофон и распознает слово "отмена"
# В случае успеха исполняется код = print('отмена')
# Запустите скрипт и скажите слово - "отмена" , чтобы увидить результат

# в параметрах функции conn=None не используется напрямую в коде.
# Conn = connection используется для Pipe multiprocessing

def main(conn=None):
    import pvporcupine
    import configparser

    from pvrecorder import PvRecorder
    from rich import print
    config = configparser.ConfigParser()
    config.read('config.ini')
    keyward_path = r'vosk_+_pvporcupine\отмена_ru_windows_v2_2_0.ppn'
    model_path = r'vosk_+_pvporcupine\porcupine_params_ru.pv'
    PICOVOICE_TOKEN   = config.get('PICOVOICE_TOKEN','token')
    porcupine         = pvporcupine.create(
        access_key    = PICOVOICE_TOKEN,
        keyword_paths=[f'{keyward_path}'], 
        keywords=['отмена'],
        model_path=f'{model_path}',
        sensitivities = [0]
    )


    # VOSK
    MICROPHONE_INDEX  = int(config.get('MIC','microphone_index'))
    # model            = vosk.Model("model_small")
    # samplerate       = 16000
    # BUFFER_SIZE      = 512                        # Количество байт в буфере записи
    # SAMPLE_RATE      = 16000                      # Частота дискретизации
    # device           = MICROPHONE_INDEX
    # kaldi_rec         = vosk.KaldiRecognizer(model, samplerate)
    # p = pyaudio.PyAudio()
    recorder = PvRecorder(device_index=MICROPHONE_INDEX, frame_length=porcupine.frame_length)


    # rec   = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    # stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True,
    #                 frames_per_buffer=BUFFER_SIZE, input_device_index=MICROPHONE_INDEX)

    # def get_next_audio_frame():
    #   pass
    # while True:
    #   audio_frame = get_next_audio_frame()
    #   keyword_index = porcupine.process(audio_frame)
    """
    if keyword_index == 0:
    # detected `отмена`
    elif keyword_index == 1:
    # detected `любое другое слово...👌`
    """
    recorder.start()
    while True:
        # Считываем аудиоданные из потока
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)
        if keyword_index == 0:
            print('отмена')
            # conn.send('отмена')
            
if __name__ == '__main__':
    main()
    # main(conn)
