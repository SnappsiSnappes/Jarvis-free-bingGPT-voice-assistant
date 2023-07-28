# -*- coding: utf-8 -*-

async def start_bot(token:str):
    '''
    ### Эта функция стартует бард бота, используя прокси.
    - ``требуется параметр token`` -  токен можно взять в браузере на странице барда => google_dev_tools => Application => __Secure-1PSID
    - ``Возвращает 1 переменную : ``
    - ``bot`` =  `bot` - стартуется бот, после успешного соедниения , в коде можно использовать ``bot.ask``
    ### ``предпочитаемый вариант использования: ``

    ```
    token = 'ваш токен , где взять? ответ: > на странице с бардом  режим разработчика в браузере > Application => __Secure-1PSID '
    bot = asyncio.run(start_bot(token=token))
    response= bot.ask("how to safely drink water?") -- ваш запрос - на англ
    print(response['content'])
    ```
    '''
    import os
    from multiprocessing import Process, Pipe
    import time
    import asyncio
    from tabnanny import check
    from Bard import Chatbot    

    import nest_asyncio
    nest_asyncio.apply()

    try:
        from modules.working_proxy_getter import proxy_file
        from modules.working_reader_proxy import read_proxies
    except:
        from working_proxy_getter import proxy_file
        from working_reader_proxy import read_proxies




    async def main(token):

        
        def append_stable_proxy_file(filename:str,proxy:str):
            """ читает файл и если не находит строчку из параметра 
            proxy - то добавляет ее в конец файла
            - ### используется в случае успешного подключения """
            proxy = proxy.replace('http://', '')
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if proxy not in lines:
                    with open('proxies_stable.txt', 'a', encoding='utf-8') as file:
                        file.write(proxy)

        def remove_stable_proxy_file(filename:str,proxy:str):
            """ ### используется для удаления строчки с нерабочим прокси
            ### в параметры указать имя файла , и прокси """
            with open(filename, 'r') as file:
                lines = file.readlines()
            with open(filename, 'w') as file:
                for line in lines:
                    if line.strip("\n") != proxy:
                        file.write(line)



        def check_alive(filename):
            """чек есть ли файл, если нет то создает пустой"""
            if os.path.exists(f'{filename}') == False:
                with open(f'{filename}',"a+",encoding='utf=8') as g: g.close()

        check_alive('proxies_stable.txt');check_alive('proxies.txt')

        proxy_file()
        #добавление прокси списка в переменную proxy_list
        proxy_list = read_proxies()
        stable_proxy_list = read_proxies('proxies_stable.txt')

        print("\nInitializing...")
        global bot
        bot=''

        def proxy_start_bot_stable_proxy(token):
            """
            Пытается подключиться к боту используя стабильные прокси
            стабильные прокси создаются если был успешный ответ от бота

            """
            global bot
            
            for proxy in stable_proxy_list:
                try:
                    bot = Chatbot(token, proxy=proxy)
                    print('\n',f'Успешное соединение через прокси {proxy}')
                    break
                except Exception as e:
                    print(f"Ошибка при использовании прокси {proxy}: {e}")
                    proxy_without_http = proxy.replace('http://' , '') # удаляет 'http//' так как в файле proxies_stable.txt нет прифекса 'http//'  
                    remove_stable_proxy_file('proxies_stable.txt', proxy_without_http) # удаляем нестабильный прокси


        async def proxy_start_bot(token):
            """
            Пытается подключиться к боту используя прокси
            """
            global bot
            for proxy in proxy_list:
                try:
                    bot = Chatbot(token, proxy=proxy, timeout=3)
                    append_stable_proxy_file('proxies_stable.txt', f'{proxy}')
                    print('\n',f'Успешное соединение через прокси {proxy}')
                    break
        
                except Exception as e:
                    print(f"Ошибка при использовании прокси {proxy}: {e}")
        
        proxy_start_bot_stable_proxy(token)

        if not bot:
            await proxy_start_bot(token)
        if not bot:
            proxy_file()
            await proxy_start_bot(token)


        print('---- успешное соединение ----')
    
    asyncio.run(main(token))
    return bot

    #asyncio.create_task(main(token=token))

if __name__ == '__main__':
    #import nest_asyncio
    #nest_asyncio.apply()
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()

    import configparser
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
    asyncio.run(start_bot(token))