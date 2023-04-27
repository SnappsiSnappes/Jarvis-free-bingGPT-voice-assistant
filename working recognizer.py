
import asyncio
async def listen_for_cancel():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
    
    print('Listening for cancel keyword...')
    while True:
        with microphone as source:
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
            print(f"Recognized text: {text}")
            if "отмена" in text.lower():
                global canceled
                canceled = True
                print("Cancel keyword detected. Cancelling all tasks.")
                return
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Request error: {e}")

if __name__ == "__main__":
    import asyncio
    from rich import print
    import speech_recognition as sr
    asyncio.run(listen_for_cancel())