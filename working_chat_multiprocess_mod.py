# этот скрипт по сути тоже самое что working chat draft
# Однако здесь используется multiprocess и Pipe соединения
# Между 2 функциями, одна из которых работает ассинхронно
# - Чтобы использовать скрипт запустите его и перед вами
# Появится окно в которое можно ввести текст, введите текст
# Далее функция через соединение Pipe передаст ваш текст в 
# В working chat через переменную conn. Подождите и вы 
# Увидите ответ в терминале, затем можете продолжить общение


from multiprocessing import Process, Pipe
from multiprocess_bing import working_chat
import asyncio
import time


def starter(conn):
    
    asyncio.run(working_chat(conn))




def second_function(conn):
    import tkinter as tk
    #tk
    def on_ok():
        nonlocal x
        x = entry.get()
        root.destroy()

    x = None
    while True:
        d = []
        x=''

        root = tk.Tk()
        entry = tk.Entry(root,width=33,font=('Helvetica', 20),fg='blue')
        entry.pack(pady=17)
        ok_button = tk.Button(root, text='OK', command=on_ok, font=('Helvetica', 16),
                              bg='lightblue',width=22, height=2,justify='center',
                              anchor='center', highlightbackground='lightblue',
                              )
        ok_button.pack(pady=10)
        root.mainloop()
        #? tk end
        print('я second_function. мой x =',x)
        if not x:
            continue
        d.append(x)
        #super
        conn.send(d[-1])

        time.sleep(5)
        while True:

            if conn.poll():
                response = conn.recv()
                print(f"Received response: {response[-1]}")
                d.clear()
                break
            time.sleep(3)
            
"""
while True:
    ...
    conn.send('запрос')     -1
    while True:
        if conn.poll():     -2
            response = conn.recv() -3
            break
        time.sleep(3)
"""

if __name__ == '__main__':
    
    # x = input('вводи сюда... ')
    parent_conn, child_conn = Pipe()
    p1 = Process(target=starter, args=(child_conn,))
    p2 = Process(target=second_function, args=(parent_conn,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
