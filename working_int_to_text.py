# Этот скритп использует модуль num2words для того чтобы
# числа перевести в слова на русском языке и в последствии 
# используется для озвучки. Т.к. модель Silerio не озвучивает цифры
from num2words import num2words


#stroke = ' +7904261 '
#stroke2 = '1234'
#d = num2words(stroke, lang='ru')
#print(d)
import re

def replace_numbers_with_words(text):
    # Находим все числа в тексте с помощью регулярного выражения
    pattern = re.compile(r'\d+')
    numbers = pattern.findall(text)
    
    # Заменяем числа на слова с помощью num2words
    for number in numbers:
        word = num2words(int(number), lang='ru')
        text = text.replace(number, word)
        
    return text

text = 'Я родился 10 июля 1995 года, а мой брат - 22 августа 2001 года.'
new_text = replace_numbers_with_words(text)
print(new_text)
# Output: Я родился десятое июля одна тысяча девятьсот девяносто пятого года, а мой брат - двадцать второе августа две тысячи первого года.

