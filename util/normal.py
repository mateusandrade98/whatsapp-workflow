from re import sub, findall, compile, UNICODE
from unicodedata import normalize


def normalizeTextMachine(i: str = ""):
    a = str(normalize('NFKD', i).encode('ASCII', 'ignore').decode('ASCII'))
    a = " ".join(filter(str.isalnum, a))
    a = sub(r"[^a-zA-Z0-9]", "", a)
    return a


def normalizeNumbers(i: str = ""):
    return "".join(findall(r"\d+", i))


def normalizaTextNormal(i: str = ""):
    a = str(i).lower()
    a = normalize('NFKD', a).encode('ASCII', 'ignore').decode('ASCII')
    a = sub(r'[^a-zA-Z0-9 ]', r'', a)
    emoji_pattern = compile("["
                               u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F1E0-\U0001F1FF"
                               "]+", flags=UNICODE)
    return emoji_pattern.sub(r'', a)


def TextMSG(i: str = ''):
    a = i.lower().title().rstrip().lstrip()
    emoji_pattern = compile("["
                            u"\U0001F600-\U0001F64F"
                            u"\U0001F300-\U0001F5FF"
                            u"\U0001F680-\U0001F6FF"
                            u"\U0001F1E0-\U0001F1FF"
                            "]+", flags=UNICODE)
    return emoji_pattern.sub(r'', a)


def selectOnlyText(s: str = ""):
    a = normalizeTextMachine(s)
    return "".join(findall("[^0-9]*", a))
