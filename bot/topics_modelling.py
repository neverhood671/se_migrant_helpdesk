import pickle
import zipfile

with zipfile.ZipFile('model.zip') as zip_model:
    KMEANS = pickle.loads(zip_model.read('model_kmeans'))
    VECTORIZER = pickle.loads(zip_model.read('model_vectorizer'))

if KMEANS is None or VECTORIZER is None:
    raise Exception("Can't load the model")


def get_topic_for_message(message: str) -> str:
    test_vec = VECTORIZER.transform([message])
    category = KMEANS.predict(test_vec)

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
