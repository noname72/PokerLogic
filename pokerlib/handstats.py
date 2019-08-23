from timeit import timeit
#try: from numpy.random import shuffle
#except ModuleNotFoundError:
from pathlib import Path
from sys import path
path.append(str(Path().cwd().parent))
from random import shuffle, sample
from pokerlib.handparser import HandParser

class StatisticModel:
    __slots__ = ['hand', 'table']
    __deck = [[i, j] for j in range(4) for i in range(13)]

    def __init__(self, hand, table=[]):
        self.hand = hand
        self.table = table

    def simulate(self, nforeign, nsim):
        deck = self.__deck.copy()
        for card in self.hand + self.table: deck.remove(card)

        p = 0
        n_table = 5 - len(self.table)
        for _ in range(nsim):
            shuffle(deck)
            deckit = iter(deck)
            mutualc = self.table + [next(deckit) for _ in range(n_table)]
            parsed_hand = HandParser(self.hand + mutualc)
            parsed_hand.parse()
            for _ in range(nforeign):
                foreign_hand = [next(deckit) for _ in range(2)] + mutualc
                foreign_hand = HandParser(foreign_hand)
                foreign_hand.parse()
                if foreign_hand > parsed_hand: break
            else: p += 1

        return p / nsim

if __name__ == '__main__':
    deck = [[i, j]  for j in range(4) for i in range(13)]
    nforeign, nsim = 5, 10**3
    hand = [[12, 0], [12, 1]]
    model = StatisticModel(hand)
    print(timeit(lambda: print(model.simulate(nforeign, nsim)), number=1))
