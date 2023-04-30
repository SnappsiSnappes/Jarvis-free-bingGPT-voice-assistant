# jarvis - ваш голосовой ассистент

![1382_wide_small2](https://user-images.githubusercontent.com/111605401/235349662-31b3ea1e-c4f7-43bc-9959-792e51a27a2d.png)
## Возможности
- Голосовое обращение к BingGPT, с возможностью отменить запрос, чтобы отменить запрос достаточно сказать слово ОТМЕНА, чтобы сделать запрос - после слова Джарвис скажите "Скажи ...(ваш запрос)" прим. Скажи кто такие рыцари? 
- Возможность создавать свои команды - запускать свои файлы и открывать свои сайты - для этого используйте working_gui.py или working_gui.exe в корневом каталоге.
- быстрая реакция, лучшее качество записи и воспроизведения, использованы лучшие бесплатные библиотеки.
### Список команд - в yaml документе commands.jaml 
- В случае ошибки установки связи с BingGPT - произойдет автоматическая замена cookies.json на новые. За это отвечает working_edge_update_cookies.py
## Инструкции
1) Сначала зарегистрируйте учетную запись Microsoft и загрузите Microsoft Edge (если еще этого не сделали).
2) Используйте VPN, если вы находитесь в России.
3) Перейдите на https://www.bing.com/ и получите доступ к чату на основе GPT в Bing (установите страну своей учетной записи как США).
4) Скачайте расширение https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm.
5) Перейдите на домашнюю страницу Bing и нажмите кнопку "Export cookies" в формате json в буфер обмена.
6) Создайте файл внутри директории со скриптом, назовите его - 'cookies.json' и вставьте свои куки в этот файл.
7) Следуйте инструкциям USAGE.

## Проблемы с правильной установкой ffmpeg
- Установите Chocolately, используя этот код в PowerShell:'''
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))'''
Затем, используя PowerShell, выполните: choco install ffmpeg
## Использование
- Установите зависимости: pip install -r requirements.txt
- Замените ключ в config.cfg - [PICOVOICE_TOKEN]  на свой API-ключ. (зарегестрируйтесь на https://console.picovoice.ai ,чтобы получить его бесплатно)
- Запустите скрипт ai_launch.py
- Скажите Джарвис -  чтобы разбудить бота.
- Ваш запрос начинается на - "Скажи","Расскажи" - тогда Джарвис пойдет в интернет и спросит у BingGPT ответ на ваш запрос, во время запроса можно сказать слово ОТМЕНА - чтобы отменить.
- Используйте working_gui.py чтобы добавить свои команды , или working_gui.exe - это одно и то же.
вот так выглядит интерфейс добавления своих команд.
![image](https://user-images.githubusercontent.com/111605401/235350281-a9ed8476-584a-4f2c-aad8-0ec2447635ba.png)
Ваши команды находятся в базе данных mydatabase.db , если его удалить, тогда он создастся снова, и будет пуст.
