HANDS = ['High Card', 'One Pair', 'Two Pair', 'Three of a Kind', 'Straight', 'Flush', 'Full House', 'Four of a Kind', 'Straight Flush']

# 33.26s for Parsing a Million hands
class HandParser:
    __slots__ = ['original_cards', 'cards', 'values', 'suits', 'status', 'top_hand_name', 'hand_base_cards', 'kickers', 'top_cards']
    deck = [[value_index, suit_index] for suit_index in range(4) for value_index in range(13)] # this represents how cards in deck are represented

    def __init__(self, hand):
        # AssertionError if hand is not valid
        test_assert_hand = [str(val) + str(suit) for val, suit in hand]
        assert len(test_assert_hand) == len(set(test_assert_hand)) == 7 and not [card for card in hand if card not in self.deck]
        self.original_cards = hand

        # hand is always represented by [[value_index, suit_index], [value_index, suit_index], ..., [value_index, suit_index]]
        self.cards = sorted(hand)
        self.values, self.suits = tuple(([card[i] for card in self.cards] for i in (0, 1)))

        # dict with keys of hands and values of cards representing that hand
        self.status = self.get_hand_status()

        # name of best hand (eg. Flush)
        self.top_hand_name = [stat for stat in self.status if self.status[stat]][-1]

        # best five cards in hand (all that really matters)
        self.hand_base_cards = self.status[self.top_hand_name]
        self.kickers = [card for card in self.cards if card not in self.hand_base_cards][::-1][:5 - len(self.hand_base_cards)]
        self.top_cards = self.hand_base_cards + self.kickers

    def __repr__(self):
        return f'HandParser({str(self)})'

    def __str__(self):
        return str([[value, suit] for value, suit in self.cards])

    def __eq__(self, other):
        if HANDS.index(self.top_hand_name) != HANDS.index(pther.top_hand_name):
            return False
        for s_card, o_card in zip(self.top_cards, other.top_cards):
            if s_card[0] != o_card[0]:
                return False
        return True

    def __gt__(self, other):
        if HANDS.index(self.top_hand_name) > HANDS.index(other.top_hand_name):
            return True
        elif HANDS.index(self.top_hand_name) < HANDS.index(other.top_hand_name):
            return False
        else:
            for s_card, o_card in zip(self.top_cards, other.top_cards):
                if s_card[0] == o_card[0]:
                    continue
                return s_card[0] > o_card[0]
        return False

    def __lt__(self, other):
        if HANDS.index(self.top_hand_name) < HANDS.index(other.top_hand_name):
            return True
        elif HANDS.index(self.top_hand_name) > HANDS.index(other.top_hand_name):
            return False
        else:
            for s_card, o_card in zip(self.top_cards, other.top_cards):
                if s_card[0] == o_card[0]:
                    continue
                return s_card[0] < o_card[0]
        return False

    def status_repr(self):
        return '\n'.join([f'{stat} --> {self.status[stat]}' for stat in self.status])

    def get_hand_status(self):
        status = {_hand: [] for _hand in HANDS}

        # Check for pairs
        from_count_to_hand = {2 : 'One Pair', 3 : 'Three of a Kind', 4 : 'Four of a Kind'}
        # count repetitions, number of one pairs and number of three of a kinds
        counters = [1,0,0]
        # just leave this part alone, you think you know what you are doing but leave it, i'm pretty sure it works now
        for i in range(1, len(self.cards))[::-1]: # it's reversed so it can skip low vlue pairs if there are too many
            if self.cards[i - 1][0] == self.cards[i][0]:
                counters[0] += 1
            if self.cards[i - 1][0] != self.cards[i][0] or i == 1:
                i = 0 if i == 1 and self.cards[i - 1][0] == self.cards[i][0] else i # if i = 1 this if block executes in the same loop as the previous one
                if not (counters[0] == 2 and counters[1] >= 1 or counters[0] == 3 and counters[2] >= 1 or counters[0] == 1):
                    status[from_count_to_hand[counters[0]]] = self.cards[i: i + counters[0]]
                elif counters[0] == 2 and counters[1] == 1:
                    status['Two Pair'] = status['One Pair'] + self.cards[i: i + counters[0]]
                    status['One Pair'] = []
                elif counters[0] == 3 and counters[2] == 1:
                    status['Full House'] = status['Three of a Kind'] + self.cards[i: i + counters[0] - 1]

                counters[2] += 1 if counters[0] == 3 else 0
                counters[1] += 1 if counters[0] == 2 else 0
                counters[0] = 1

        if status['One Pair'] and status['Three of a Kind']:
            status['Full House'] = status['Three of a Kind'] + status['One Pair']
        if status['Two Pair'] and status['Three of a Kind']:
            status['Full House'] = status['Three of a Kind'] + status['Two Pair'][:2]

        # Check for Straight
        whole_straight = [[], []]
        aces_front, aces_back = [ace for ace in self.cards if ace[0] == 12] + [not_ace for not_ace in self.cards if not_ace[0] != 12], self.cards
        # check if straight was made by aces being the last or the first card
        for j, hand in zip([0, 1], [aces_back, aces_front]):
            straight_count, duplicates = 1, 0
            for i in range(len(hand) - 1)[::-1]:
                if hand[i][0] + 1 == hand[i + 1][0]:
                    straight_count += 1
                    whole_straight[j] = hand[i: i + straight_count + duplicates] if straight_count >= 5 else whole_straight[j]
                elif hand[i][0] == hand[i + 1][0]:
                    duplicates += 1
                    whole_straight[j] = hand[i: i + straight_count + duplicates] if straight_count >= 5 else whole_straight[j]
                elif hand[i][0] != hand[i + 1][0]:
                    straight_count = 1
                    duplicates = 0
            if aces_back == aces_front:
                break

        whole_straight = whole_straight[0] if len(whole_straight[0]) >= len(whole_straight[1]) else whole_straight[1]
        # remove duplicates in the middle of straight eg. 5,6,6,7,8,9
        status['Straight'] = [whole_straight[i] for i in range(len(whole_straight)) if whole_straight[i][0] not in self.get_values(whole_straight[:i])][-5:][::-1]

        # Check for Flush
        for suit in range(4):
            if self.suits.count(suit) >= 5:
                status['Flush'] = self.get_same_suits(self.cards, suit)[-5:][::-1]
                break

        # Check for Straight Flush
        if status['Straight'] and status['Flush']:
            candidates =  self.get_same_suits(whole_straight, suit)
            # we know all are the same suit so they are all different numbers
            for pos in [[value for value, _ in candidates], [value for value, _ in candidates if value == 12] + [value for value, _ in candidates if value != 12]]:
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
            status['High Card'] = [self.cards[-1]]

        return status

    @staticmethod
    def get_values(split_cards):
        return [value for value, _ in split_cards]
    @staticmethod
    def get_same_suits(split_cards, match):
        return [[value, suit] for value, suit in split_cards if suit == match]

    # get winners
    @staticmethod
    def winners(hands: list) -> list:
        winner = max(hands)
        return [hand for hand in hands if hand == winner]

    @staticmethod
    def get_kicker(hands: list):
        kicker = []

        winner = max(hands)
        losers = [hand for hand in hands if hand < winner]
        if not losers: # everyone won or winner the only one in hands
            return None
        max_loser = max(losers)

        # if winner won by a hand level there is no kicker
        if HANDS.index(winner.top_hand_name) > HANDS.index(max_loser.top_hand_name):
            return None
        else:
            winner_best_vals = [card[0] for card in winner.hand_base_cards]
            loser_best_vals = [card[0] for card in max_loser.hand_base_cards]

            # here the best hand is represented by not 5 card + kickers != 0
            if winner.top_hand_name in ['High Card', 'One Pair', 'Two Pair', 'Three of a Kind', 'Full House', 'Four of a Kind']:
                if set(winner_best_vals) != set(loser_best_vals):
                    return None
                else:
                    searchForKicker = zip(winner.kickers, max_loser.kickers)

            elif winner.top_hand_name == 'Flush':
                if winner_best_vals[0] != loser_best_vals[0]: # it can be equal or >
                    return None
                searchForKicker = zip(winner.hand_base_cards[1:], max_loser.hand_base_cards[1:])

            # hand in ['Straight', 'Straight Flush']
            else:
                return None

            for w_card, l_card in searchForKicker:
                if w_card[0] == l_card[0]:
                    kicker.append(w_card[0])
                elif w_card[0] > l_card[0]:
                    kicker.append(w_card[0])
                    return kicker


if __name__ == '__main__':
    from numpy.random import shuffle
    from timeit import timeit

    def ran_hand():
        crds = HandParser.deck.copy()
        shuffle(crds)
        return [crds.pop() for _ in range(7)]
