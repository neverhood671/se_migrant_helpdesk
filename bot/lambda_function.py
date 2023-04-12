import json
import logging

import telegram_utils as t_utils
from dynamo_db_provider import DynamoDb

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        if 'message' in event:
            process_message(event)
        elif 'callback_query' in event:
            process_callback(event)
        else:
            print(f'WARN Undefined request type. event: {json.dumps(event)}')
    except Exception as error:
        logger.error('Something goes wrong. Event: %s, Error: %s', {json.dumps(event)}, error)
        return {
            'statusCode': 500,
            'body': json.dumps('Something goes wrong')
        }

    return {'statusCode': 200}


def process_message(event):
    message = event['message']
    text = message['text']
    message_id = message['message_id']
    chat_id = message['chat']['id']
    first_name = message['chat']['first_name']

    response_text = f'{first_name}, you said: {text}'
    data = {
        'text': response_text.encode('utf8'),
        'chat_id': chat_id,
        'reply_markup': {
            'inline_keyboard': [[
                {'text': '👍', 'callback_data': 'good_answer'},
                {'text': '👎', 'callback_data': 'bad_answer'}
            ]]
        }
    }

    response = t_utils.send_new_message(data)

    if response.status_code >= 300:
        print(f'Response status code: {response.status_code}')
        print(f'Response content: {response.content}')
    else:
        response_message_id = json.loads(response.content)['result']['message_id']
        DynamoDb().save_question(
            chat_id=chat_id,
            question_message_id=message_id,
            question=text,
            response_message_id=response_message_id,
            answer=response_text
        )


def process_callback(event):
    callback_query = event['callback_query']
    callback_data = callback_query['data']
    message = callback_query['message']
    message_id = message['message_id']
    text = message['text']
    chat_id = message['chat']['id']

    if callback_data == 'good_answer':
        vote = '👍'
    elif callback_data == 'bad_answer':
        vote = '👎'
    else:
        print(f'ERROR Unknown data: {callback_data}')
        return

    response_text = f'{text}\n\nYou voted as {vote}'
    data = {
        'text': response_text.encode('utf8'),
        'chat_id': chat_id,
        'message_id': message_id,
        'reply_markup': {
            'inline_keyboard': [[]]
        }
    }
    response = t_utils.update_message(data)
    if response.status_code >= 300:
        print(f'Response status code: {response.status_code}')
        print(f'Response content: {response.content}')
    else:
        DynamoDb().save_vote(
            chat_id=chat_id,
            response_message_id=message_id,
            vote=callback_data
        )
