from sys import path
from pathlib import Path
path.append(str(Path().cwd().parent))
from random import sample
from timeit import timeit
from pokerlib.handparser import *
from pokerlib.enums import Value, Suit

SUITS = ['♠', '♣', '♦', '♥']
CARDS = [[val, suit] for val in Value for suit in Suit]

def randomHandTests():
    while True:
        hand = HandParser(sample(CARDS, 7))
        hand.parse()
        print(', '.join([str(int(val)) + SUITS[suit]
                         for val, suit in hand.cards]))
        print(hand.handenum)
        print(hand.handbase)
        input()

def timeParser(n):
    a = timeit(lambda: HandParser(sample(CARDS, 7)).parse(),
               number=n)
    b = timeit(lambda: sample(CARDS, 7), number=n)
    print(a - b)
    
if __name__ == '__main__':
    timeParser(10**5)
