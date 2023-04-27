


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
    from EdgeGPT import Chatbot
    import sys
    from numpy import argsort
    import asyncio
    from working_edge_update_cookies import working_edge_update_cookies

    """
    Main function
    """

    print("Initializing...")
    global bot
    bot = ''
    try:
        
        bot = Chatbot(cookie_path='cookies.json')
    except:
        print('Cookies timout, trying to update cookies')
        try:working_edge_update_cookies();
        except:pass
        try:

            bot = Chatbot(cookie_path='cookies.json')
        except: print('ПЕРЕЗАГРУЗИТЕ ДЖАРВИСА')
    
        
    while True:
        await asyncio.sleep(5)
        if conn.poll(): # проверяем, есть ли данные для чтения
            prompt = conn.recv()
            print(prompt)
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
                    print(response)

                    conn.send(response) # отправляем ответ в другой процесс
                except: 
                    try:working_edge_update_cookies();
                    except:pass

                    try:                    
                        response = (
                        (await bot.ask(prompt=prompt))["item"]["messages"][1]['text'], 
                        #!! ниже версия с карточками сайтов - ссылками
                    #   (await bot.ask(prompt=prompt))["item"]["messages"][1]["adaptiveCards"][
                        #     0
                        # ]["body"][0]["text"],
                        #!! end
                        )
                        print(response)
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
