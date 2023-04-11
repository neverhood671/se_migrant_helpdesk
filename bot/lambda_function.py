import json
import traceback

import telegram_utils as t_utils


def lambda_handler(event, context):
    try:
        if 'message' in event:
            process_message(event)
        elif 'callback_query' in event:
            process_callback(event)
        else:
            print(f'WARN Undefined request type. event: {json.dumps(event)}')
    except Exception:
        print('Something goes wrong')
        print(traceback.format_exc())
        print(f'event: {json.dumps(event)}')
        return {
            'statusCode': 500,
            'body': json.dumps('Something goes wrong')
        }

    return {'statusCode': 200}


def process_message(event):
    message = event['message']
    text = message['text']
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


def process_callback(event):
    callback_query = event['callback_query']
    data = callback_query['data']
    message = callback_query['message']
    message_id = message['message_id']
    text = message['text']
    chat_id = message['chat']['id']
    first_name = message['chat']['first_name']

    if data == 'good_answer':
        vote = '👍'
    elif data == 'bad_answer':
        vote = '👎'
    else:
        print(f'ERROR Unknown data: {data}')
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
