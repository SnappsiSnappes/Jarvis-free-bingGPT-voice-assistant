


#!! working_getter_from_db('открой вк')
#!! return https://vk.com
def working_getter_from_db(text):
    from fuzzywuzzy import fuzz

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
    result = getter_from_db()
    #print(result)

    all_launch_data = {}
    all_open_data = {}

    for action, values in result.items():
        if action == 'запусти':
            for voice, data in values:
                all_launch_data[data] = voice
        elif action == 'открой':
            for voice, data in values:
                all_open_data[data] = voice
    

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

    all_open_data = filter_all_open_data(all_open_data)

    def filtered(voice):
        voice2 = voice
        y = ['запусти', 'запускай', 'запуск']
        x = ['открой', 'открывай', 'открыть']
        data = None
        max_ratio = 0
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


    voice_get = text

    data = filtered(text)
    # print(data)
    # print(
    # all_launch_data,
    # all_open_data)
    return data
    
if __name__ == '__main__':
    text = input('введите команду: ')
    print(working_getter_from_db(text))
    
    #!#old
    #! data = None
    #! for key, value in all_open_data.items():
    #!     if any(voice in voice_get for voice in value):
    #!         data = key
    #!         break
    #! print('data = ', data)

