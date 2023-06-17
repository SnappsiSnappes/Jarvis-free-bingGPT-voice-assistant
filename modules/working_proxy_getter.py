
# создает файл proxies.txt и добавляет туда ip
# можно указать limit=10 тогда будет 10 адресов


def proxy_file():
    import asyncio
    from proxybroker import Broker
    async def save(proxies, filename):
        """Save proxies to a file."""
        with open(filename, 'w') as f:
            while True:
                proxy = await proxies.get()
                if proxy is None:
                    break
                f.write('%s:%d\n' % (proxy.host, proxy.port))


    def main():
        proxies = asyncio.Queue()
        broker = Broker(proxies)
        tasks = asyncio.gather(broker.grab(countries=['US', 'GB'], limit=10),
                            save(proxies, filename='proxies.txt'))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(tasks)
    main()


if __name__ == '__main__':
    proxy_file()