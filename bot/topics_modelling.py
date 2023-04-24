def get_topic_for_message(message: str) -> str:
    if 'elephant' in message.lower():
        return 'Elephants'
    return 'Sweden'
