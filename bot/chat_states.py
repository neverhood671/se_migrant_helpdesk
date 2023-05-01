from typing import Optional

import telegram_utils as t_utils
import topics_modelling as model
from user_requests_storage import UserRequestsStorage
from user_session_storage import UserSession

REPEAT_STATE_ID = 'REPEAT'
HOME_STATE_ID = 'HOME'

user_requests_storage = UserRequestsStorage()


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
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        raise NotImplementedError("Please Implement this method")

    def get_next_state(
            self,
            user_session: Optional[UserSession],
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
        return f'check_topic_prediction_{topic}'


class CheckTopicPredictionNode(AbstractChatNode):
    EXPECTED_ACTIONS = {'good_answer', 'bad_answer'}

    def __init__(self, node_id: str, topic: str):
        AbstractChatNode.__init__(self, node_id)
        self.topic = topic

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
            message: t_utils.MessageAction,
            prefix: str = ""
    ) -> Optional[dict]:
        response_text = f'{prefix}{message.first_name}, you want to talk about: {self.topic}'
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
        user_requests_storage.save_vote(
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
        return f'head_topic_{self.topic}'


class FeedbackNode(AbstractChatNode):
    EXPECTED_ACTIONS = {'bad_conversation', 'normal_conversation', 'good_conversation'}

    def __init__(self, node_id: str = 'feedback'):
        AbstractChatNode.__init__(self, node_id)

    def get_message_data(
            self,
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
        # TODO:save user_session_result
        return

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

    def _get_next_state(
            self,
            user_session: Optional[UserSession],
            message: t_utils.MessageAction,
            action_text: str
    ) -> str:
        return HOME_STATE_ID


def load_base_states():
    return {
        'make_topic_prediction': MakeTopicPredictionNode(),
        # check topic predictions
        'check_topic_prediction_swedish': CheckTopicPredictionNode('check_topic_prediction_swedish', 'swedish'),
        'check_topic_prediction_bank': CheckTopicPredictionNode('check_topic_prediction_bank', 'bank'),
        'check_topic_prediction_pn': CheckTopicPredictionNode('check_topic_prediction_pn', 'pn'),
        'check_topic_prediction_apartment': CheckTopicPredictionNode('check_topic_prediction_apartment', 'apartment'),
        'check_topic_prediction_culture': CheckTopicPredictionNode('check_topic_prediction_culture', 'culture'),
        #
        'head_topic_swedish': FeedbackNode('head_topic_swedish'),
        'head_topic_bank': FeedbackNode('head_topic_bank'),
        'head_topic_pn': FeedbackNode('head_topic_pn'),
        'head_topic_apartment': FeedbackNode('head_topic_apartment'),
        'head_topic_culture': FeedbackNode('head_topic_culture'),
    }


ALL_STATES = load_base_states()


def get_state(state_id: str) -> AbstractChatNode:
    return ALL_STATES[state_id]
