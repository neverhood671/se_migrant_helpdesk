import logging
import os

import boto3
from botocore.client import BaseClient

logger = logging.getLogger(__name__)
DYNAMODB_REGION_NAME = os.getenv('DYNAMODB_REGION_NAME', 'eu-north-1')


class DynamoDb:
    def __init__(self):
        try:
            session = boto3.session.Session()
        except Exception as error:
            logging.error('Error: cannot create service session: %s', error)
            raise error

        try:
            self.client = session.client('dynamodb', region_name=DYNAMODB_REGION_NAME)
        except Exception as error:
            logging.error('Cannot connect to %s in %s:%s', 'dynamodb', DYNAMODB_REGION_NAME, error)
            raise error

    def get_client(self) -> BaseClient:
        return self.client
