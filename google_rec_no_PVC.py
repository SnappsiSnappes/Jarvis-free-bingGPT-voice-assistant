# Простой скрипт, используется модуль от Google
# для распознования речи, в параметрах функции указывается
# строка - слово - услышав которое будет инициирован выход из цикла While True
# и программа завершится
async def google_rec(target:str):
    
    import asyncio
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    print('Произнесите - Джарвис')
    while True:
        with microphone as source:
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"Recognized text: {text}")
            if target in text.lower():
                # global canceled
                # canceled = True
                # print("Cancel keyword detected. Cancelling all tasks.")
                
                return True
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    target = 'отмена'
    import asyncio
    from rich import print
    import speech_recognition as sr
    asyncio.run(google_rec(target))
    #! print(asyncio.run(google_rec(target))) ; output:True
    
