### Платформа - Windows 7 / 10 x64
### python 3.10.6
<details>
  <summary>Установка</summary>
  
- Имя пользователя Windows не должно содержать кирилицы.
- Клонируйте репозиторий на свой компьютер.
- ОПЦИОНАЛЬНО:
 Создайте виртуальное окружение с помощью команды в **CMD/powershell** 
```python -m venv venv``` и активируйте его ```.\venv\Scripts\activate``` 
( Чтобы сделать это нажмите на пустое место в директории SHIFT+RIGHT CLICK > Открыть CMD здесь или Открыть PowerShell здесь)
- Python 3.10.6 x64 - проверено
- Установите все зависимости с помощью команды 
```
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements2.txt
```
Если видите ошибки то разберитесь с ними и установити зависимости. Проблемный модуль - PyAudio
Требуется много зависимостей связанных с C++ Redist, и прочие. К сожалению пока так.
- установите ffmpeg корректным образом, внизу есть пояснение
- отредактируйте config.ini и выберите модель bard/bing
- запуск
```
python ai_launch.py
или
python ai_launch_no_PVC.py
```
</details>

### UPD: смотрите видео

# Jarvis - ваш голосовой ассистент


![1382_wide_small2](https://user-images.githubusercontent.com/111605401/235349662-31b3ea1e-c4f7-43bc-9959-792e51a27a2d.png)
<details>
  <summary>Видео</summary>

[![Watch the video](https://user-images.githubusercontent.com/111605401/235522397-1c1fdd5f-6dc1-4dea-9b4b-aa0c260baabd.png)](https://www.youtube.com/watch?v=BE-5cg2RLVs)
</details>

<details>
<summary>Возможности</summary>

- Голосовое обращение к BingGPT, с возможностью отменить запрос, чтобы отменить запрос достаточно сказать слово ОТМЕНА, чтобы сделать запрос - после слова Джарвис скажите "Скажи ...(ваш запрос)" прим. Скажи кто такие рыцари? 
- Возможность создавать свои команды - запускать свои файлы и открывать свои сайты - для этого используйте working_gui.py или working_gui.exe в корневом каталоге.
- быстрая реакция, лучшее качество записи и воспроизведения, использованы лучшие бесплатные библиотеки.
- Автоматизированное подключение через прокси. Работает стабильно из РФ.
</details>

### Список команд - в yaml документе commands.yaml 


<details>
  <summary>Инструкции Bard</summary>
  
- ``приемущества :`` легко, быстро
- ``недостатки :`` из за перевода происходит неграмотный ответ , используется двойной перевод. 

  1) Зайдите на сайт , используя впн , получите доступ к барду , используя свой гугл аккаунт - https://bard.google.com/?hl=en ![image](https://github.com/SnappsiSnappes/Jarvis-free-bingGPT-voice-assistant/assets/111605401/1a908389-6356-4c2b-a674-3576a74a34d6)
  2) вставьте токен в config.ini - [bard_token] token = ![image](https://github.com/SnappsiSnappes/Jarvis-free-bingGPT-voice-assistant/assets/111605401/a3c6d1c5-3c68-4f07-92ce-cf5b08c90713)

  
</details>

<details>
  <summary>Инструкции Bing</summary>

- ``Приемущества:`` Качественные ответы, креатив, грамотность
- ``Недостатки:`` Необходимость установки MS EDGE браузера, учетная запись Microosft, ВПН, необходимость обновлять cookies раз в 12 часов, нестабильность работы в последнее время. Долгое время ожидания ответа.
  
1) Сначала зарегистрируйте учетную запись Microsoft и скачайте последнюю версию Microsoft Edge.
2) Используйте VPN, если вы находитесь в России. (РАСШИРЕНИЕ BROWSEC: https://chrome.google.com/webstore/detail/browsec-vpn-free-vpn-for/omghfjlpggmjjaagoclmmobgdodcjboh)
3) Перейдите на https://www.bing.com/ и получите доступ к чату на основе GPT в Bing (установите страну своей учетной записи как США).
4) Скачайте расширение https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm.
5) Перейдите на домашнюю страницу Bing и нажмите кнопку "Export cookies" в формате json в буфер обмена.
6) Создайте файл внутри директории со скриптом, назовите его - 'cookies.json' и вставьте свои куки в этот файл.
7) Следуйте инструкциям Использование.
</details>




<details>
  <summary>Инструкции gpt3</summary>
  
- ``приемущества :`` Очень легко, очень быстро, зачастую этого достаточно обычному пользователю
- ``недостатки :`` Не умеет пользоваться интернетом, знания ограничены интернетом до 2021 года

  1) в config.ini в графе ai, сделайте model = gpt3

  
</details>


<summary> Авто замена cookies.json и прокси </summary>

