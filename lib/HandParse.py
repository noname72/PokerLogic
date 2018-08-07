HANDS = ['High Card', 'One Pair', 'Two Pairs', 'Three of a Kind', 'Straight', 'Flush', 'Full House', 'Four of a Kind', 'Straight Flush']
VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
VALUES_S = ['Ace'] + VALUES[:-1]
SUITS = ['Hearts', 'Diamonds', 'Spades', 'Clubs']
CARDS = [f'{value} of {suit}' for suit in SUITS for value in VALUES]

class HandParser:

    def __init__(self, hand):
        # AssertionError if hand is not valid
        assert len(hand) == len(set(hand)) == 7 and not [card for card in hand if card not in CARDS]
        self.original = hand

        # hand is always represented by [[value, suit], [value, suit], ..., [value, suit]]
        self.hand = self.sort_cards(self.split_cards(hand))
        self.values, self.suits = tuple(([card[i] for card in self.hand] for i in (0, 1)))

        # dict with keys of hands and values of cards representing that hand
        self.status = self.get_hand_status()

        # name of best hand (eg. Flush)
        self.best_hand_name = [stat for stat in self.status if self.status[stat]][-1]

        # best five cards in hand (all that really matters)
        best_cards = self.status[self.best_hand_name]
        self.best_cards = best_cards + [card for card in self.hand if card not in best_cards][::-1][:5 - len(best_cards)]

    def __repr__(self):
        return f'HandParser({str(self)})'

    def __str__(self):
        return str([f'{value} of {suit}' for value, suit in self.hand])

    def __eq__(self, other):
        return not self > other and not self < other

    def __gt__(self, other):
        if HANDS.index(self.best_hand_name) > HANDS.index(other.best_hand_name):
            return True
        elif HANDS.index(self.best_hand_name) < HANDS.index(other.best_hand_name):
            return False
        else:
            for s_card, o_card in zip(self.best_cards, other.best_cards):
                if VALUES.index(s_card[0]) > VALUES.index(o_card[0]):
                    return True
                elif VALUES.index(s_card[0]) < VALUES.index(o_card[0]):
                    return False
        return False

    def __lt__(self, other):
        if HANDS.index(self.best_hand_name) < HANDS.index(other.best_hand_name):
            return True
        elif HANDS.index(self.best_hand_name) > HANDS.index(other.best_hand_name):
            return False
        else:
            for s_card, o_card in zip(self.best_cards, other.best_cards):
                if VALUES.index(s_card[0]) < VALUES.index(o_card[0]):
                    return True
                elif VALUES.index(s_card[0]) > VALUES.index(o_card[0]):
                    return False
        return False

    def status_repr(self):
        return '\n'.join([f'{stat} --> {self.status[stat]}' for stat in self.status])

    def best_hand_repr(self):
        win = [_hand for _hand in self.status if self.status[_hand]][-1]
        if win in ['One Pair', 'Three of a Kind', 'Four of a Kind']:
            return f'{win} of {self.status[win][0][0]}\'s'
        elif win == 'High Card':
            return f'High Card {self.status["High Card"][0][0]}'
        elif win == 'Two Pairs':
            return f'Two Pairs, {self.status["Two Pairs"][0][0]}\'s and {self.status["Two Pairs"][2][0]}\'s'
        elif win == 'Straight':
            return f'{"Straight"} from {self.status["Straight"][-1][0]}\'s to {self.status["Straight"][0][0]}\'s'
        elif win == 'Flush':
            return f'Flush of {self.status["Flush"][0][1]} with high card {self.status["Flush"][0][0]}'
        elif win == 'Full House':
            return f'Full House {self.status["Full House"][0][0]}\'s over {self.status["Full House"][-1][0]}\'s'
        elif win == 'Straight Flush':
            return f'{"Straight Flush"} of {self.status["Straight Flush"][0][1]} from {self.status["Straight Flush"][0][0]}\'s to {self.status["Straight Flush"][-1][0]}\'s'

    def get_hand_status(self):
        status = {_hand: [] for _hand in HANDS}

        # Check for pairs
        from_count_to_hand = {2 : 'One Pair', 3 : 'Three of a Kind', 4 : 'Four of a Kind'}
        # count repetitions, number of one pairs and number of three of a kinds
        counters = [1,0,0]
        # just leave this part alone, you think you know what you are doing but leave it, i'm pretty sure it works now
        for i in range(1, len(self.hand))[::-1]: # it's reversed so it can skip low vlue pairs if there are too many
            if self.hand[i - 1][0] == self.hand[i][0]:
                counters[0] += 1
            if self.hand[i - 1][0] != self.hand[i][0] or i == 1:
                i = 0 if i == 1 and self.hand[i - 1][0] == self.hand[i][0] else i # if i = 1 this if block executes in the same loop as the previous one
                if not (counters[0] == 2 and counters[1] >= 1 or counters[0] == 3 and counters[2] >= 1 or counters[0] == 1):
                    status[from_count_to_hand[counters[0]]] = self.hand[i: i + counters[0]]
                elif counters[0] == 2 and counters[1] == 1:
                    status['Two Pairs'] = status['One Pair'] + self.hand[i: i + counters[0]]
                    status['One Pair'] = []
                elif counters[0] == 3 and counters[2] == 1:
                    status['Full House'] = status['Three of a Kind'] + self.hand[i: i + counters[0] - 1]

                counters[2] += 1 if counters[0] == 3 else 0
                counters[1] += 1 if counters[0] == 2 else 0
                counters[0] = 1

        if status['One Pair'] and status['Three of a Kind']:
            status['Full House'] = status['Three of a Kind'] + status['One Pair']
        if status['Two Pairs'] and status['Three of a Kind']:
            status['Full House'] = status['Three of a Kind'] + status['Two Pairs'][:2]

        # Check for Straight
        whole_straight = [[], []]
        aces_front, aces_back = [ace for ace in self.hand if ace[0] == 'Ace'] + [not_ace for not_ace in self.hand if not_ace[0] != 'Ace'], self.hand
        # check if straight was made by aces being the last or the first card
        for j, hand, values in zip([0, 1], [aces_back, aces_front], [VALUES, VALUES_S]):
            straight_count, duplicates = 1, 0
            for i in range(len(hand) - 1)[::-1]:
                if (values.index(hand[i][0]) + 1 == values.index(hand[i + 1][0])):
                    straight_count += 1
                    whole_straight[j] = hand[i: i + straight_count + duplicates] if straight_count >= 5 else whole_straight[j]
                elif values.index(hand[i][0]) == values.index(hand[i + 1][0]):
                    duplicates += 1
                    whole_straight[j] = hand[i: i + straight_count + duplicates] if straight_count >= 5 else whole_straight[j]
                elif values.index(hand[i][0]) != values.index(hand[i + 1][0]):
                    straight_count = 1
                    duplicates = 0
            if aces_back == aces_front:
                break

        whole_straight = whole_straight[0] if len(whole_straight[0]) >= len(whole_straight[1]) else whole_straight[1]
        # remove duplicates in the middle of straight eg. 5,6,6,7,8,9
        status['Straight'] = [whole_straight[i] for i in range(len(whole_straight)) if whole_straight[i][0] not in self.get_values(whole_straight[:i])][-5:][::-1]

        # Check for Flush
        for suit in SUITS:
            if self.suits.count(suit) >= 5:
                status['Flush'] = self.get_same_suits(self.hand, suit)[-5:][::-1]
                break

        # Check for Straight Flush
        if status['Straight'] and status['Flush']:
            candidates =  self.get_same_suits(whole_straight, suit)
            # we know all are the same suit so they are all different numbers
            for pos in [[VALUES.index(value) for value, _ in candidates], [VALUES_S.index(value) for value, _ in candidates]]:
                count = 1
                for i in range(len(pos) - 1)[::-1]:
                    count = count + 1 if pos[i] + 1 == pos[i + 1] else 1
                    if count == 5:
                        status['Straight Flush'] = candidates[::-1][i: i + 5][::-1]
                        break
                if status['Straight Flush']:
                    break

        # Set high card if there is none higher hands matched
        if not [status[stat_name] for stat_name in status if status[stat_name]]:
            status['High Card'] = self.hand[-5:][::-1]

        return status

    @staticmethod
    def split_cards(raw_cards):
        return [[value, suit] for value, suit in ((card.split(' of ')[0], card.split(' of ')[1]) for card in raw_cards)]

    @staticmethod
    def sort_cards(split_cards):
        sorted_indexed = sorted([[VALUES.index(value), suit] for value, suit in split_cards])
        return [[VALUES[i], suit] for i, suit in sorted_indexed]

    @staticmethod
    def get_values(split_cards):
        return [value for value, _ in split_cards]
    @staticmethod
    def get_same_suits(split_cards, match):
        return [[value, suit] for value, suit in split_cards if suit == match]
    @staticmethod
    def get_same_values(split_cards, match):
        return [[value, suit] for value, suit in split_cards if value == match]

    @staticmethod
    def max(hands : list) -> list:
        winner = max(hands)
        return [hand for hand in hands if hand == winner]
