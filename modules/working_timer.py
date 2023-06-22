
def timer(func):
    """```
    - это таймер
    - импортируешь его и ставишь декоратор над
    - любой функцией @timer
    - получишь print результат в секундах
    """
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds to run.")
        print(result)
        return result
    return wrapper
