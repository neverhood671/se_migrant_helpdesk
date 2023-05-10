import logging
import re
from typing import Optional

import telegram_utils as t_utils
import topics_modelling as model
import yaml
from postnummer_komun_provider import POSTNUMMER_KOMUN_PROVIDER
from user_feedback_storage import USER_FEEDBACK_STORAGE
from user_requests_storage import USER_REQUESTS_STORAGE
from user_session_storage import UserSession

logger = logging.getLogger(__name__)

REPEAT_STATE_ID = 'REPEAT'
HOME_STATE_ID = 'HOME'


def apply_session_params(string: str, session: UserSession):
    if session.session_attributes is not None:
        for k, v in session.session_attributes.items():
            string = string.replace(f'<{k}>', v)
    return string


class AbstractChatNode:
    def __init__(self, node_id: str):
        self.node_id = node_id

    def close_node(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
    ):
        self._close_node(
            user_session,
            message,
            self._normalize_action(message.new_text.strip())
        )

    def _close_node(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            action_text: str
    ):
        return

    def get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction
    ) -> Optional[dict]:
        norm_action = self._normalize_action(message.new_text.strip())
        return self._get_message_data_for_lock_message(
            user_session, norm_action
        )

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        raise NotImplementedError("Please Implement this method")

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        raise NotImplementedError("Please Implement this method")

    def get_next_state(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
    ) -> str:
        norm_action = self._normalize_action(message.new_text.strip())
        if self._is_expected_action(norm_action):
            return self._get_next_state(user_session, message, norm_action)
        else:
            return REPEAT_STATE_ID

    def _is_expected_action(self, action_text: str) -> bool:
        return True

    def _normalize_action(self, action_text: str) -> str:
        return action_text

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        raise NotImplementedError("Please Implement this method")


class StaticTopicNode(AbstractChatNode):
    def __init__(self, node_id: str = 'static_topic'):
        AbstractChatNode.__init__(self, node_id)

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        return None

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        return None

    def _is_expected_action(self, action_text: str) -> bool:
        return True

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        user_session.session_attributes['wellcome_text'] = \
            'Hi! I can provide you with information about the following topics'
        return 'select_topic'


class MakeTopicPredictionNode(AbstractChatNode):
    def __init__(self, node_id: str = 'make_topic_prediction'):
        AbstractChatNode.__init__(self, node_id)

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        return None

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        return None

    def _is_expected_action(self, action_text: str) -> bool:
        return True

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        topic = model.get_topic_for_message(message.new_text)
        user_session.session_attributes['topic'] = topic
        return 'check_topic_prediction'


class SelectTopicNode(AbstractChatNode):
    EXPECTED_ACTIONS = {'swedish', 'bank', 'pn', 'apartment', 'culture'}

    def __init__(self):
        AbstractChatNode.__init__(self, 'check_topic_prediction')

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        response_text = f'{user_session.current_text}\n\nYou selected {action_text}'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': user_session.chat_id,
            'message_id': user_session.current_message_id,
            'reply_markup': {
                'inline_keyboard': [[]]
            }
        }

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        response_text = user_session.session_attributes.get('wellcome_text')
        if response_text is None:
            response_text = 'Choose the option you want to talk about'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': message.chat_id,
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': 'Swedish: SFI', 'callback_data': 'swedish'}],
                    [{'text': 'Bank', 'callback_data': 'bank'}],
                    [{'text': 'Personal number', 'callback_data': 'pn'}],
                    [{'text': 'Apartment', 'callback_data': 'apartment'}],
                    [{'text': 'Culture', 'callback_data': 'culture'}],
                ]
            }
        }

    def _is_expected_action(self, action_text: str) -> bool:
        return action_text in SelectTopicNode.EXPECTED_ACTIONS

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        user_session.session_attributes['topic'] = action_text
        return f'head_topic_{action_text}'


class CheckTopicPredictionNode(AbstractChatNode):
    EXPECTED_ACTIONS = {'good_answer', 'bad_answer'}

    def __init__(self):
        AbstractChatNode.__init__(self, 'check_topic_prediction')

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        if action_text == 'good_answer':
            vote = '👍'
        elif action_text == 'bad_answer':
            vote = '👎'
        else:
            vote = action_text

        response_text = f'{user_session.current_text}\n\nYou voted as {vote}'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': user_session.chat_id,
            'message_id': user_session.current_message_id,
            'reply_markup': {
                'inline_keyboard': [[]]
            }
        }

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        response_text = f'{prefix}{message.first_name}, you want to talk about: {user_session.session_attributes["topic"]}'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': message.chat_id,
            'reply_markup': {
                'inline_keyboard': [[
                    {'text': '👍', 'callback_data': 'good_answer'},
                    {'text': '👎', 'callback_data': 'bad_answer'}
                ]]
            }
        }

    def _normalize_action(self, action_text: str) -> str:
        low_text = action_text.lower()
        if low_text == 'yes':
            return 'good_answer'
        if low_text == 'no':
            return 'bad_answer'

        return super()._normalize_action(action_text)

    def _is_expected_action(self, action_text: str) -> bool:
        return action_text in CheckTopicPredictionNode.EXPECTED_ACTIONS

    def _close_node(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            action_text: str
    ):
        USER_REQUESTS_STORAGE.save_vote(
            chat_id=user_session.chat_id,
            response_message_id=user_session.current_message_id,
            vote=action_text
        )

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        if action_text == 'good_answer':
            return f'head_topic_{user_session.session_attributes["topic"]}'
        else:
            return 'select_topic'


