import tkinter as tk
import sqlite3

# Подключение к базе данных SQLite
conn = sqlite3.connect('mydatabase.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS mytable (id INTEGER PRIMARY KEY, action TEXT, voice TEXT, data TEXT)')

# Функция для обновления списка элементов
def update_listbox():
    listbox.delete(0, tk.END)
    for row in c.execute('SELECT * FROM mytable'):
        listbox.insert(tk.END, f"{row[0]}: {row[1]} - {row[2]} - {row[3]}")

# Функция для удаления выбранного элемента
def delete_item():
    selection = listbox.curselection()
    if selection:
        item_id = int(listbox.get(selection[0]).split(':')[0])
        c.execute('DELETE FROM mytable WHERE id=?', (item_id,))
        conn.commit()
        update_listbox()

# Функция для добавления нового элемента
def add_item():
    action = action_var.get()
    voice = voice_entry.get()
    data = data_entry.get()
    if action and voice and data:
        c.execute('INSERT INTO mytable (action, voice, data) VALUES (?, ?, ?)', (action, voice, data))
        conn.commit()
        update_listbox()


# Создание главного окна
root = tk.Tk()
root.title('Создатель команд')
root.resizable(False, False)
root.geometry('500x560')
try:
    root.iconbitmap('snappes.ico')
except:pass
# Создание списка и кнопок удаления и добавления
frame = tk.Frame(root)
frame.pack()
yscrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
xscrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
listbox = tk.Listbox(frame, width=80, height=15, yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set,
                     font=('TkDefaultFont', 13))
listbox.pack(side=tk.LEFT)
update_listbox()
yscrollbar.config(command=listbox.yview)
xscrollbar.config(command=listbox.xview)
delete_button = tk.Button(root, text='Удалить', command=delete_item, width=10, height=2)
delete_button.pack()
action_var = tk.StringVar(root)
action_var.set('запусти')
action_options = ['запусти', 'открой']
action_menu = tk.OptionMenu(root, action_var, *action_options)
action_menu.config(width=20, height=2)
action_menu.pack()
voice_label = tk.Label(root, text='Что произнести:',font=('TkDefaultFont', 13))
voice_label.pack()
voice_entry = tk.Entry(root,width=35,font=('TkDefaultFont', 13))
voice_entry.pack()
data_label = tk.Label(root, text='Данные:',font=('TkDefaultFont', 13))
data_label.pack()
data_entry = tk.Entry(root,width=35,font=('TkDefaultFont', 13))
#!!
data_entry.pack()
#!!
add_button = tk.Button(root, text='Добавить', command=add_item, width=10, height=2)
add_button.pack()

# Запуск главного цикла
root.mainloop()

# Закрытие соединения с базой данных
conn.close()