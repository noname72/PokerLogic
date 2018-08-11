from os import listdir
from json import dumps, load

original = {'money': 1000}


for elt in listdir():
    if '.py' in elt:
        continue
    with open(elt, 'r', encoding='UTF-8') as raw:
        a = load(raw)
        print(a)
