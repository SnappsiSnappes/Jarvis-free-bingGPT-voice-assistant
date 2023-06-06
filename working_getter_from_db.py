
# Этот скрипт парсит базу данных на наличие строки
# В параметрах которую мы передали при запуске
# Используется модуль fuzzywuzzy чтобы найти совпадение.
# Работает очень хорошо и стабильно
# - Чтобы пользоваться скриптом, создайте свою команду используя
# Working_gui . Запустите скрипт напишите искомую строчку
# В терминале - используется input.
# Строчка подразумивает собой поле - "Что говорить", вы должны были
# Ранее создать свою команду и указать эту строчку.
# !! После обновления не надо писать/говорить "запусти" или "открой"
# просто напишите что нужно открыть или запустить
# пример input: вк; output: https://vk.com/
from numpy import empty


def working_getter_from_db(text):
    if 'запусти' not in text and 'открой' not in text:
        data1 = working_getter_from_db(f'запусти {text}')
        data2 = working_getter_from_db(f'открой {text}')

        #print(data1,data2)
        if data1 != None:
            return data1
        elif data2 != None:
            return data2

    # Импортируем необходимые библиотеки
    from fuzzywuzzy import fuzz

    # Функция для получения данных из базы данных
    def getter_from_db():
        import sqlite3
        conn = sqlite3.connect('mydatabase.db')
        c = conn.cursor()
        result = {}
        for row in c.execute('SELECT action, voice, data FROM mytable'):
            action, voice, data = row
            if action not in result:
                result[action] = []
            result[action].append((voice.split(','), data))
        conn.close()
        return result

    # Получаем данные из базы данных
    result = getter_from_db()

    # Инициализируем словари для хранения данных о запуске и открытии
    all_launch_data = {}
    all_open_data = {}

    # Заполняем словари данными из базы данных
    for action, values in result.items():
        if action == 'запусти':
            for voice, data in values:
                all_launch_data[data] = voice
        elif action == 'открой':
            for voice, data in values:
                all_open_data[data] = voice

    # Функция для фильтрации ключей в словаре all_open_data
    def filter_all_open_data(all_open_data):
        """
        фильтрует ключи
        из yandex.ru сделает https://yandex.ru
        из http://yandex.ru ничего не сделает 
        """
        new_all_open_data = {}
        for key, value in all_open_data.items():
            if not key.startswith('https://') and not key.startswith('http://'):
                new_key = 'https://' + key
            else:
                new_key = key
            new_all_open_data[new_key] = value
        return new_all_open_data

    # Фильтруем ключи в словаре all_open_data
    all_open_data = filter_all_open_data(all_open_data)

    # Функция для поиска соответствующих данных для текста голосового сообщения
    def filtered(voice):
        voice2 = voice
        y = ['запусти', 'запускай', 'запуск']
        x = ['открой', 'открывай', 'открыть']
        data = None
        max_ratio = 50
        if any(word in voice for word in x):
            for key, value in all_open_data.items():
                for v in value:
                    vrt = fuzz.ratio(voice2, v)
                    if vrt > max_ratio:
                        max_ratio = vrt
                        data = key
        elif any(word in voice for word in y):
            for key, value in all_launch_data.items():
                for v in value:
                    vrt = fuzz.ratio(voice2, v)
                    if vrt > max_ratio:
                        max_ratio = vrt
                        data = key
        if max_ratio > 0:
            return data
        else:
            return None

    # Ищем соответствующие данные для текста голосового сообщения и возвращаем их
    data = filtered(text)
    return data


if __name__ == '__main__':
    text = input('введите команду: ')
    print(working_getter_from_db(text))

