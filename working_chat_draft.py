# -*- coding: utf-8 -*-


# input style
# запустите файл, и напишите свое сообщение в терминале - когда увидите надпись You
# нажмите enter чтобы отправить сообщение и дождитесь ответа
import os
from multiprocessing import Process, Pipe
import time
import asyncio
from tabnanny import check
from EdgeGPT import Chatbot
import sys
import configparser
global config
from modules.working_proxy_getter import proxy_file
from modules.working_reader_proxy import read_proxies
from numpy import argsort

# чтение конфига, для настройки стиля диалога с BingGPT
# всего существует 3 тиля 'creative', 'balanced', 'precise'
# в conifg.ini  
#   [conversation_style]
#   style = creative
config_conversation_style = ''
try:
    config = configparser.ConfigParser()
    config.read('config.ini')
    config_conversation_style = str(config.get('conversation_style','style'))
except:
    print('''создайте config.ini в директории с скриптом и добавьте в него две строчки 
        [conversation_style]
        style = creative''')
    pass

async def main():
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

    check_alive('proxies_stable.txt');check_alive('proxies.txt')
    
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
    bot=''
    #!!
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
                print(f"Ошибка при использовании прокси {proxy}: {e}")
    
    proxy_start_bot_stable_proxy()

    if not bot:
        proxy_start_bot()
    if not bot:
        while True:
            time.sleep(5)
            print('Соединение не установлено, выключите скрипт')
    #!!
    print('---- успешное соединение ----')
    while True:
        prompt = input("\nYou:\n")
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
            if config_conversation_style:
                print((await bot.ask(prompt=prompt,conversation_style=config_conversation_style))["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"],)
            else:
                print(
                (await bot.ask(prompt=prompt))["item"]["messages"][1]["adaptiveCards"][
                    0
                ]["body"][0]["text"],
            )
        else:
            wrote = 0
            async for final, response in bot.ask_stream(prompt=prompt):
                if not final:
                    print(response[wrote:], end="")
                    wrote = len(response)
                    sys.stdout.flush()
            print()
        sys.stdout.flush()
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
