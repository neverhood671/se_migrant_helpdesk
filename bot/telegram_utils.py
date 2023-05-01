from typing import Optional

import requests
from token_provider import get_telegram_token

BASE_URL = 'https://api.telegram.org/bot{}'
SEND_MESSAGE_SUB_URL = '/sendMessage'
EDIT_MESSAGE_SUB_URL = '/editMessageText'


class MessageAction:
    def __init__(
            self,
            action_type: str,
            chat_id: int,
            first_name: str,
            new_text: str,
            new_message_id: Optional[int] = None,
    ):
        self.action_type = action_type
        self.chat_id = chat_id
        self.first_name = first_name
        self.new_message_id = new_message_id
        self.new_text = new_text


def post(sub_url, data):
    token = get_telegram_token()
    url = BASE_URL.format(token) + sub_url
    return requests.post(url, json=data)


def send_new_message(data):
    return post(SEND_MESSAGE_SUB_URL, data)


def update_message(data):
    return post(EDIT_MESSAGE_SUB_URL, data)
