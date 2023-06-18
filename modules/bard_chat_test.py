from os import environ
from Bard import Chatbot

token =''
#! proxy='http://18.143.215.49:80' 
chatbot = Chatbot(token,proxy='http://8.219.97.248:80')

response= chatbot.ask("Hello, how are you?")
print(response['content'])
