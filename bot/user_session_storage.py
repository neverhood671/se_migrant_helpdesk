import logging
import uuid
from typing import Optional

from botocore.exceptions import ClientError

from dynamo_db_provider import DynamoDb

logger = logging.getLogger(__name__)

USER_SESSION_TABLE = 'user_sessions'


class UserSession:
    def __init__(
            self,
            chat_id: str,
            state_id: str,
            current_message_id: int,
            current_text: str,
            session_id: str = None,
            session_attributes: dict = None,
    ):
        if session_id is None:
            session_id = str(uuid.uuid4())
        if session_attributes is None:
            session_attributes = dict()

        self.chat_id = chat_id
        self.session_id = session_id
        self.state_id = state_id
        self.current_message_id = current_message_id
        self.current_text = current_text
        self.session_attributes = session_attributes

    def get_update_attribute_values(self):
        return {
            ':session_id': {'S': self.session_id},
            ':state_id': {'S': self.state_id},
            ':current_message_id': {'N': str(self.current_message_id)},
            ':current_text': {'S': self.current_text},
            ':session_attributes': {'M': self.__attributes_to_ddb_map()},
        }

    def to_item(self):
        return {
            'chat_id': {'S': self.chat_id},
            'session_id': {'S': self.session_id},
            'state_id': {'S': self.state_id},
            'current_message_id': {'N': str(self.current_message_id)},
            'current_text': {'S': self.current_text},
            'session_attributes': {'M': self.__attributes_to_ddb_map()},
        }

    def __attributes_to_ddb_map(self):
        attributes = dict()
        for k, v in self.session_attributes.items():
            attributes[k] = {'S': v}
        return attributes

    def get_key_item(self):
        return {'chat_id': {'S': self.chat_id}}

    def get_session_attribute_values(self):
        return {':session_id': {'S': self.session_id}}


class UserSessionStorage:
    def __init__(self):
        self.dynamo_db = DynamoDb()

    def create_table_if_not_exists(self):
        try:
            dynamodb_client = self.dynamo_db.get_client()
            existing_tables = dynamodb_client.list_tables()['TableNames']
            if USER_SESSION_TABLE not in existing_tables:
                dynamodb_client.create_table(
                    TableName=USER_SESSION_TABLE,
                    KeySchema=[
                        {'AttributeName': 'chat_id', 'KeyType': 'HASH'},  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'chat_id', 'AttributeType': 'S'},
                    ],
                    ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
                table = dynamodb_client.describe_table(TableName=USER_SESSION_TABLE)
                table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", USER_SESSION_TABLE,
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err

    def get_session(self, chat_id: str) -> Optional[UserSession]:
        try:
            response = self.dynamo_db.get_client().get_item(
                TableName=USER_SESSION_TABLE,
                Key={
                    'chat_id': {'S': chat_id}
                }
            )
            data = response.get('Item')
            if data is None:
                return None
            session_attributes = dict()
            for k, v in data.get('session_attributes')['M'].items():
                session_attributes[k] = v['S']
            return UserSession(
                chat_id=chat_id,
                session_id=data.get('session_id')['S'],
                state_id=data.get('state_id')['S'],
                current_message_id=int(data.get('current_message_id')['N']),
                current_text=data.get('current_text')['S'],
                session_attributes=session_attributes,
            )
        except ClientError as err:
            logger.error(
                "Couldn't get user session to table %s. "
                "chat_id: %s. "
                "Here's why: %s: %s",
                USER_SESSION_TABLE,
                chat_id,
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err

    def create_new_session(
            self,
            chat_id: str,
            state_id: str,
            current_message_id: Optional[int] = None,
            current_text: str = ''
    ):
        return UserSession(
            chat_id=chat_id,
            state_id=state_id,
            current_message_id=current_message_id,
            current_text=current_text,
        )

    def save_new_session(self, new_session: UserSession):
        if new_session.current_message_id is None:
            raise Exception('Message id is None for new session')
        if new_session.current_text == '':
            raise Exception('Message text is empty for new session')
        try:
            self.dynamo_db.get_client().put_item(
                TableName=USER_SESSION_TABLE,
                Item=new_session.to_item()
            )
        except ClientError as err:
            logger.error(
                "Couldn't add new user session to table %s. "
                "chat_id: %s. "
                "Here's why: %s: %s",
                USER_SESSION_TABLE,
                new_session.chat_id,
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err

    def update_user_session(self, user_session: UserSession):
        try:
            self.dynamo_db.get_client().update_item(
                TableName=USER_SESSION_TABLE,
                Key=user_session.get_key_item(),
                UpdateExpression="SET session_id = :session_id"
                                 ", state_id = :state_id"
                                 ", current_message_id = :current_message_id"
                                 ", current_text = :current_text"
                                 ", session_attributes = :session_attributes",
                ExpressionAttributeValues=user_session.get_update_attribute_values(),
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as err:
            logger.error(
                "Couldn't update user session %s in table %s. chat_id: %s. "
                "Here's why: %s: %s",
                user_session.session_id, USER_SESSION_TABLE,
                str(user_session.chat_id),
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err

    def delete_session(self, user_session: UserSession):
        try:
            self.dynamo_db.get_client().delete_item(
                TableName=USER_SESSION_TABLE,
                Key=user_session.get_key_item(),
                ConditionExpression='session_id = :session_id',
                ExpressionAttributeValues=user_session.get_session_attribute_values(),
            )
        except ClientError as err:
            logger.error(
                "Couldn't delete user session %s in table %s. chat_id: %s. "
                "Here's why: %s: %s",
                user_session.session_id, USER_SESSION_TABLE,
                str(user_session.chat_id),
                err.response['Error']['Code'], err.response['Error']['Message'],
                exc_info=True
            )
            raise err


USER_SESSION_STORAGE = UserSessionStorage()
