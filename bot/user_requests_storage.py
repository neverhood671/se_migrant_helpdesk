import logging

from botocore.exceptions import ClientError

from dynamo_db_provider import DynamoDb

logger = logging.getLogger(__name__)

USER_REQUESTS_TABLE = 'user_requests'


class UserRequestsStorage:
    def __init__(self):
        self.__create_table_if_not_exists()

    @staticmethod
    def __create_table_if_not_exists():
        try:
            dynamo_db = DynamoDb()
            dynamodb_client = dynamo_db.get_client()
            existing_tables = dynamodb_client.list_tables()['TableNames']
            if USER_REQUESTS_TABLE not in existing_tables:
                dynamodb_client.create_table(
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
                table = dynamodb_client.describe_table(TableName=USER_REQUESTS_TABLE)
                table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", USER_REQUESTS_TABLE,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise err

    def save_question(self, chat_id, question_message_id, question, response_message_id, answer):
        try:
            DynamoDb().get_client().put_item(
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
            DynamoDb().get_client().update_item(
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
