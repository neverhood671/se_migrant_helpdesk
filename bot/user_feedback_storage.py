import logging

from botocore.exceptions import ClientError

from dynamo_db_provider import DynamoDb

logger = logging.getLogger(__name__)

USER_FEEDBACKS_TABLE = 'user_feedbacks'


class UserFeedbackStorage:
    def __init__(self):
        self.dynamo_db = DynamoDb()

    def create_table_if_not_exists(self):
        try:
            dynamodb_client = self.dynamo_db.get_client()
            existing_tables = dynamodb_client.list_tables()['TableNames']
            if USER_FEEDBACKS_TABLE not in existing_tables:
                dynamodb_client.create_table(
                    TableName=USER_FEEDBACKS_TABLE,
                    KeySchema=[
                        {'AttributeName': 'session_id', 'KeyType': 'HASH'}, # Partition key
                        {'AttributeName': 'chat_id', 'KeyType': 'RANGE'}, # Sort key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'session_id', 'AttributeType': 'S'},
                        {'AttributeName': 'chat_id', 'AttributeType': 'S'},
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
                table = dynamodb_client.describe_table(TableName=USER_FEEDBACKS_TABLE)
                table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", USER_FEEDBACKS_TABLE,
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err

    def save_feedback(self, chat_id: str, session_id: str, topic_id: str, vote: str):
        try:
            self.dynamo_db.get_client().put_item(
                TableName=USER_FEEDBACKS_TABLE,
                Item={
                    "session_id": {'S': session_id},
                    "chat_id": {'S': str(chat_id)},
                    "topic_id": {'S': topic_id},
                    "vote": {'S': vote}
                }
            )
        except ClientError as err:
            logger.error(
                "Couldn't add new feedback to table %s. "
                "chat_id: %s, session_id: %s, topic_id: %s, "
                "vote: %s "
                "Here's why: %s: %s",
                USER_FEEDBACKS_TABLE,
                chat_id, session_id, topic_id, vote,
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err


USER_FEEDBACK_STORAGE = UserFeedbackStorage()
