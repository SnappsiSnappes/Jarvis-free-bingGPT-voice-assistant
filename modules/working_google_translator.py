
#модуль использует Google переводчик
#
#Лимит = 500 символов
#в среднем 1.35 секунд для 500 символов
from translate import Translator
#from working_timer import timer
#@timer
def tranlastor(text):
    translator= Translator(to_lang="ru")
    response = translator.translate(text)
    print(response)
    return response

if __name__ == '__main__':
    tranlastor(text='''hi''')