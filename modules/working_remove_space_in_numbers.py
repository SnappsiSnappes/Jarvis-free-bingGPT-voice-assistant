# -*- coding: utf-8 -*-


def remove_spaces_in_numbers(text:str):
    '''```
    Удаляет пробел в цифрах
    `150 7242 , 126 000, 123435 345`
    >>>
    `1507242 , 126000, 123435345`
    -> str
    `возвращает строку без пробелов между цифрами`
    '''
    import re
    return re.sub(r'(\d)\s+(\d)', r'\1\2', text)

if __name__ == '__main__':
    text = '150 7242 , 126 031, 123435 345'
    result = remove_spaces_in_numbers(text)
    print(type(result))
