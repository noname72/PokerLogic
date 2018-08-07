from os import listdir


for elt in listdir()[:-1]:
    with open(elt, 'w') as raw:
        print('1000', file=raw)
