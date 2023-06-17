
# возвращает 1 рабочую прокси
# достать ее можно:
# random_func = proxy_getter()
# print(random_func[1])
import asyncio
from proxybroker import Broker

#from working_timer import timer
#@timer
# 0.59 sec, 0.69 sec
def proxy_getter():

    async def get_proxies(proxies):
        """Get a proxy and return it as a string."""
        proxy = await proxies.get()
        if proxy is None:
            return None
        return '%s:%d' % (proxy.host, proxy.port)

    def main():
        proxies = asyncio.Queue()
        broker = Broker(proxies)
        tasks = asyncio.gather(broker.grab(countries=['US', 'GB'], limit=1),
                            get_proxies(proxies))
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(tasks)
        #print(result[1]) output = 157.245.27.9:3128
        return result
    return main()

if __name__ == '__main__':
    random_func = proxy_getter()
    print('я random func [1]= ',random_func[1])