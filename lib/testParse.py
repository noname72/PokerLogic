from HandParse import *
from random import shuffle
from timeit import timeit

def rand_hand():
    cards = CARDS.copy()
    shuffle(cards)
    return [cards.pop() for i in range(7)]


test = lambda: HandParser.get_kicker([HandParser(rand_hand()) for _ in range(10)])
print(timeit(test, number=1000))
    
