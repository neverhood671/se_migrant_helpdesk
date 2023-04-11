import requests
from token_provider import get_telegram_token

BASE_URL = 'https://api.telegram.org/bot{}'
SEND_MESSAGE_SUB_URL = '/sendMessage'
EDIT_MESSAGE_SUB_URL = '/editMessageText'


def post(sub_url, data):
    token = get_telegram_token()
    url = BASE_URL.format(token) + sub_url
    return requests.post(url, json=data)


def send_new_message(data):
    return post(SEND_MESSAGE_SUB_URL, data)


def update_message(data):
    return post(EDIT_MESSAGE_SUB_URL, data)