- В случае ошибки установки связи с BingGPT - произойдет автоматическая замена cookies.json на новые. За это отвечает working_edge_update_cookies.py
- Авто-замена cookies работает только от python 3.10 , то есть у тех у кого Windows 10 , тем у кого Windows 7 придется обновлять cookies.json раз в 12 часов.
## принцип обновления cookies
1) Выйдите из Microsoft EDGE браузера
- запустите ai_launch.py или working_update_cookies.py
- ![image](https://github.com/SnappsiSnappes/Jarvis-free-bingGPT-voice-assistant/assets/111605401/5bc7cfa2-cd24-40ae-8e9a-0d4bec9357ef)
2) вы увидите в консоли Trying to update cookies 
3) ждите 
4) далее увидите в терминале много текста - значит все ок, cookies обновлены. Файл cookies.json создан
5) ждите до появления строчки - __"Успешное соединение"__ потом можете спокойно говорить свой запрос.
  
- Совет: на MS EDGE ставьте расширение впн - Browsec  - постоянно включенным.
</details>

<details>
<summary>Проблемы с правильной установкой ffmpeg</summary>
  
- Как понять что ffmpeg установлен? - ввидите ffmpeg в CMD или PowerSHELL
1) Установите ffmpeg любым удобным для вас способом. https://ffmpeg.org/download.html
- распокуйте папку в любую директорию (например C:/ffmpeg) и занесите в переменную PATH путь до например C:/ffmpeg/bin/
2) быстрый способ - Установите Chocolately, используя этот код в PowerShell:```
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))```
Затем, используя PowerShell, выполните: ```choco install ffmpeg```
3) другой способ : https://www.youtube.com/watch?v=jZLqNocSQDM посмотрите видео инструкцию
</details>

<details>
<summary>Использование</summary>
  
- Замените ключ в config.ini - [PICOVOICE_TOKEN]  на свой API-ключ. (зарегестрируйтесь на https://console.picovoice.ai ,чтобы получить его бесплатно)
- Запустите скрипт ai_launch.py
- Скажите Джарвис -  чтобы разбудить бота.
- Ваш запрос начинается на - "Скажи","Расскажи" - тогда Джарвис пойдет в интернет и спросит у BingGPT ответ на ваш запрос, во время запроса можно сказать слово ОТМЕНА - чтобы отменить. Если у вас ошибка - "Перезагрузите джарвиса" или какая то иная, проверьте создали ли вы cookies.json
- Создавайте команды - например Открой инстаграм, открой гугл и тд.
- Используйте working_gui.py чтобы добавить свои команды .
вот так выглядит интерфейс добавления своих команд.
### ![image](https://user-images.githubusercontent.com/111605401/235350281-a9ed8476-584a-4f2c-aad8-0ec2447635ba.png)
### ![image](https://user-images.githubusercontent.com/111605401/235444261-15d79af0-36eb-4b36-b485-9c3f57f88540.png)
</details>

<details>
<summary> Обратите внимание: </summary>
  
- Первое - октрой/запусти , открой - указывайте сайт в данные https:// somewebsite.com (можно без https/http), запусти - указыайте метоположение файла пример - c:/dir/my_file.exe.
- Слово открой/запусти писать не надо.
- В графе "Что сказать" - пишите  через запятую то что необходимо услышать программе, в случае обнаружения будет выполнен запуск - того что вы напишите в "Данные". Используйте длинные слова. Пример "Что сказать": контакты, контакт "Данные" : vk.com  
- Данные - о том что писать , сказанно выше. c:/dir/my_file.exe. - в запусти. https:// somewebsite.com (можно без https/http), - в открой.
Ваши команды находятся в базе данных mydatabase.db , если его удалить, тогда он создастся снова, и будет пуст.
- Скажите Джарвису то, что написали в графе - "Что говорить", и файл, или веб сайт, будет открыт.
- В файле config.ini [add_to_prompt]
add_to_prompt = можно указать какой нибудь стиль выдачи, который будет все время добавляться к вашим запросом в бинг - в КОНЕЦ запроса. Например если написать - напиши коротко, в простом стиле. Тогда все ответы будут короткими и упрощенными на сколько это возможно. ВАЖНО! Строчка должна быть в кавычках вся. 
- В файле config.ini - можно указать индекс микрофона, по умолчанию это -1 
### Схема работы 😊 
![схема](https://user-images.githubusercontent.com/111605401/235351434-7f6c7d9a-8289-4e02-b4d2-07ddc94b2af5.png)
</details>


donate - https://www.donationalerts.com/r/snappes_tv
<details>
<summary>Все файлы с приставкой working_...</summary>

работают автономно, в их коде содержится подробное описание и принцип работы.
По сути это файлы конструкторы, можете использовать их для своих программ
</details>
