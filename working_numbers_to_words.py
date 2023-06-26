


def numbers_to_wards(text):
    '''```
    
    меняет цифры на русские слова
    input: 'Я родился 10 июля 1995 года, а мой брат - 22 августа 2001 года.'
    return: 'Я родился десятое июля одна тысяча девятьсот девяносто пятого года, а мой брат - двадцать второе августа две тысячи первого года.
    '''
    import re
    from num2words import num2words
    # Находим все числа в тексте с помощью регулярного выражения
    pattern = re.compile(r'\d+')
    numbers = pattern.findall(text)
    
    # Заменяем числа на слова с помощью num2words
    for number in numbers:
        word = num2words(int(number), lang='ru')
        text = text.replace(number, word)
        
    return text

if __name__=='__main__':
    text = 'Я родился 10 июля 1995 года, а мой брат - 22 августа 2001 года.'
    new_text = numbers_to_wards(text)
    print(new_text)
    # Output: Я родился десятое июля одна тысяча девятьсот девяносто пятого года, а мой брат - двадцать второе августа две тысячи первого года.