class FeedbackNode(AbstractChatNode):
    EXPECTED_ACTIONS = {'bad_conversation', 'normal_conversation', 'good_conversation'}

    def __init__(self):
        AbstractChatNode.__init__(self, 'feedback')

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        if action_text == 'bad_conversation':
            vote = '🙁'
        elif action_text == 'normal_conversation':
            vote = '😐'
        elif action_text == 'good_conversation':
            vote = '🙂'
        else:
            vote = action_text

        response_text = f'{user_session.current_text}\n\nYou voted as {vote}'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': user_session.chat_id,
            'message_id': user_session.current_message_id,
            'reply_markup': {
                'inline_keyboard': [[]]
            }
        }

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        response_text = f'{prefix}{message.first_name}, how it was?'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': message.chat_id,
            'reply_markup': {
                'inline_keyboard': [[
                    {'text': '🙁', 'callback_data': 'bad_conversation'},
                    {'text': '😐', 'callback_data': 'normal_conversation'},
                    {'text': '🙂', 'callback_data': 'good_conversation'},
                ]]
            }
        }

    def _normalize_action(self, action_text: str) -> str:
        low_text = action_text.lower()
        if low_text == 'good' or low_text == 'perfect':
            return 'good_conversation'
        if low_text == 'ok':
            return 'normal_conversation'
        if low_text == 'terrible' or low_text == 'bad':
            return 'bad_conversation'

        return super()._normalize_action(action_text)

    def _is_expected_action(self, action_text: str) -> bool:
        return action_text in FeedbackNode.EXPECTED_ACTIONS

    def _close_node(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            action_text: str
    ):
        topic = user_session.session_attributes.get('topic')
        if topic is None:
            logger.warning(
                'Topic is None for session %s in chat %s',
                user_session.session_id, message.chat_id
            )
        else:
            USER_FEEDBACK_STORAGE.save_feedback(
                chat_id=message.chat_id,
                session_id=user_session.session_id,
                topic_id=topic,
                vote=action_text
            )

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        return HOME_STATE_ID


class SimpleOptionNode(AbstractChatNode):

    def __init__(self, node_id: str, node_dict: dict):
        AbstractChatNode.__init__(self, node_id)
        self.content = node_dict['content']
        self.exit_node_id = node_dict.get('exit_node_id')
        self.exit_node_content = node_dict.get('exit_node_content')

        self.links: list[list[dict]] = node_dict.get('links')
        if self.links is None:
            self.links: list[list[dict]] = list()

        self.options: list[list[dict]] = node_dict.get('options')
        self.options_by_node = dict()
        if self.options is None:
            self.options: list[list[dict]] = list()
        else:
            for row in self.options:
                for o in row:
                    self.options_by_node[o['content'].lower()] = o['next_node_id']
        if self.exit_node_id is not None:
            self.options_by_node['exit'] = self.exit_node_id

    def _normalize_action(self, action_text: str) -> str:
        next_node = self.options_by_node.get(action_text.lower())
        if next_node is not None:
            return next_node
        else:
            return super()._normalize_action(action_text)

    def _is_expected_action(self, action_text: str) -> bool:
        if len(self.options_by_node) == 0:
            return False
        return action_text in self.options_by_node.values()

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        links = []
        for row in self.links:
            links_row = []
            for l in row:
                links_row.append(
                    {'text': l['content'], 'url': l['url']}
                )
            if len(links_row) > 0:
                links.append(links_row)

        keyboards = []
        for row in self.options:
            keyboard = []
            for o in row:
                keyboard.append(
                    {'text': o['content'], 'callback_data': o['next_node_id']}
                )
            if len(keyboard) > 0:
                keyboards.append(keyboard)
        if self.exit_node_id is not None:
            keyboards.append([{'text': self.exit_node_content, 'callback_data': self.exit_node_id}])

        inline_keyboard = []
        if len(links) > 0:
            inline_keyboard.extend(links)
        if len(keyboards) > 0:
            inline_keyboard.extend(keyboards)
        if len(inline_keyboard) == 0:
            inline_keyboard.append([])

        return {
            'text': apply_session_params(self.content, user_session).encode('utf8'),
            'chat_id': message.chat_id,
            'reply_markup': {
                'inline_keyboard': inline_keyboard
            }
        }

    def _get_message_data_for_lock_message(
            self,
            user_session: UserSession,
            action_text: str
    ) -> Optional[dict]:
        links = []
        for row in self.links:
            links_row = []
            for l in row:
                links_row.append(
                    {'text': l['content'], 'url': l['url']}
                )
            if len(links_row) > 0:
                links.append(links_row)
        if len(links) == 0:
            links.append([])

        response_text = user_session.current_text
        break_out_flag = False
        if self.exit_node_id is not None and action_text != self.exit_node_id:
            for row in self.options:
                for o in row:
                    if action_text == o['next_node_id']:
                        response_text += f'\n\nYour answer: {o["content"]}'
                        break_out_flag = True
                        break
                if break_out_flag:
                    break

        return {
            'text': response_text.encode('utf8'),
            'chat_id': user_session.chat_id,
            'message_id': user_session.current_message_id,
            'reply_markup': {
                'inline_keyboard': links
            }
        }

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        return action_text


