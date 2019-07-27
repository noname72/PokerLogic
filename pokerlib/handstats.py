from timeit import timeit
#try: from numpy.random import shuffle
#except ModuleNotFoundError:
from random import shuffle
from pokerlib.handparse import HandParser

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
            parsed_hand.analyse()
            for _ in range(nforeign):
                foreign_hand = [next(deckit) for _ in range(2)] + mutualc
                foreign_hand = HandParser(foreign_hand)
                foreign_hand.analyse()
                if foreign_hand > parsed_hand: break
            else: p += 1
            
        return p / nsim

if __name__ == '__main__':
    deck = [[i, j]  for j in range(4) for i in range(13)]
    nforeign, nsim = 5, 10**4
    hand = [[7, 0], [8, 0]]
    model = StatisticModel(hand)
    print(model.simulate(nforeign, nsim))
