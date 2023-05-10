import json
import logging

import chat_states
import telegram_utils as t_utils
from user_feedback_storage import USER_FEEDBACK_STORAGE
from user_requests_storage import USER_REQUESTS_STORAGE
from user_session_storage import USER_SESSION_STORAGE, UserSession

logger = logging.getLogger(__name__)

SYSTEM_MESSAGES = {'/help', '/start', '/reset'}
# INIT_STATE_ID = 'make_topic_prediction'
INIT_STATE_ID = 'static_topic'


def lambda_handler(event, context):
    try:
        if 'message' in event:
            tg_message = process_message(event)
        elif 'callback_query' in event:
            tg_message = process_callback(event)
        else:
            raise Exception(f'Undefined request type. event: {json.dumps(event)}')

        update_user_state(tg_message)
    except Exception as error:
        logger.error('Something goes wrong. Event: %s, Error: %s', {json.dumps(event)}, error, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps('Something goes wrong')
        }

    return {'statusCode': 200}


def process_message(event) -> t_utils.MessageAction:
    message = event['message']
    text = message['text']
    message_id = message['message_id']
    chat_id = message['chat']['id']
    first_name = message['chat']['first_name']

    return t_utils.MessageAction(
        action_type="message",
        chat_id=chat_id,
        first_name=first_name,
        new_message_id=message_id,
        new_text=text
    )


def process_callback(event):
    callback_query = event['callback_query']
    callback_data = callback_query['data']
    message = callback_query['message']
    first_name = message['chat']['first_name']
    chat_id = message['chat']['id']

    return t_utils.MessageAction(
        action_type="callback",
        chat_id=chat_id,
        first_name=first_name,
        new_text=callback_data
    )


def update_user_state(tg_message: t_utils.MessageAction):
    user_session = USER_SESSION_STORAGE.get_session(str(tg_message.chat_id))
    if user_session is None:
        if tg_message.new_text in SYSTEM_MESSAGES:
            process_system_message(tg_message)
        else:
            start_new_session(tg_message)
    else:
        do_for_session(tg_message, user_session)


def process_system_message(tg_message: t_utils.MessageAction):
    if tg_message.new_text == '/reset':
        user_session = USER_SESSION_STORAGE.get_session(str(tg_message.chat_id))
        if user_session is not None:
            USER_SESSION_STORAGE.delete_session(user_session)


def start_new_session(tg_message: t_utils.MessageAction):
    make_topic_prediction_node = chat_states.get_state(INIT_STATE_ID)

    new_user_session = USER_SESSION_STORAGE.create_new_session(
        chat_id=str(tg_message.chat_id),
        state_id=INIT_STATE_ID,
        current_message_id=None,
        current_text=tg_message.new_text
    )

    topic_node_id = make_topic_prediction_node.get_next_state(user_session=new_user_session, message=tg_message)
    topic_node = chat_states.get_state(topic_node_id)
    data = topic_node.get_message_data(user_session=new_user_session, message=tg_message)
    if data is None:
        raise Exception(f'Empty data for topic node {topic_node_id}')

    response = t_utils.send_new_message(data)

    if response.status_code >= 300:
        print(f'Response status code: {response.status_code}')
        print(f'Response content: {response.content}')
    else:
        response_content = json.loads(response.content)
        new_user_session.state_id = topic_node_id
        new_user_session.current_message_id = response_content['result']['message_id']
        new_user_session.current_text = response_content['result']['text']
        USER_SESSION_STORAGE.save_new_session(new_user_session)


def do_for_session(tg_message: t_utils.MessageAction, user_session: UserSession):
    current_node = chat_states.get_state(user_session.state_id)
    next_state_id = current_node.get_next_state(user_session, tg_message)

    if chat_states.REPEAT_STATE_ID == next_state_id:
        repeat(tg_message, user_session, current_node)
    elif chat_states.HOME_STATE_ID == next_state_id:
        go_home(tg_message, user_session, current_node)
    else:
        update_session(tg_message, user_session, current_node, next_state_id)


def repeat(
        tg_message: t_utils.MessageAction,
        user_session: UserSession,
        current_node: chat_states.AbstractChatNode
):
    repeat_text = f'Sorry, I don\'t recognized your answer. could you repeat?\n\n'
    data = current_node.get_message_data(
        user_session=user_session,
        message=tg_message,
        prefix=repeat_text
    )
    response = t_utils.send_new_message(data)

    if response.status_code >= 300:
        print(f'Response status code: {response.status_code}')
        print(f'Response content: {response.content}')
    else:
        data = {
            'text': user_session.current_text.encode('utf8'),
            'chat_id': user_session.chat_id,
            'message_id': user_session.current_message_id,
            'reply_markup': {
                'inline_keyboard': [[]]
            }
        }
        t_utils.update_message(data)

        response_content = json.loads(response.content)
        user_session.current_message_id = response_content['result']['message_id']
        user_session.current_text = response_content['result']['text']
        USER_SESSION_STORAGE.update_user_session(user_session)


def update_session(
        tg_message: t_utils.MessageAction,
        user_session: UserSession,
        current_node: chat_states.AbstractChatNode,
        next_state_id: str
):
    next_node = chat_states.get_state(next_state_id)
    data = next_node.get_message_data(
        user_session=user_session,
        message=tg_message,
    )
    response = t_utils.send_new_message(data)

    if response.status_code >= 300:
        print(f'Response status code: {response.status_code}')
        print(f'Response content: {response.content}')
    else:
        current_node.close_node(user_session, tg_message)
        data = current_node.get_message_data_for_lock_message(user_session, tg_message)
        if data is not None:
            t_utils.update_message(data)

        response_content = json.loads(response.content)
        user_session.state_id = next_state_id
        user_session.current_message_id = response_content['result']['message_id']
        user_session.current_text = response_content['result']['text']
        USER_SESSION_STORAGE.update_user_session(user_session)


def go_home(
        tg_message: t_utils.MessageAction,
        user_session: UserSession,
        current_node: chat_states.AbstractChatNode
):
    current_node.close_node(user_session, tg_message)
    data = current_node.get_message_data_for_lock_message(user_session, tg_message)
    if data is not None:
        t_utils.update_message(data)
    USER_SESSION_STORAGE.delete_session(user_session)


USER_SESSION_STORAGE.create_table_if_not_exists()
USER_FEEDBACK_STORAGE.create_table_if_not_exists()
USER_REQUESTS_STORAGE.create_table_if_not_exists()
