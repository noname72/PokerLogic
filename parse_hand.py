from random import randint, shuffle

HANDS = ['High Card', 'One Pair', 'Two Pairs', 'Three of a Kind', 'Straight', 'Flush', 'Full House', 'Four of a Kind', 'Straight Flush']
SUITS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
SUITS_S = ['Ace'] + SUITS[:-1]
COLORS = ['Hearts', 'Diamonds', 'Spades', 'Clubs']
CARDS = [f'{suit} of {color}' for color in COLORS for suit in SUITS]

class HandParser:

    def __init__(self, hand):
        if not self.is_valid_hand(hand):
            raise ValueError('Hand is invalid')

        # hand is always represented by [[suit, color], [suit, color], ..., [suit, color]]
        self.hand = self.sort_cards(self.split_cards(hand))
        self.suits, self.colors = tuple([card[i] for card in self.hand] for i in [0, 1])

        # [] changes to the higher five cards that represent hand
        self.status = {_hand: [] for _hand in HANDS}
        self._get_hand_status()
        self.best_hand = [_hand for _hand in self.status if self.status[_hand]][-1]

    def __repr__(self):
        return f'HandParser({str(self)})'
    def __str__(self):
        return str([f'{suit} of {color}' for suit, color in self.hand])

    def status_repr(self):
        return '\n'.join([f'{stat} -> {self.status[stat]}' for stat in self.status])

    def _get_hand_status(self):
        # Check for pairs
        from_count_to_hand = {2 : 'One Pair', 3 : 'Three of a Kind', 4 : 'Four of a Kind'}
        # count repetitions, number of one pairs and number of two pairs in that order
        counters = [1,0,0]
        # just leave this part alone, you think you know what you are doing but leave it, i'm pretty sure it works now
        for i in range(1, len(self.hand))[::-1]: # it's reversed so it can skip low vlue pairs if there are too many
            if self.hand[i - 1][0] == self.hand[i][0]:
                counters[0] += 1
            if self.hand[i - 1][0] != self.hand[i][0] or i == 1:
                i = 0 if i == 1 and self.hand[i - 1][0] == self.hand[i][0] else i # if i = 1 this if block executes in the same loop as the previous one
                if not (counters[0] == 2 and counters[1] >= 1 or counters[0] == 3 and counters[2] >= 1 or counters[0] == 1):
                    self.status[from_count_to_hand[counters[0]]] = self.hand[i: i + counters[0]]
                elif counters[0] == 2 and counters[1] == 1:
                    self.status['Two Pairs'] = self.status['One Pair'] + self.hand[i: i + counters[0]]
                    self.status['One Pair'] = []
                elif counters[0] == 3 and counters[2] == 1:
                    self.status['Full House'] = self.status['Three of a Kind'] + self.hand[i: i + counters[0] - 1]

                counters[2] += 1 if counters[0] == 3 else 0
                counters[1] += 1 if counters[0] == 2 else 0
                counters[0] = 1

        if self.status['One Pair'] and self.status['Three of a Kind']:
            self.status['Full House'] = self.status['Three of a Kind'] + self.status['One Pair']
        if self.status['Two Pairs'] and self.status['Three of a Kind']:
            self.status['Full House'] = self.status['Three of a Kind'] + self.status['Two Pairs'][:2]

        # Check for Straight
        whole_straight = [[], []]
        aces_front, aces_back = [ace for ace in self.hand if ace[0] == 'Ace'] + [not_ace for not_ace in self.hand if not_ace[0] != 'Ace'], self.hand
        # check if straight was made by aces being the last or the first card
        for j, hand, suits in zip([0, 1], [aces_back, aces_front], [SUITS, SUITS_S]):
            straight_count, duplicates = 1, 0
            for i in range(len(hand) - 1)[::-1]:
                if (suits.index(hand[i][0]) + 1 == suits.index(hand[i + 1][0])):
                    straight_count += 1
                    whole_straight[j] = hand[i: i + straight_count + duplicates] if straight_count >= 5 else whole_straight[j]
                elif suits.index(hand[i][0]) == suits.index(hand[i + 1][0]):
                    duplicates += 1
                    whole_straight[j] = hand[i: i + straight_count + duplicates] if straight_count >= 5 else whole_straight[j]
                elif suits.index(hand[i][0]) != suits.index(hand[i + 1][0]):
                    straight_count = 1
                    duplicates = 0

        whole_straight  = whole_straight[0] if len(whole_straight[0]) >= len(whole_straight[1]) else whole_straight[1]
        # remove duplicates in the middle of straight eg. 5,6,6,7,8,9
        self.status['Straight'] = [whole_straight[i] for i in range(len(whole_straight)) if whole_straight[i][0] not in self.get_suits(whole_straight[:i])][-5:]

        # Check for Flush
        for color in COLORS:
            if self.colors.count(color) >= 5:
                self.status['Flush'] = self.get_same_colors(self.hand, color)[-5:]
                break

        # Check for Straight Flush
        if self.status['Straight'] and self.status['Flush']:
            candidates =  self.get_same_colors(whole_straight, color)
            indx = self.five_aligned(candidates)
            self.status['Straight Flush'] = candidates[::-1][indx[0]: indx[1]][::-1] if indx else []

        # Set high card if there is none higher hands matched
        if not [self.status[stat_name] for stat_name in self.status if self.status[stat_name]]:
            self.status['High Card'] = self.hand[-5:]

    def best_hand_repr(self):
        win = self.best_hand
        if win in ['One Pair', 'Three of a Kind', 'Four of a Kind']:
            return f'{win} of {self.status[win][0][0]}\'s'
        elif win == 'High Card':
            return f'High Card {self.status["High Card"][-1][0]}'
        elif win == 'Two Pairs':
            return f'Two Pairs, {self.status["Two Pairs"][0][0]}\'s and {self.status["Two Pairs"][2][0]}\'s'
        elif win == 'Straight':
            return f'{"Straight"} from {self.status["Straight"][0][0]}\'s to {self.status["Straight"][-1][0]}\'s'
        elif win == 'Flush':
            return f'Flush of {self.status["Flush"][0][1]} with high card {self.status["Flush"][-1][0]}'
        elif win == 'Full House':
            return f'Full House {self.status["Full House"][0][0][0]}\'s over {self.status["Full House"][-1][0][0]}\'s'
        elif win == 'Straight Flush':
            return f'{"Straight Flush"} of {self.status["Straight Flush"][0][1]} from {self.status["Straight Flush"][0][0]}\'s to {self.status["Straight Flush"][-1][0]}\'s'

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
    def five_aligned(split_cards):
        if_aces_back = [SUITS.index(suit) for suit, _ in split_cards]
        if_aces_front = [SUITS_S.index(suit) for suit, _ in split_cards]
        # we know all are the same color so they are all different numbers
        for pos in [if_aces_back, if_aces_front]:
            count = 1
            for i in range(len(pos) - 1)[::-1]:
                count = count + 1 if pos[i] + 1 == pos[i + 1] else 1
                if count == 5:
                    return (i, i + count)
        return False

    @staticmethod
    def get_suits(split_cards):
        return [suit for suit, _ in split_cards]
    @staticmethod
    def get_same_colors(split_cards, match):
        return [[suit, color] for suit, color in split_cards if color == match]
    @staticmethod
    def get_same_suits(split_cards, match):
        return [[suit, color] for suit, color in split_cards if suit == match]


def random_hand():
    cards = CARDS.copy()
    shuffle(cards)
    hand = [cards.pop(randint(0, len(cards) - 1)) for _ in range(7)]
    return hand

l = []
for i in range(10000):
    c = random_hand()
    a = HandParser(c)
    l.append(a.best_hand)
for elt in set(l):
    print(f'{elt}: {l.count(elt)}')
