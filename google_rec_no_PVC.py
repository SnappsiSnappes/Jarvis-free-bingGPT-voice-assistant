# -*- coding: utf-8 -*-



async def google_rec(target:str or list):
    '''

    ```
    Функция слушает микрофон
    принимает в параметры строку или список слов на которые надо реагировать
    при звучании заданых слов - `возвращает True`
    ```
    `` ВАЖНО! строка должна быть с маленьких букв    
    '''


    #import asyncio
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    print('Произнесите - Джарвис')
    while True:
        with microphone as source:
            audio = recognizer.listen(source,phrase_time_limit=4)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
            #print(f"Услышано: {text}")
            if   text.lower() in target:
                #print('success')
                # global canceled
                # canceled = True
                # print("Cancel keyword detected. Cancelling all tasks.")
                
                return True
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    target = ['отмена', 'джарвис']
    import asyncio
    from rich import print
    import speech_recognition as sr
    asyncio.run(google_rec(target))
    #! print(asyncio.run(google_rec(target))) ; output:True
    
