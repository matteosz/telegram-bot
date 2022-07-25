import requests, os

prefix = 'https://api.telegram.org/bot' + str(os.getenv('BOT_TOKEN'))
MAX_REQ = 10
space = '%20'

def alert(price,url,chat_id):

    text = (f'Product found at €{price}!\n' + url).replace(' ',space) 
    requests.post(prefix + f'/sendMessage?chat_id={chat_id}&text={text}').json()