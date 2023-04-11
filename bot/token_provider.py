import json
import os

import boto3
from botocore.exceptions import ClientError

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
