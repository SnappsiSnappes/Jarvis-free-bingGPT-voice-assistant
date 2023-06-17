


# читает файл proxies
# возвращает в переменную список 
# в которую возвращает каждую строчку
# пробелы и знак /n игнорирует

def read_proxies(filename='proxies.txt'):
    with open(filename, 'r') as f:
        lines = f.readlines()
    proxies = ['http://' + line.strip() for line in lines if line.strip()]
    return proxies

if __name__ =='__main__':
    proxies = read_proxies('proxies.txt')
    print(proxies)
