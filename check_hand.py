from random import randint, shuffle

HANDS = ['High Card', 'One Pair', 'Two Pairs', 'Three of a Kind', 'Straight', 'Flush', 'Full House', 'Four of a Kind', 'Straight Flush']
SUITS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
COLORS = ['Hearts', 'Diamonds', 'Spades', 'Clubs']
CARDS = [f'{suit} of {color}' for color in COLORS for suit in SUITS]

class HandChecker:

    def __init__(self, hand):
        if not self.is_valid_hand(hand):
            raise ValueError

        # hand is always represented by [[suit, color], [suit, color], ..., [suit, color]]
        self.hand = self.sort_cards(self.split_cards(hand))
        self.suits, self.colors = tuple([card[i] for card in self.hand] for i in [0, 1])

        # [] changes to the higher five cards that represent hand
        self.status = {_hand: [] for _hand in HANDS}
        self._get_hand_status()
        self.highest_hand = [_hand for _hand in self.status if self.status[_hand]][-1]

    def __repr__(self):
        return f'HandChecker({str(self)})'
    def __str__(self):
        return str([f'{suit} of {color}' for suit, color in self.hand])


    def _get_hand_status(self):
        # set high cards
        self.status['High Card'] = self.hand[2:]

        # check for pairs
        from_count_to_hand = {2 : 'One Pair', 3 : 'Three of a Kind', 4 : 'Four of a Kind'}
        # count repetitions, number of one pairs and number of two pairs in that order
        counters = [1,0,0]
        for i in range(1, len(self.hand))[::-1]:
            if self.hand[i - 1][0] == self.hand[i][0]:
                counters[0] += 1
            else:
                if not (counters[0] == 2 and counters[1] >= 1 or counters[0] == 3 and counters[2] >= 1 or counters[0] == 1):
                    self.status[from_count_to_hand[counters[0]]].append(self.hand[i: i + counters[0]])
                elif counters[0] == 2 and counters[1] == 2:
                    self.status['Two Pairs'] = self.status['One Pair'] + self.hand[i: i + counters[0]]
                    self.status['One Pair'] = []
                elif counters[0] == 3 and counters[2] == 1:
                    self.status['Full House'] = self.status['Three of a Kind'] + self.hand[i: i + counters[0] - 1]

                counters[1] += 1 if counters[0] == 3 else 0
                counters[2] += 1 if counters[0] == 2 else 0
                counters[0] = 1

        if self.status['One Pair'] and self.status['Three of a Kind']:
            self.status['Full House'] = self.status['Two Pairs'] + self.status['Three of a Kind']
        if self.status['Two Pairs'] and self.status['Three of a Kind']:
            self.status['Full House'] = self.status['Two Pairs'][0] + self.status['Three of a Kind']

        # check for Straight
        whole_straight = []
        straight_count = 1
        for i in range(1, len(self.hand))[::-1]:
            if (SUITS.index(self.hand[i][0]) - 1) % len(SUITS) == SUITS.index(self.hand[i - 1][0]):
                straight_count += 1
                whole_straight = self.hand[i: i + straight_count] if straight_count >= 5 else whole_straight
            elif not SUITS.index(self.hand[i][0]) == SUITS.index(self.hand[i - 1][0]):
                straight_count = 1

        self.status['Straight'] = whole_straight[-5:] if whole_straight else []

        #check for Flush
        for color in COLORS:
            if self.colors.count(color) >= 5:
                self.status['Flush'] = self.get_same_colors(self.hand, color)[-5:]
                break

        # check for Straight Flush
        if self.status['Straight'] and self.status['Flush'] and len(self.get_same_colors(whole_straight, color)) >= 5:
            self.status['Straight Flush'] = [card for card in whole_straight if card[1] == color][-5:]


    @staticmethod
    def is_valid_hand(hand):
        if not (len(hand) == len(set(hand)) == 7):
            return False
        for card in hand:
            if card not in CARDS:
                return False
        return True

    @staticmethod
    def split_cards(raw_cards):
        return [[suit, color] for suit, color in ((card.split(' of ')[0], card.split(' of ')[1]) for card in raw_cards)]

    @staticmethod
    def sort_cards(split_cards):
        sorted_indexed = sorted([[SUITS.index(suit), color] for suit, color in split_cards])
        return [[SUITS[i], color] for i, color in sorted_indexed]

    @staticmethod
    def get_same_colors(split_cards, match):
        return [[suit, color] for suit, color in split_cards if color == match]
    @staticmethod
    def get_same_suits(split_cards, match):
        return [[suit, color] for suit, color in split_cards if suit == match]


def random_hand():
    _cards = CARDS.copy()
    shuffle(_cards)
    _hand = [_cards.pop(randint(0, len(_cards) - 1)) for _ in range(7)]
    return _hand

c = HandChecker(random_hand())
print(c)
print(c.highest_hand)
