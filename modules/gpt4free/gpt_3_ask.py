# -*- coding: utf-8 -*-






def gpt_3_ask(conn) -> str:
    '''```
    используя иодуль gpt-4-free эта функция обращается к 
    сервисам в интернете которые бесплатно дают пользоваться
    gpt_3_5 .
    - не имеет доступа к интернету
    использование:
    `   text = 'приветствую'
        i = gpt_3_ask(text=text)
        print(i) 
    `
    ```
    ``ответ: Здравствуйте! Как я могу помочь вам?``
        
    '''
    import time
    from multiprocessing import Process, Pipe

    try:
        import g4f
    except:
        from modules.gpt4free import g4f

    from g4f.Provider import (
        Ails,
        You,
        Bing,
        Yqcloud,
        Theb,
        Aichat,
        Bard,
        Vercel,
        Forefront,
        Lockchat,
        Liaobots,
        H2o,
        ChatgptLogin,
        DeepAi,
        GetGpt
    )

    #H2o
    #GetGpt
    #Aichat
    #Yqcloud



    gpt3_easy_list = [Aichat,GetGpt,H2o,Yqcloud]



    def asker(text):
        for i in gpt3_easy_list:
            try:
                response = g4f.ChatCompletion.create(provider=i,model='gpt-3.5-turbo', messages=[
                                            {"role": "user", "content": f"{text}"}]) # alterative model setting
            except:
                continue
            if response: break
        return response


    while True:
        time.sleep(5)
        if type(conn) != str:
            if conn.poll():
                prompt = conn.recv()
                response= asker(prompt)
                conn.send(response)

        else: 
            return asker(conn)
            


if __name__ == '__main__':
     text = 'приветствую'
     i = gpt_3_ask(conn=text)
     print(i,type(i))