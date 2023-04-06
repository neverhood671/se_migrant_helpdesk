import json
import os
import traceback
import boto3
import requests
from botocore.exceptions import ClientError

BASE_URL = 'https://api.telegram.org/bot{}'
SEND_MESSAGE_URL = BASE_URL + '/sendMessage'
SECRET_REGION_NAME = os.getenv('SECRET_REGION_NAME', 'eu-north-1')

telegram_token = None


def get_telegram_token():
    global telegram_token

    if not telegram_token:
        telegram_token = request_telegram_token()

    return telegram_token


def request_telegram_token():
    secret_name = 'prod/se_migrant_help_bot'

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=SECRET_REGION_NAME
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = json.loads(get_secret_value_response['SecretString'])['se-migrant-help-bot-token']

    return secret


def send_message(first_name, message, chat_id, token):
    response_text = f'{first_name}, you said: {message}'
    data = {
        'text': response_text.encode('utf8'),
        'chat_id': chat_id
    }
    url = SEND_MESSAGE_URL.format(token)
    response = requests.post(url, json=data)
    if response.status_code >= 300:
        print(f'Response status code: {response.status_code}')
        print(f'Response content: {response.content}')


def lambda_handler(event, context):
    try:
        message = event['message']
        text = message['text']
        chat_id = message['chat']['id']
        first_name = message['chat']['first_name']

        send_message(first_name, text, chat_id, get_telegram_token())
    except Exception:
        print('Something goes wrong')
        print(traceback.format_exc())
        print(f'event: {json.dumps(event)}')
        return {
            'statusCode': 500,
            'body': json.dumps('Something goes wrong')
        }

    return {'statusCode': 200}
