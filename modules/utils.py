import re

strings = re.compile('[^a-zA-Z]')


def preprocess_text(text):
    t = re.sub(strings, ' ', text)
    tokens = [t.rstrip().lstrip() for t in t.split()]
    tokens = [t.lower() for t in tokens if len(t) > 0]
    text = ' '.join(tokens)
    return text
