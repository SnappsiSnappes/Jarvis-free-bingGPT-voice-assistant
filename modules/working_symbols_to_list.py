

def split_string(stroke:str, amount_of_wards:int=1000):
        '''возвращает список из большой строчки, делит строчку таким образом. параметр = длина элемента строчки
        пример использования
        ``text = split_string(text,500)``
        '''
        return [stroke[i:i+amount_of_wards] for i in range(0, len(stroke), amount_of_wards)]



if __name__ == '__main__':
    x = """123"""

    print(split_string(x))
