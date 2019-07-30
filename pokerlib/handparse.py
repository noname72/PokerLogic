from bisect import insort
from pokerlib.enums import Hand, Value, Suit

class HandParser:
    __slots__ = ["original", "ncards", "cards",
                 "__valnums", "__suitnums",
                 "__flushsuit", "__straightstart",
                 "handenum", "handbase", "kickers"]

    def __init__(self, cards: list):
        self.original = cards
        self.ncards = len(cards)
        self.cards = sorted(cards, key = lambda x: x[0])

        self.__valnums = [0] * 13
        self.__suitnums = [0] * 4
        for value, suit in cards:
            self.__valnums[value] += 1
            self.__suitnums[suit] += 1

        self.__flushsuit = None
        for suit in Suit:
            if self.__suitnums[suit] >= 5:
                self.__flushsuit = suit
                break

        self.__straightstart = self.checkStraight(self.__valnums)

        self.kickers = []
        self.handenum = None
        self.handbase = []

    def idx2cards(self, full=True):
        if full is True: return map(
            lambda i: self.cards[i],
            self.handbase + self.kickers)
        elif full is False: return map(
            lambda i: self.cards[i],
            self.handbase)
        elif full == 'k': return map(
            lambda i: self.cards[i],
            self.kickers)

    def __str__(self):
        return str(self.cards)

    def __repr__(self):
        return f"HandParser({self.cards})"

    def __eq__(self, other):
        if self.handenum != other.handenum: return False
        for (s_val, _), (o_val, _) in zip(self.idx2cards(),
                                          other.idx2cards()):
            if s_val != o_val: return False
        return True

    def __gt__(self, other):
        if self.handenum != other.handenum:
            return self.handenum > other.handenum
        for (s_val, _), (o_val, _) in zip(self.idx2cards(),
                                          other.idx2cards()):
            if s_val != o_val: return s_val > o_val
        return False

    def __lt__(self, other):
        return other > self

    def addCards(self, cards):
        self.original.extend(cards)
        self.ncards += len(cards)
        map(lambda card: insort(self.cards, card), cards)

        for value, suit in cards:
            self.__valnums[value] += 1
            self.__suitnums[suit] += 1

        for suit in Suit:
            if self.__suitnums[suit] >= 5:
                self.__flushsuit = suit
                break

        self.__straightstart = self.checkStraight(self.__valnums)

    @staticmethod
    def checkStraight(valnums):
        straightcounter = 1
        for i in reversed(range(len(valnums))):
            if valnums[i-1] and valnums[i]:
                straightcounter += 1
                if straightcounter == 5:
                    return i - 1
            else: straightcounter = 1

    @staticmethod
    def getStraightFrom(cards, straightstart):
        instraight, idxs = [False] * 13, []
        for i in range(straightstart, straightstart + 5):
            instraight[i] = True
        for i, (value, _) in enumerate(cards):
            if instraight[value]:
                idxs.append(i)
                instraight[value] = False
        return idxs

    def setStraightFlush(self):
        permut = [0] * len(self.cards)
        suited_cards, suited_vals = [], [0] * 13
        for i, (val, suit) in enumerate(self.cards):
             if suit == self.__flushsuit:
                 permut[len(suited_cards)] = i
                 suited_vals[val] += 1
                 suited_cards.append([val, suit])

        stflstart = self.checkStraight(suited_vals)
        if stflstart is not None:
            suited_handbase = self.getStraightFrom(suited_cards, stflstart)
            self.handbase = [permut[i] for i in suited_handbase]
            return True
        return False

    def setFourOfAKind(self):
        vals = [val for val in Value if self.__valnums[val] == 4]
        self.handbase = [i for i in reversed(range(self.ncards))
                         if self.cards[i][0] == vals[0]]

    def setFullHouse(self):
        self.handbase.clear()
        threes, twos = [], []
        for val, num in enumerate(self.__valnums):
            if num == 3: threes.append(val)
            elif num == 2: twos.append(val)

        maxvals = [threes.pop(), max(threes + twos)]
        i = self.ncards - 1
        while len(self.handbase) < 5:
            if self.cards[i][0] in maxvals:
                self.handbase.append(i)
            i -= 1

    def setFlush(self):
        self.handbase.clear()
        counter = 0
        for i in reversed(range(self.ncards)):
            if self.cards[i][1] == self.__flushsuit:
                self.handbase.append(i)
                counter += 1
            if counter == 5: break

    def setStraight(self):
        self.handbase = self.getStraightFrom(self.cards, self.__straightstart)

    def setThreeOfAKind(self):
        threeval = [i for i in Value if self.__valnums[i] == 3][0]
        self.handbase = [i for i in reversed(range(self.ncards))
                         if self.cards[i][0] == threeval]

    def setTwoPair(self):
        self.handbase.clear()
        vals = [val for val in Value if self.__valnums[val] == 2]
        i = self.ncards - 1
        while len(self.handbase) < 4:
            if any([self.cards[i][0] == val for val in vals]):
                self.handbase.append(i)
            i -= 1

    def setOnePair(self):
        self.handbase.clear()
        pairval = [val for val in Value if self.__valnums[val] == 2][0]
        self.handbase = [i for i in reversed(range(self.ncards))
                         if self.cards[i][0] == pairval]

    def setHighCard(self):
        self.handbase.clear()
        self.handbase.append(self.ncards - 1)

    def parse(self):
        pairnums = [0] * 5
        for num in self.__valnums: pairnums[num] += 1

        # straight flush
        if None not in [self.__straightstart, self.__flushsuit]:
            if self.setStraightFlush():
                self.handenum = Hand.STRAIGHTFLUSH

        # four of a kind
        if pairnums[4]:
            self.handenum = Hand.FOUROFAKIND
            self.setFourOfAKind()

        # full house
        elif pairnums[3] == 2 or pairnums[3] == 1 and pairnums[2] >= 1:
            self.handenum = Hand.FULLHOUSE
            self.setFullHouse()

        # flush
        elif self.__flushsuit is not None:
            self.handenum = Hand.FLUSH
            self.setFlush()

        # straight
        elif self.__straightstart is not None:
            self.handenum = Hand.STRAIGHT
            self.setStraight()

        # three of a kind
        elif pairnums[3]:
            self.handenum = Hand.THREEOFAKIND
            self.setThreeOfAKind()

        # two pair
        elif pairnums[2] >= 2:
            self.handenum = Hand.TWOPAIR
            self.setTwoPair()

        # one pair
        elif pairnums[2] == 1:
            self.handenum = Hand.ONEPAIR
            self.setOnePair()

        # high card
        else:
            self.handenum = Hand.HIGHCARD
            self.setHighCard()

    def getKickers(self):
        self.kickers.clear()
        inhand = [False] * self.ncards
        for i in self.handbase: inhand[i] = True
        i = len(self.cards) - 1
        while len(self.kickers) < 5 - len(self.handbase) and i > 0:
            if not inhand[i]: self.kickers.append(i)
            i -= 1

    @classmethod
    def getGroupKickers(cls, hands: list):
        winner = max(hands)
        losers = [hand for hand in hands if hand < winner]
        if not losers: return # everyone in hands is split evenly
        max_loser = max(losers)

        # if winner won by a hand level there is no kicker
        if winner.handenum > max_loser.handenum: return
        winner_best_vals = [val for val, _ in winner.idx2cards(False)]
        winner_kicker_vals = [val for val, _ in winner.idx2cards('k')]
        loser_best_vals = [val for val, _ in max_loser.idx2cards(False)]
        loser_kicker_vals = [val for val, _ in max_loser.idx2cards('k')]

        # the hands represented by five hands do not have kickers
        if winner.handenum not in [Hand.STRAIGHT, Hand.FLUSH,
                                   Hand.FULLHOUSE, Hand.STRAIGHTFLUSH]:
            # if the hand bases differ kickers do not apply
            if set(winner_best_vals) != set(loser_best_vals): return
            else: searchForKicker = zip(winner_kicker_vals, loser_kicker_vals)

        elif winner.handenum == Hand.FLUSH:
            # it can be equal or >
            if winner_best_vals[0] != loser_best_vals[0]: return
            searchForKicker = zip(winner_best_vals[1:], loser_best_vals[1:])

        # hand in ["Straight", "FullHouse" "StraightFlush"]
        else: return

        kickers = []
        for w_val, l_val in searchForKicker:
            kickers.append(w_val)
            if w_val > l_val: return kickers

if __name__ == '__main__':
    from random import sample
    from timeit import timeit
    n = 10**5
    cards = [[val, suit] for suit in Suit for val in Value]
    print(timeit(lambda: HandParser(sample(cards, 7)).parse(), number=n))
    
