




async def working_chat(conn):
    """
    1) сделайте pipe
    2) отправляйте сюда запрос таким образом
    
while True:            
    ...
    conn.send('запрос')     -1 
    while True:
        if conn.poll():     -2
            response = conn.recv() -3
            break
            response ...
            ...
            break
        time.sleep(3) #<-или await asyncio.sleep(3)
    """
    from multiprocessing import Process, Pipe
    from EdgeGPT import Chatbot
    import sys
    from numpy import argsort
    import asyncio
    import os
    from working_edge_update_cookies import working_edge_update_cookies
    from modules.working_proxy_getter import proxy_file
    from modules.working_reader_proxy import read_proxies
    """
    Main function
    """
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

    check_alive('proxies_stable.txt')
    
    def create_proxy():
        """создание прокси файла proxies.txt"""
        p1 = Process(target=proxy_file)
        p1.start()
        p1.join()

    create_proxy()

    #добавление прокси списка в переменную proxy_list
    proxy_list = read_proxies()
    stable_proxy_list = read_proxies('proxies_stable.txt')
    print("Initializing...")

    global bot
    bot = ''
    
    # идея в том чтобы сохранять стабильные прокси в отдельный файл

    def proxy_start_bot_stable_proxy():
        """
        Пытается подключиться к боту используя стабильные прокси
        стабильные прокси создаются если был успешный ответ от бота

        """
        global bot
        
        for proxy in stable_proxy_list:
            try:
                bot = Chatbot(cookie_path='cookies.json', proxy=proxy)
                
                break
            except Exception as e:
                if str(e) == 'Cookie file not found':
                    print('пытаюсь обновить cookies')
                    try:
                        working_edge_update_cookies()
                    except Exception as e:
                        print(e,' Ошибка обновления cookies, обновите cookies самостоятельно.')
                        sys.exit()
                    continue
                print(f"Ошибка при использовании прокси {proxy}: {e}")
                proxy_without_http = proxy.replace('http://' , '') # удаляет 'http//' так как в файле proxies_stable.txt нет прифекса 'http//'  
                remove_stable_proxy_file('proxies_stable.txt', proxy_without_http) # удаляем нестабильный прокси


    def proxy_start_bot():
        """
        Пытается подключиться к боту используя прокси
        """
        global bot
        for proxy in proxy_list:
            try:
                bot = Chatbot(cookie_path='cookies.json', proxy=proxy)
                append_stable_proxy_file('proxies_stable.txt', f'{proxy}')
                break
            except Exception as e:
                if str(e) == 'Cookie file not found':
                    print('пытаюсь обновить cookies')
                    try:
                        working_edge_update_cookies()
                    except:
                        print('Ошибка обновления cookies, обновите cookies самостоятельно.')
                        sys.exit()
                    continue
                print(f"Ошибка при использовании прокси {proxy}: {e}")
    proxy_start_bot_stable_proxy()

    if not bot:
        proxy_start_bot()
    #!!
    # if not bot:
    #     print('Все прокси не работают, пытаемся обновить cookies')
    #     try:
    #         working_edge_update_cookies()
    #         proxy_start_bot()
    #         #bot = Chatbot(cookie_path='cookies.json')
    #     except Exception as e:
    #         print(f"Ошибка при обновлении cookies: {e}")
    #         print('ПЕРЕЗАГРУЗИТЕ ДЖАРВИСА')
    #!!
    if not bot:
        print("ПЕРЕЗАГРУЗИТЕ ДЖАРВИСА")
    
    print('Успешное соединение')
    
    
    while True:
        await asyncio.sleep(5)
        if conn.poll(): # проверяем, есть ли данные для чтения
            prompt = conn.recv()
            #! print(prompt)
            if prompt == "!exit":
                break
            elif prompt == "!help":
                print(
                    """
                !help - Show this help message
                !exit - Exit the program
                !reset - Reset the conversation
                """,
                )
                continue
            elif prompt == "!reset":
                await bot.reset()
                continue
            print("Bot:")
            if argsort:
                try:
                    response = (
                        (await bot.ask(prompt=prompt))["item"]["messages"][1]['text'],
                        #!! ниже версия с карточками сайтов - ссылками
                    #   (await bot.ask(prompt=prompt))["item"]["messages"][1]["adaptiveCards"][
                        #     0
                        # ]["body"][0]["text"],
                        #!! end
                    )
                    #! print(response)

                    conn.send(response) # отправляем ответ в другой процесс

                except: 
                    #! try:working_edge_update_cookies()
                    #! except:continue

                    try:         
                        await bot.reset()           
                        response = (
                        (await bot.ask(prompt=prompt))["item"]["messages"][1]['text'])
                        #! print(response)
                        conn.send(response) # отправляем ответ в другой процесс
                    except: pass
                        

            else:
                wrote = 0
                async for final, response in bot.ask_stream(prompt=prompt):
                    if not final:
                        print(response[wrote:], end="")
                        wrote = len(response)
                        sys.stdout.flush()
                print()
            sys.stdout.flush()                

        else:
            await asyncio.sleep(1) # ждем 1 секунду перед следующей проверкой

            

    await bot.close()

# if __name__ == "__main__":
#      asyncio.run(main())

if __name__ == "__main__":
    import asyncio
    conn = input("Enter your message: ")
    asyncio.run(working_chat(conn))
