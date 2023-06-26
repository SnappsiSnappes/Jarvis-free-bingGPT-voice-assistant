# -*- coding: utf-8 -*-

# from working_timer import timer
# @timer
def tranlastor(text,from_lang:str='en',to_lang:str='ru') -> str:
    '''
    - модуль = ``translatepy``
    - модуль использует Google переводчик
    - любая длинна строки
    - работает очень быстро = ``в среднем 0.09 секунд``
    - может обрабатывать список, словарь, строку = ``Возвращает список , словарь, строку``
    '''
    try:
        from modules.working_symbols_to_list import split_string
    except:
        from working_symbols_to_list import split_string
    # лимит в день  => from translate import Translator
    # не работает => from googletrans import Translator
    from translatepy import Translator    

    translator= Translator()

    if type(text) == list:
        response = []
        for i in text:
            i = str(i)
            i = translator.translate(i,to_lang)
            i = str(i)
            response.append(i)
        return response

    elif type(text) == str:
            response = translator.translate(text,to_lang)
            response = str(response)
            return response
        
    elif type(text) == dict:
        response = {}
        for key,i in text.items():
            # Translate value
            i = translator.translate(i,to_lang)
            i = str(i)
            
            # Translate key
            new_key = translator.translate(key,to_lang)
            new_key = str(new_key)
            key = new_key
            # Add translated key-value pair to response
            response[new_key] = i
        return response


    else:
        print(type(text))
        raise Exception('Text is not list, or str, or dict')


if __name__ == '__main__':
    x = tranlastor(text=['привет','бард'],from_lang='ru',to_lang='en')
    print('list ',x, f' type of x = {type(x)}')
    y = tranlastor(text={'привет':'бард'},from_lang='ru',to_lang='en')
    print('dict ',y, f' type of y = {type(y)}')
    z = tranlastor(text=''' привет бааааааааааааард ''',from_lang='ru',to_lang='en')
    print('str ',z, f' type of z = {type(z)}')
