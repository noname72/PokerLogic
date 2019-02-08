class models:
    nvals = 13
    nsuits = 4
    handdict = ["HighCard", "OnePair", "TwoPair",
    "ThreeOfAKind", "Straight", "Flush",
    "FullHouse", "FourOfAKind", "StraightFlush"]
    nhands = len(handdict)
    for i, hand in enumerate(handdict): locals()[hand] = i

class HandParser:
    __slots__ = ["original", "ncards", "cards", "valnums",
                 "suitnums", "handindex", "__handbase", "kickers"]

    def __init__(self, cards: list):
        self.original = cards
        self.ncards = len(cards)
        self.cards = sorted(cards, key = lambda x: x[0])

        self.valnums = [0] * models.nvals
        self.suitnums = [0] * models.nsuits
        for value, suit in cards:
            self.valnums[value] += 1
            self.suitnums[suit] += 1

        self.kickers = []
        self.handindex = None
        self.__handbase = []

    @property
    def handbase(self):
        return self.__handbase
    @handbase.setter
    def handbase(self, value):
        self.__handbase = sorted(value, reverse=True)

    def idx2cards(self, full=True):
        if full is True: return map(
            lambda i: self.cards[i],
            self.handbase + self.kickers)
        elif full is False: return map(
            lambda i: self.cards[i],
            self.handbase)
        elif full is 'k': return map(
            lambda i: self.cards[i],
            self.kickers)

    def __str__(self):
        return str([[value, suit] for value, suit in self.cards])

    def __repr__(self):
        return f"HandParser({str(self)})"

    def __eq__(self, other):
        if self.handindex != other.handindex: return False
        for (s_val, _), (o_val, _) in zip(self.idx2cards(),
                                          other.idx2cards()):
            if s_val != o_val: return False
        return True

    def __gt__(self, other):
        if self.handindex != other.handindex:
            return self.handindex > other.handindex
        for (s_val, _), (o_val, _) in zip(self.idx2cards(),
                                          other.idx2cards()):
            if s_val != o_val: return s_val > o_val
        return False

    def __lt__(self, other):
        return other > self

    def addCards(self, cards):
        self.original.extend(cards)
        self.ncards += len(cards)
        self.cards = sorted(self.original, key = lambda x: x[0])
        for value, suit in cards:
            self.valnums[value] += 1
            self.suitnums[suit] += 1

    @staticmethod
    def checkStraight(valnums):
        straightcounter = 1
        for i in range(len(valnums)-1, -1, -1):
            if valnums[i-1] and valnums[i]:
                straightcounter += 1
                if straightcounter == 5: break
            else: straightcounter = 1
        return straightcounter, i

    @staticmethod
    def getStraightFrom(cards, straightstart):
        instraight = [False] * models.nvals
        for i in range(straightstart - 1, straightstart + 4):
            instraight[i] = True
        return_cards = []
        for i, (value, _) in enumerate(cards):
            if instraight[value]:
                return_cards.append(i)
                instraight[value] = False
        return return_cards

    def analyse(self):
        # order in which hands will be iterated
        handrange = range(self.ncards-1, -1, -1)

        # number of zero, one, two pair,
        # three and four of a kinds
        npairs = [0] * 5
        for num in self.valnums: npairs[num] += 1

        # check flush
        flushsuit = [i for i in range(models.nsuits) if self.suitnums[i] >= 5]
        # check straight
        straightcount, straightstart = \
            self.checkStraight(self.valnums)

        # straight flush
        if straightcount == 5 and flushsuit:
            cards = []
            suitedVals = [0] * models.nvals
            for val, suit in self.cards:
                if suit == flushsuit[0]:
                    suitedVals[val] += 1
                    cards.append([val, suit])
            # can revalue straightcount, flush > straight
            straightcount, i = self.checkStraight(suitedVals)
            if straightcount == 5:
                self.handindex = models.StraightFlush
                self.handbase = self.getStraightFrom(cards, i)
                return

        # four of a kind
        if npairs[4]:
            vals = [i for i in range(models.nvals) if self.valnums[i] == 4]
            cards = [i for i in handrange if self.cards[i][0] == vals[0]]
            self.handindex = models.FourOfAKind
            self.handbase = cards

        # full house
        elif npairs[3] == 2 or npairs[3] == 1 and npairs[2] >= 1:
            inhouse = [False] * models.nvals
            threes, twos = [], []
            for val, num in enumerate(self.valnums):
                if num == 3: threes.append(val)
                elif num == 2: twos.append(val)
            maxvals = [threes.pop(), max(threes + twos)]
            cards, i = [], self.ncards - 1
            while len(cards) < 5:
                if self.cards[i][0] in maxvals: cards.append(i)
                i -= 1
            self.handindex = models.FullHouse
            self.handbase = cards

        # flush
        elif flushsuit:
            fcolor = flushsuit[0]
            cards = [i for i in handrange if self.cards[i][1] == fcolor]
            self.handindex = models.Flush
            self.handbase = cards[:5]

        # straight
        elif straightcount == 5:
            self.handindex = models.Straight
            self.handbase = self.getStraightFrom(self.cards, straightstart)

        # three of a kind
        elif npairs[3] == 1:
            vals = [i for i in range(models.nvals) if self.valnums[i] == 3]
            cards = [i for i in handrange if self.cards[i][0] == vals[0]]
            self.handindex = models.ThreeOfAKind
            self.handbase = cards

        # two / one pair
        elif npairs[2]:
            hand = models.OnePair if npairs[2] == 1 else models.TwoPair
            lim = 2 if hand == models.OnePair else 4
            vals = [i for i in range(models.nvals) if self.valnums[i] == 2]
            cards, i = [], self.ncards - 1
            while len(cards) < lim:
                if self.cards[i][0] in vals: cards.append(i)
                i -= 1
            self.handindex = hand
            self.handbase = cards

        # high card
        else:
            self.handindex = models.HighCard
            self.handbase = [self.ncards - 1]

    def getKickers(self):
        self.kickers = []
        inhand = [False] * self.ncards
        for i in self.handbase: inhand[i] = True
        for i, _ in zip(range(len(self.cards)-1,-1,-1),
                        range(5 - len(self.handbase))):
            if not inhand[i]: self.kickers.append(i)

    @classmethod
    def get_kickers(cls, hands: list):
        winner = max(hands)
        losers = [hand for hand in hands if hand < winner]
        if not losers: return # everyone in hands is split evenly
        max_loser = max(losers)

        # if winner won by a hand level there is no kicker
        if winner.handindex > max_loser.handindex: return
        winner_best_vals = [val for val, _ in winner.idx2cards(False)]
        winner_kicker_vals = [val for val, _ in winner.idx2cards('k')]
        loser_best_vals = [val for val, _ in max_loser.idx2cards(False)]
        loser_kicker_vals = [val for val, _ in max_loser.idx2cards('k')]

        # the hands represented by five hands do not have kickers
        if winner.handindex not in [models.Straight, models.Flush,
                                    models.FullHouse, models.StraightFlush]:
            # if the hand bases differ kickers do not apply
            if set(winner_best_vals) != set(loser_best_vals): return
            else: searchForKicker = zip(winner_kicker_vals, loser_kicker_vals)
            
        elif winner.handindex == Flush:
            # it can be equal or >
            if winner_best_vals[0] != loser_best_vals[0]: return
            searchForKicker = zip(winner_best_vals[1:], loser_best_vals[1:])

        # hand in ["Straight", "FullHouse" "StraightFlush"]
        else: return

        kickers = []
        for w_val, l_val in searchForKicker:
            kickers.append(w_val)
            if w_val > l_val: return kickers
