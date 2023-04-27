

def working_tts(text):
    import torch
    import sounddevice as sd
    import time
    language    = 'ru'

    model_id    = 'v3_1_ru'
    sample_rate = 48000
    speaker     = 'eugene'
    #aidar, baya, kseniya, xenia, eugene, random
    put_accent  = True
    put_yo      = True
    device      = torch.device('cpu')

    if isinstance(text, str):
        pass

    model, _                              = torch.hub.load(repo_or_dir='snakers4/silero-models',
                            model         = 'silero_tts',language=language,speaker=model_id)
    model.to(device)
    audio                                 = model.apply_tts(text=text,
                            speaker       = speaker,
                            sample_rate   = sample_rate,
                            put_accent    = put_accent,
                            put_yo        = put_yo)

    #print(text)

    sd.play(audio,sample_rate)
    time.sleep(len(audio)/sample_rate)
    sd.stop

if __name__ == '__main__':
    working_tts('произнесите команду ДЖААрвИс, чтобы продолжить...')

   #? if phrase == "greet":  # for py 3.8
   #?     filename += f"greet{random.choice([1, 2, 3])}.wav"
   #? elif phrase == "ok":
   #?     filename += f"ok{random.choice([1, 2, 3])}.wav"
   #? elif phrase == "not_found":
   #?     filename += "not_found.wav"
   #? elif phrase == "thanks":
   #?     filename += "thanks.wav"
   #? elif phrase == "run":
   #?     filename += "run.wav"
   #? elif phrase == "stupid":
   #?     filename += "stupid.wav"
   #? elif phrase == "ready":
   #?     filename += "ready.wav"
   #? elif phrase == "off":
   #?     filename += "off.wav"