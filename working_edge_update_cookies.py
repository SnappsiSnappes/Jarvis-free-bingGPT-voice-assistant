# Этот скрипт обновляет Cookies.json в папке
# Работает только на win 10 и выше
# Здесь используется копия вашей User Data
# Это сделано потому что ваша User Data защищена и 
# Не может быть использована
# - Чтобы использовать скрипт, запустите его, подождите
# Как только он завершит работу то закроет терминал и 
# Вы можете увидить обновленную cookies.json в папке с проектом 

def working_edge_update_cookies():
    from selenium.webdriver import Edge
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    import edgedriver_autoinstaller
    import json
    import os
    import shutil
    import time
    from subprocess import CREATE_NO_WINDOW

    try:
        remove = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data1')
        shutil.rmtree(remove)
    except:pass
    # path = str(edgedriver_autoinstaller.install())
    # src = rf'{path}'
    # dst = os.path.dirname(os.path.abspath(__file__))
    # if not os.path.exists(os.path.join(dst, 'msedgedriver.exe')):
    #     shutil.move(src, dst)
    def check():
        try:
            edge_path2 = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data1')
            
            os.path.exists(edge_path2)
            src = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data')
            shutil.copytree(src, edge_path2)
        except:
            pass

    try:

        edgedriver_autoinstaller.install()  # Check if the current version of edgedriver exists
                                        # and if it doesn't exist, download it automatically,
                                        # then add edgedriver to path


        check()
        edge_path = (f"{os.path.expanduser('~')}/AppData/Local/Microsoft/Edge/User Data1")
        print(edge_path)
        options = Options()
        options.add_argument(f"--user-data-dir={edge_path}")
        # options.add_argument("--headless")
        # options.binary_location = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--start-maximized")
        options.add_argument('--disable-background-timer-throttling') # exp
        options.add_argument('--remote-allow-origins=*')
        options.add_argument('--disable-dev-shm-usage')
        #options.add_argument('--no-sandbox')
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        #options.add_argument("--silent")
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-extensions') # exp
        options.use_chromium = True
        options.add_argument("--headless=new")


        s = Service(executable_path=r"msedgedriver.exe")
        driver = Edge(service=s, options=options)



        # driver.implicitly_wait(5) # exp
        driver.get('https://www.bing.com/')
        print('зашел')
        time.sleep(2)
        cookies = driver.get_cookies()
        print(cookies)
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)
        print('успешно обновил cookies.json')
        driver.quit()
    except: print('error')

if __name__ == '__main__':
    working_edge_update_cookies()
