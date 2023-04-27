

def wake_word_recognition(conn=None):
    import configparser

    import pvporcupine
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
            print("Cancel keyword detected. Cancelling all tasks.")
            canceled = True
            conn.send(canceled)
            
if __name__ == '__main__':
    wake_word_recognition()
    # main(conn)