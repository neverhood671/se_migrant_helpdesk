import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
DYNAMODB_REGION_NAME = os.getenv('DYNAMODB_REGION_NAME', 'eu-north-1')
USER_REQUESTS_TABLE = 'user_requests'


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

        self.__create_table_if_not_exists()

    def __create_table_if_not_exists(self):
        try:
            existing_tables = self.client.list_tables()['TableNames']
            if USER_REQUESTS_TABLE not in existing_tables:
                self.client.create_table(
                    TableName=USER_REQUESTS_TABLE,
                    KeySchema=[
                        {'AttributeName': 'chat_id', 'KeyType': 'HASH'},  # Partition key
                        {'AttributeName': 'response_message_id', 'KeyType': 'RANGE'}  # Sort key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'chat_id', 'AttributeType': 'S'},
                        {'AttributeName': 'response_message_id', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
                self.table = self.client.Table(USER_REQUESTS_TABLE)
                table = self.client.describe_table(TableName=USER_REQUESTS_TABLE)
                table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", USER_REQUESTS_TABLE,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise err

    def save_question(self, chat_id, question_message_id, question, response_message_id, answer):
        try:
            self.client.put_item(
                TableName=USER_REQUESTS_TABLE,
                Item={
                    "chat_id": {'S': str(chat_id)},
                    "question_message_id": {'S': str(question_message_id)},
                    "question": {'S': question},
                    "response_message_id": {'S': str(response_message_id)},
                    "answer": {'S': answer}
                }
            )
        except ClientError as err:
            logger.error(
                "Couldn't add new request to table %s. "
                "chat_id: %s, question_message_id: %s, question: %s, "
                "response_message_id: %s, answer: %s "
                "Here's why: %s: %s",
                USER_REQUESTS_TABLE,
                chat_id, question_message_id, question, response_message_id, answer,
                err.response['Error']['Code'], err.response['Error']['Message']
            )
            raise err

    def save_vote(self, chat_id, response_message_id, vote):
        try:
            self.client.update_item(
                TableName=USER_REQUESTS_TABLE,
                Key={'chat_id': {'S': str(chat_id)}, 'response_message_id': {'S': str(response_message_id)}},
                UpdateExpression="SET vote = :val",
                ExpressionAttributeValues={':val': {'S': vote}},
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as err:
            logger.error(
                "Couldn't add vote %s in table %s. chat_id: %s, response_message_id: %s "
                "Here's why: %s: %s",
                vote, USER_REQUESTS_TABLE,
                str(chat_id), str(response_message_id),
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise err
