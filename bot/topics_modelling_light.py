from random import randint


def get_topic_for_message(message: str) -> str:
    category = randint(0, 4)

    if category == 0:
        return 'swedish'
    elif category == 1:
        return 'bank'
    elif category == 2:
        return 'pn'
    elif category == 3:
        return 'apartment'
    elif category == 4:
        return 'culture'

    raise Exception(f'Undefined category "{category}" for message "{message}"')
