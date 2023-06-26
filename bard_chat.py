# -*- coding: utf-8 -*-




def bard_msg(text):
    '''```
    Модуль для отправки сообщения Барду.
    - стартует бот через прокси генератор.
    - определяет язык
    - русский переводит в английский для барда,
    - английский переводит в русский для пользователя
    - `Возвращает ответ барда -> str`
      
    '''
    # фикс asyncio 
    import nest_asyncio
    nest_asyncio.apply()
    import asyncio

    import configparser
    from Bard import Chatbot
    import langid

    # мои модули
    from modules.start_bot_bard import start_bot

    from modules.working_symbols_to_list import split_string
    from modules.working_google_translator import tranlastor
    
    # 1) делаем из текста список, при этом делим на 500 символов его
    text = split_string(text,500)
    # 2) пытаемся понять что за язык в параметре text    
    # если русский текст то переводим в англ
    for i in text:
        if langid.classify(i) == 'ru' or 'bg':
            text = tranlastor(i,from_lang='ru',to_lang='en')
        # если англ то pass
        elif langid.classify(i)[0] == 'en':
            print('англ текст')

    text = str(text)
    
#получение токена
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        token = str(config.get('bard_token','token'))
    except:
        print('''
        ! Ошибка получения токена !
            создайте config.int в директории с скриптом и добавьте в него две строчки 
            [bard_token]
            token = ваш токен
            токен это google_dev_tools => Application => __Secure-1PSID
            ''')
        
    # token = 'ваш токен , где взять? ответ: > на странице с бардом  режим разработчика в браузере > Application => __Secure-1PSID '
    
    bot = asyncio.run(start_bot(token=token))
    #bot = Chatbot(token)

    response= bot.ask(text)
    response = response['content']#!
    #print('я len(respnse) = ',len(response))
    response = tranlastor(response,'en','ru')
    #print('я respnse = ',response)
    #print('\n', 'я len(respnse) = ',len(response))
    
    
    return response

if __name__=='__main__':
    response = bard_msg(''' скажи создатели South park - братья? кто они вообще
      ''')
    print('я рабочий ',response)
    from working_tts import working_tts
    working_tts(response)