class PostnumberKomvuxSearcherNode(AbstractChatNode):

    def __init__(self, node_id: str, node_dict: dict):
        AbstractChatNode.__init__(self, node_id)
        self.content = node_dict['content']
        self.unknown_postnumer_node_id = node_dict['unknown_postnumer_node_id']
        self.komvux_exists_node_id = node_dict['komvux_exists_node_id']
        self.komvux_doesnt_exists_node_id = node_dict['komvux_doesnt_exists_node_id']
        self.exit_node_id = node_dict.get('exit_node_id')
        self.exit_node_content = node_dict.get('exit_node_content')

    def _normalize_action(self, action_text: str) -> str:
        if self.exit_node_id is not None and action_text.lower() == 'exit':
            return self.exit_node_id
        return re.sub(r"\s+", "", action_text)

    def _is_expected_action(self, action_text: str) -> bool:
        if self.exit_node_id is not None and action_text == self.exit_node_id:
            return True
        return bool(re.match(r"^\d{5}$", action_text))

    def _get_message_data_for_lock_message(self, user_session: UserSession, action_text: str) -> Optional[dict]:
        if self.exit_node_id is not None and action_text == self.exit_node_id:
            response_text = user_session.current_text
        else:
            response_text = f'{user_session.current_text}\n\nYour answer: {action_text}'
        return {
            'text': response_text.encode('utf8'),
            'chat_id': user_session.chat_id,
            'message_id': user_session.current_message_id,
            'reply_markup': {
                'inline_keyboard': [[]]
            }
        }

    def get_message_data(
            self,
            user_session: UserSession,
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        keyboard = []
        if self.exit_node_id is not None:
            keyboard.append({'text': self.exit_node_content, 'callback_data': self.exit_node_id})

        return {
            'text': apply_session_params(self.content, user_session).encode('utf8'),
            'chat_id': message.chat_id,
            'reply_markup': {
                'inline_keyboard': [keyboard]
            }
        }

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        if self.exit_node_id is not None and action_text == self.exit_node_id:
            return self.exit_node_id

        user_session.session_attributes["postnumer"] = action_text
        kommun = POSTNUMMER_KOMUN_PROVIDER.get_kommun_info_by_number(action_text)
        if kommun is None:
            return self.unknown_postnumer_node_id
        elif kommun.vuxenutbildningar_link is None:
            user_session.session_attributes["kommun_name"] = kommun.name
            user_session.session_attributes["kommun_link"] = kommun.kommun_link
            return self.komvux_doesnt_exists_node_id
        else:
            user_session.session_attributes["kommun_name"] = kommun.name
            user_session.session_attributes["kommun_link"] = kommun.kommun_link
            user_session.session_attributes["komvux_link"] = kommun.vuxenutbildningar_link
            return self.komvux_exists_node_id


ALL_STATES = {}


def load_base_states():
    global ALL_STATES
    ALL_STATES['make_topic_prediction'] = MakeTopicPredictionNode()
    ALL_STATES['check_topic_prediction'] = CheckTopicPredictionNode()
    ALL_STATES['static_topic'] = StaticTopicNode()
    ALL_STATES['select_topic'] = SelectTopicNode()
    ALL_STATES['feedback'] = FeedbackNode()


def load_pipeline(file_name: str):
    global ALL_STATES
    with open(file_name, "r") as f:
        data = yaml.safe_load(f)
        for k, v in data.items():
            if v['node_type'] == 'SimpleOptionNode':
                ALL_STATES[k] = SimpleOptionNode(node_id=k, node_dict=v)
            elif v['node_type'] == 'PostnumberKomvuxSearcherNode':
                ALL_STATES[k] = PostnumberKomvuxSearcherNode(node_id=k, node_dict=v)
            else:
                raise Exception(f'Undefined node_type: {v["node_type"]}')


def get_state(state_id: str) -> AbstractChatNode:
    return ALL_STATES[state_id]


load_base_states()
load_pipeline('bot_appartment_pipeline.yml')
load_pipeline('bot_bank_pipeline.yml')
load_pipeline('bot_culture_pipeline.yml')
load_pipeline('bot_pn_pipeline.yml')
load_pipeline('bot_swedish_pipeline.yml')
