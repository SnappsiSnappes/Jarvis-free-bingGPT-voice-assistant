from os import environ
from Bard import Chatbot

token = 'Wwi9j9nchaxcQDhVeoDC02n-vQwMZ9B1lxVFR9omKmO5_whtPHZ2-D4nH1O6BlKePD10-Q.'
#! proxy='http://18.143.215.49:80' 
chatbot = Chatbot(token,proxy='http://8.219.97.248:80')

response= chatbot.ask("Hello, how are you?")
print(response['content'])