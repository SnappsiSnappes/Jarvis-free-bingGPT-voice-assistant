


def working_tts(text:str):
    '''```
    Лучший модуль. Озвучивает текст.
    - text = строка, любой длинны. 
    Если больше 1000 символов то будет разделение на список
    из элементов по 1000 символов и будет озвучен каждый элемент списка
    - можно выбрать голос озвучки
    - Нажмите ESC чтобы закончить воспроизведение
    >>> speaker = 'eugene' 
    # aidar, baya, kseniya, xenia, eugene, random
    '''
    # Импортируем необходимые библиотеки
    
    import torch
    import sounddevice as sd
    import time
    from silero import silero_stt, silero_tts, silero_te
    from transliterate import translit
    import keyboard

    from modules.working_symbols_to_list import split_string
    from working_numbers_to_words import numbers_to_wards
    from modules.working_remove_space_in_numbers import remove_spaces_in_numbers
    

    # переменная для остановки аудиозвучки
    global stop_signal
    stop_signal = False

    global print_counter
    print_counter = 0
    def stop_tts():
        '''
        Для останов озвучивания достаточно нажать ESC
        '''
        global stop_signal
        global print_counter
        if print_counter == 0 :
            print_counter += 1
            print('''\n Озвучивание началось \n Для остановки нажмите ESC\n''')
        while sd.get_stream().active:
            if keyboard.is_pressed('esc'):
                sd.stop()
                stop_signal = True
                break
            time.sleep(0.1)

    # Переводим цифры в текст
    text = numbers_to_wards(text)
    
    # Перевод текста в русскиий язык из английского
    # Sam = Сэм
    text = translit(text,'ru')

    # удаление пробелов между цифрами
    text = remove_spaces_in_numbers(text)

    # Устанавливаем параметры для TTS
    language = 'ru'
    model_id = 'v3_1_ru'
    sample_rate = 48000
    speaker = 'eugene'  # aidar, baya, kseniya, xenia, eugene, random
    put_accent = True
    put_yo = True
    device = torch.device('cpu')
    
    # Загружаем модель TTS из репозитория snakers4/silero-models
    model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
                              model='silero_tts', language=language, speaker=model_id)
    model.to(device)

    # если строка больше 1000 символов то разделяется на массивов и озвучивается
    # 1000 = лимит
    if len(text) >1000:
        text = split_string(text,1000)
        for i in text:
            if stop_signal == False:
            
                audio = model.apply_tts(text=i,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=put_accent,
                                put_yo=put_yo)
                sd.play(audio, sample_rate)
                #!
                stop_tts()
                #!time.sleep(len(audio) / sample_rate)
                sd.stop
    else:
        # Применяем TTS к тексту и получаем аудиоданные
        text = str(text)
        audio = model.apply_tts(text=text,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)
        # Воспроизводим аудиоданные с помощью sounddevice
        sd.play(audio, sample_rate)
        #!
        stop_tts()
        #!time.sleep(len(audio) / sample_rate)
        sd.stop


if __name__ == '__main__':
    working_tts(""" Ваш текст """)
