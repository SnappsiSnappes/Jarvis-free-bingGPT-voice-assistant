
# Офлайн переводчик , чтобы использовать - в параметры введите текст для перевода
# 2.26 секунд = 1 слово 'hi'
# 2.34 секунд в среднем
# 3.17 секунд = 841 символов 
# 3.82 сек = 1175 символов
#from working_timer import timer
#@timer
def offline_translator(text=str, from_lang:str='en',to_lang:str='ru'):
    """
    ### Офлайн переводчик 
    чтобы использовать:
    1) в параметры введите текст для перевода
    2) from_lang = 'ru' пример
    3) to_lang = 'en' пример
    - без лимита на длину строчки
    - 2.26 секунд = 1 слово 'hi'
    - 2.34 секунд в среднем
    - 3.17 секунд = 841 символов 
    - 3.82 сек = 1175 символов
    """
    import argostranslate.package
    import argostranslate.translate

    from_code = from_lang
    to_code = to_lang

    # Download and install Argos Translate package
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
        )
    )
    argostranslate.package.install_from_path(package_to_install.download())

    # Translate
    translatedText = argostranslate.translate.translate(text, from_code, to_code)
    print(translatedText)
    return translatedText
    # '¡Hola Mundo!'
if __name__ == '__main__':
    
    offline_translator('hi.') # сюда текст 'hello world' <-пример