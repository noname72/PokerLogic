from bisect import insort
from pokerlib.enums import Hand, Value, Suit

class HandParser:
    __slots__ = ["original", "ncards", "cards",
                 "handenum", "handbase", "kickers",
                 "__valnums", "__suitnums",
                 "__flushsuit", "__straightindexes"]

    def __init__(self, cards: list):
        self.original = cards
        self.ncards = len(cards)
        self.cards = sorted(cards, key = lambda x: x[0])

        self.handenum = None
        self.handbase = []
        self.kickers = []

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

        self.__straightindexes = \
            self.getStraightIndexes(self.__valnums)

    @property
    def handbasecards(self):
        return map(
            lambda i: self.cards[i],
            self.handbase
            )
    @property
    def kickercards(self):
        return map(
            lambda i: self.cards[i],
            self.handbase + self.kickers
            )
    @property
    def handfullcards(self):
        return map(
            lambda i: self.cards[i],
            self.handbase + self.kickers
            )

    def __str__(self):
        return str(self.cards)

    def __repr__(self):
        return f"HandParser({self.cards})"

    def __eq__(self, other):
        if self.handenum != other.handenum: return False
        for (s_val, _), (o_val, _) in zip(self.handfullcards,
                                          other.handfullcards):
            if s_val != o_val: return False
        return True

    def __gt__(self, other):
        if self.handenum != other.handenum:
            return self.handenum > other.handenum
        for (s_val, _), (o_val, _) in zip(self.handfullcards,
                                          other.handfullcards):
            if s_val != o_val: return s_val > o_val
        return False

    def __lt__(self, other):
        return other > self

    def addCards(self, cards):
        self.original.extend(cards)
        self.ncards += len(cards)
        map(lambda card: insort(self.cards, card), cards)

        self.handenum = None
        self.handbase.clear()
        self.kickers.clear()

        for value, suit in cards:
            self.__valnums[value] += 1
            self.__suitnums[suit] += 1

        for suit in Suit:
            if self.__suitnums[suit] >= 5:
                self.__flushsuit = suit
                break

        self.__straightindexes = \
            self.getStraightIndexes(self.__valnums)

    @staticmethod
    def getStraightIndexes(valnums):
        straightindexes = [None] * 5
        straightlen, indexptr = 1, sum(valnums)
        for i in reversed(range(len(valnums))):
            indexptr -= valnums[i]
            if valnums[i-1] and valnums[i]:
                straightindexes[straightlen-1] = indexptr
                straightlen += 1
                if straightlen == 5:
                    if indexptr == 0:
                        indexptr = sum(valnums)-1
                    else: indexptr -= valnums[i-1]
                    straightindexes[4] = indexptr
                    return straightindexes
            else: straightlen = 1

    def setStraightFlush(self):
        counter = 0
        suited_vals, permut = [0] * 13, [0] * len(self.cards)
        for i, (val, suit) in enumerate(self.cards):
             if suit == self.__flushsuit:
                 suited_vals[val] += 1
                 permut[counter] = i
                 counter += 1

        suited_handbase = self.getStraightIndexes(suited_vals)
        if suited_handbase is not None:
            self.handenum = Hand.STRAIGHTFLUSH
            self.handbase = [permut[i] for i in suited_handbase]
            return True

        return False

    def setFourOfAKind(self):
        self.handenum = Hand.FOUROFAKIND

        hindex = self.ncards
        for valnum in self.__valnums:
            hindex += valnum
            if valnum == 4: break

        self.handbase = [hindex-3, hindex-2, hindex-1, hindex]

    def setFullHouse(self):
        self.handenum = Hand.FULLHOUSE

        threes, twos = [], []
        hindex = -1
        for val, valnum in enumerate(self.__valnums):
            hindex += valnum
            if valnum == 3: threes.append((val, hindex))
            elif valnum == 2: twos.append((val, hindex))

        i1, i2 = [threes.pop()[1], max(threes + twos)[1]]
        self.handbase = [i1-2, i1-1, i1, i2-1, i2]

    def setFlush(self):
        self.handenum = Hand.FLUSH
        self.handbase.clear()

        counter = 0
        for i in reversed(range(self.ncards)):
            if self.cards[i][1] == self.__flushsuit:
                self.handbase.append(i)
                counter += 1
            if counter == 5:
                break

    def setStraight(self):
        self.handenum = Hand.STRAIGHT
        self.handbase = self.__straightindexes

    def setThreeOfAKind(self):
        self.handenum = Hand.THREEOFAKIND
        self.handbase.clear()

        hindex = -1
        for valnum in self.__valnums:
            hindex += valnum
            if valnum == 3: break

        self.handbase = [hindex-2, hindex-1, hindex]

    def setTwoPair(self):
        self.handenum = Hand.TWOPAIR
        self.handbase.clear()

        hindex, paircounter = self.ncards, 0
        for valnum in reversed(self.__valnums):
            hindex -= valnum
            if valnum == 2:
                self.handbase.extend([hindex, hindex+1])
                paircounter += 1
                if paircounter == 2: break

    def setOnePair(self):
        self.handenum = Hand.ONEPAIR

        hindex = self.ncards
        for valnum in self.__valnums:
            hindex += valnum
            if valnum == 2: break

        self.handbase = [hindex-1, hindex]

    def setHighCard(self):
        self.handenum = Hand.HIGHCARD
        self.handbase = [self.ncards - 1]

    def parse(self):
        pairnums = [0] * 5
        for num in self.__valnums: pairnums[num] += 1

        # straight flush
        if None not in [self.__straightindexes, self.__flushsuit] \
        and self.setStraightFlush(): pass

        # four of a kind
        elif pairnums[4]:
            self.setFourOfAKind()

        # full house
        elif pairnums[3] == 2 or pairnums[3] == 1 and pairnums[2] >= 1:
            self.setFullHouse()

        # flush
        elif self.__flushsuit is not None:
            self.setFlush()

        # straight
        elif self.__straightindexes is not None:
            self.setStraight()

        # three of a kind
        elif pairnums[3]:
            self.setThreeOfAKind()

        # two pair
        elif pairnums[2] >= 2:
            self.setTwoPair()

        # one pair
        elif pairnums[2] == 1:
            self.setOnePair()

        # high card
        else: self.setHighCard()

    def getKickers(self):
        self.kickers.clear()
        
        inhand = [False] * self.ncards
        for i in self.handbase: inhand[i] = True
        
        i, lim = self.ncards - 1, 5 - len(self.handbase)
        while len(self.kickers) < lim and i >= 0:
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
        winner_best_vals = [val for val, _ in winner.handbasecards]
        winner_kicker_vals = [val for val, _ in winner.kickercards]
        loser_best_vals = [val for val, _ in max_loser.handbasecards]
        loser_kicker_vals = [val for val, _ in max_loser.kickercards]

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
