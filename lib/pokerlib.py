from itertools import cycle
from copy import copy as shallowcopy
try:
    from numpy.random import shuffle # numpy is faster (fcourse)
except ModuleNotFoundError as e:
    from random import shuffle

# 33.26s for Parsing a Million hands
class HandParser:
    __slots__ = ['original_cards', 'cards', 'values', 'suits', 'status', 'top_hand_name', 'hand_base_cards', 'kickers', 'top_cards']
    HANDS = ['High Card', 'One Pair', 'Two Pair', 'Three of a Kind', 'Straight', 'Flush', 'Full House', 'Four of a Kind', 'Straight Flush']
    deck = [[value_index, suit_index] for suit_index in range(4) for value_index in range(13)] # this represents how cards in deck are represented

    def __init__(self, hand):
        # AssertionError if hand is not valid
        test_assert_hand = [str(val) + str(suit) for val, suit in hand]
        assert len(test_assert_hand) == len(set(test_assert_hand)) <= 7 and not [card for card in hand if card not in self.deck]
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
        kicker_options = [card for card in self.cards if card not in self.hand_base_cards][::-1]
        self.kickers = kicker_options[:5 - len(self.hand_base_cards)] if len(hand) >= 5 else kicker_options
        self.top_cards = self.hand_base_cards + self.kickers

    def __repr__(self):
        return f'HandParser({str(self)})'

    def __str__(self):
        return str([[value, suit] for value, suit in self.cards])

    def __eq__(self, other):
        if HandParser.HANDS.index(self.top_hand_name) != HandParser.HANDS.index(other.top_hand_name):
            return False
        for s_card, o_card in zip(self.top_cards, other.top_cards):
            if s_card[0] != o_card[0]:
                return False
        return True

    def __gt__(self, other):
        if HandParser.HANDS.index(self.top_hand_name) > HandParser.HANDS.index(other.top_hand_name):
            return True
        elif HandParser.HANDS.index(self.top_hand_name) < HandParser.HANDS.index(other.top_hand_name):
            return False
        else:
            for s_card, o_card in zip(self.top_cards, other.top_cards):
                if s_card[0] == o_card[0]:
                    continue
                return s_card[0] > o_card[0]
        return False

    def __lt__(self, other):
        if HandParser.HANDS.index(self.top_hand_name) < HandParser.HANDS.index(other.top_hand_name):
            return True
        elif HandParser.HANDS.index(self.top_hand_name) > HandParser.HANDS.index(other.top_hand_name):
            return False
        else:
            for s_card, o_card in zip(self.top_cards, other.top_cards):
                if s_card[0] == o_card[0]:
                    continue
                return s_card[0] < o_card[0]
        return False

    def add(self, cards): # THIS METHOD SHOULD BE OPTIMIZED
        self.__init__(self.cards + cards)

    def status_repr(self):
        return '\n'.join([f'{stat} --> {self.status[stat]}' for stat in self.status])

    def get_hand_status(self):
        status = {_hand: [] for _hand in HandParser.HANDS}

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

    @staticmethod
    def get_kicker(hands: list):
        kicker = []

        winner = max(hands)
        losers = [hand for hand in hands if hand < winner]
        if not losers: # everyone won or winner the only one in hands
            return None
        max_loser = max(losers)

        # if winner won by a hand level there is no kicker
        if HandParser.HANDS.index(winner.top_hand_name) > HandParser.HANDS.index(max_loser.top_hand_name):
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


# this was just needed constantly within PokerGame
TABLE_DICT = {0: 0, 3: 1, 4: 2, 5: 3}

# Wrapper around a list of Player objects (used onlly for getting info, not setting; PokerGame is used for manipulating/setting data to players)
# type(self) is used if this class should be baseclassed
class PlayerGroup(list):

    def __init__(self, players: list):
        assert not any([players[i - 1].id == players[i].id for i in range(1, len(players))]) # all names must differ
        assert all([isinstance(player, Player) for player in self]) # every player in list has to be an object derived from Player class (or its baseclass)
        super().__init__(players)

    def __getitem__(self, i):
        if isinstance(i, tuple) and len(i) == 2:
            attr, value = i
            for player in self:
                if player.__getattribute__(attr) == value:
                    return player
        else:
            _return = super().__getitem__(i)
            if isinstance(_return, list):
                return type(self)(_return)
            else:
                return _return

    def __add__(self, other):
        added = super().__add__(other)
        _return = []
        for pl in added:
            if pl not in _return:
                _return.append(pl)
        return type(self)(_return)

    def next_active_player_from(self, index_player):
        assert len(self.get_active_players()) >= 1
        cyc = cycle(self)
        for player in cyc:
            if player == index_player:
                break
        for player in cyc:
            if player.is_active():
                return player

    def previous_active_player_from(self, index_player):
        return self[::-1].next_active_player_from(index_player)

    def get_active_players(self):
        return type(self)([player for player in self if player.is_active()])

    def get_not_folded_players(self):
        return type(self)([player for player in self if not player.is_folded])

    def all_played_turn(self):
        for player in self:
            if not player.played_turn and player.is_active():
                return False
        return True

    def winners(self):
        winner = max(self)
        return type(self)([player for player in self if player.hand == winner.hand])

# Game is made so that it is controled from input function, where the Game logic from this object must be combined
# in private out if list or tuple is passed it means it contains cards
class Player:

    def __init__(self, name: str, money: int):
        # static properties
        self.name = name
        self.id = name # can be changed as to identify a certain player

        # this changes through the game but ?never resets?
        self.money = money

        # this resets every round
        self.cards = ()
        self.hand = None
        self.is_folded = False
        self.is_all_in = False # sets to the round player went all_in
        self.money_given = [0, 0, 0, 0] # for pre-flop, flop, turn, river

        # this resets every turn
        self.played_turn = False

    def __repr__(self):
        return f"Player({self.name}, {self.money})"

    def __str__(self):
        return self.id

    # two players shouldnt share the same name
    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        if self.hand and other.hand:
            return self.hand < other.hand
        print('error')

    def __gt__(self, other):
        if self.hand and other.hand:
            return self.hand > other.hand
        print('error')

    def is_active(self):
        return not self.is_folded and not self.is_all_in


# everything in here returns cards represented as [value_index, suit_index] to public/private outs
# players without money are removed at round.close() and should not be included in any game
# if player's money within a round is 0 he should be all in
class PokerGame:
    # these define how a classmethod public_out will respond with given arguments (important when public_out is overriden)
    # these methods must be overriden to have IO support for the game
    IO_actions = {
    'Dealt Cards': lambda cards: None,
    'New Round': lambda round_index: None,
    'Small Blind': lambda player_id, player_name, given: None,
    'Big Blind': lambda player_id, player_name, given: None,
    'Player Raised': lambda player_id, player_name, raised_by: None,
    'Player Called': lambda player_id, player_name, called: None,
    'Player Checked': lambda player_id, player_name: None,
    'Player Folded': lambda player_id, player_name: None,
    'New Turn': lambda turn_name, table: None,
    'To Call': lambda player_name, player_id, to_call: None,
    'Player Went All-In': lambda player_id, player_name, player_money: None,
    'Declare Unfinished Winner': lambda winner_id, winner_name, won: None,
    'Public Show Cards': lambda player_id, player_name, player_cards: None,
    'Declare Finished Winner': lambda winner_id, winner_name, won, hand_name, hand_base, kicker: None,
    'Player Lost Money': lambda player_id, player_name: None}

    # accepts PlayerGroup as players and big_blinds
    def __init__(self, players: PlayerGroup, big_blind: int):
        self.big_blind = big_blind
        self.players = players # players playing the current round

        self.round = None
        self.rounds_played = 0

        # changes during game, resets every round
        self.button = players[0] if players else None # player that posts big blind (starts with the first one)

    @property
    def all_players(self):
        return self.players if not self.round else self.players + self.round.players

    def on_player_join(self, player):
        if player.money > 0: # safety
            self.players.append(player)
            self.button = player if not self.button else self.button
            return True
        return False

    def on_player_leave(self, player):
        # if round is being played and if player is playing in it (all_ins bugs)
        if self.round and player in self.round.players and player.is_active():
            self.public_out(player.name + "'s Hand is Folded")
            if player == self.round.current_player:
                self.round.process_action(player, 'fold')
                self.round.process_after_input()
            elif player.is_active():
                player.is_folded = True
                if len(self.round.players.get_not_folded_players()) == 1:
                    self.round.process_action(self.round.current_player, 'call')
                    self.round.process_after_input()
        if player in self.players:
            self.players.remove(player)

    def is_ok(self):
        if not 2 <= len(self.players) <= 9:
            return False
        return True

    def new_round(self):
        # round should be None and game should be OK to start another round (external processes should cover this)
        assert self.round is None and self.is_ok()

        self.rounds_played += 1
        self.public_out(round_index = self.rounds_played, _id = 'New Round')
        # set the next player that will be the button
        self.button = self.players[(self.players.index(self.button) + 1) % len(self.players)]

        self.round = self.Round(type(self.players)(self.players), self.button, self)

        # this happens if during the self.round attribute setting the game closes,
        # so this.round sets itself to None, but because this
        # is during its attribute setting it is still defined as round
        if not self.is_ok():
            self.round = None

    class Round:
        __deck = [[value, suit] for suit in range(4) for value in range(13)]

        def __init__(this, players, button, game_ref):
            # reference from this to self. Has to stay, because of public out
            this.self = game_ref
            # a sign that can be toggled from an outside source signaling that round will end after the current round is finished
            this.exit_after_this = False

            this.players = players
            this.button = button

            this.table = []
            this.deck = this.deck_generator()
            this.turn_gen = this.turn_generator()

            this.current_player = this.button

            for player in this.players:
                player.money_given = [0, 0, 0, 0]
                player.is_folded = False
                player.is_all_in = False
                player.played_turn = False

                assert player.money > 0
                player.cards = tuple(next(this.deck) for _ in range(2))
                player.hand = HandParser(list(player.cards))
                this.self.private_out(player, cards = player.cards, _id = 'Dealt Cards')

            previous_player = this.players.previous_active_player_from(this.button)
            this.player_added_to_pot(previous_player, this.self.big_blind // 2)
            this.self.public_out(player_id = previous_player.id, player_name = previous_player.name,
            given = previous_player.money_given[0], _id = 'Small Blind')
            this.player_added_to_pot(this.button, this.self.big_blind)
            this.self.public_out(player_id = this.button.id, player_name = this.button.name,
            given = this.button.money_given[0], _id = 'Big Blind')

            this.process_after_input()

        # deletes itself from game attributes, resets everything and returns whether the game should be continued
        def close(this):
            for player in this.players:
                player.money_given = [0, 0, 0, 0]
                player.is_folded = False
                player.is_all_in = False
                player.played_turn = False
                player.cards = ()
                player.hand = None
                if player.money == 0:
                    this.self.players.remove(player)
                    this.self.public_out(player_name = player.name, player_id = player.id, _id = 'Player Lost Money')

            # if game wasnt scheduled to end after this round from an
            # external source and game is ok to continue, then trigger a new round
            this.self.round = None
            if not this.exit_after_this and this.self.is_ok():
                this.self.new_round()

        # returns a shuffled deck generator
        def deck_generator(this):
            deck = shallowcopy(this.__deck)
            shuffle(deck)
            return (card for card in deck) # returns a generator

        # money other players have to call (or go all_in) to continiue to the next turn
        def get_money_to_call(this):
            return max(player.money_given[TABLE_DICT[len(this.table)]] for player in this.players)

        # returns [a,b,c,d] for pot invested on every turn during round (for pre-flop, flop, turn, river)
        def get_pot_size(this):
            return [sum(player.money_given[i] for player in this.players) for i in range(4)]

        # this is used to see whether round can continue to another turn
        # checks if all active players have given equal amount of money, and those that have gone all in have less money in that those who are active
        def pot_is_equal(this):
            # so max returns 0 or max money_given
            all_ins_money = [player.money_given[TABLE_DICT[len(this.table)]] for player in this.players if player.is_all_in and not player.is_folded] or [0]
            # so the second boolean expression works
            active_money = [player.money_given[TABLE_DICT[len(this.table)]] for player in this.players if player.is_active()] or [float('Inf')]
            return len(set(active_money)) == 1 and active_money[0] >= max(all_ins_money)

        # this is called whenever player puts money in the pot and processes whether he went all-in
        def player_added_to_pot(this, player, money):
            turn_index = TABLE_DICT[len(this.table)]

            if 0 <= money < player.money:
                player.money -= money # subtract player's money
                player.money_given[turn_index] += money # add given money to attribute of money given during this turn

            # if player raises more than he has it is considered as going all in
            else:
                this.self.public_out(player_id = player.id, player_name = player.name, player_money = player.money, _id = 'Player Went All-In')
                player.money_given[turn_index] += player.money
                player.money = 0
                player.is_all_in = True

        # process raise, call or fold and return true or false whether input is valid
        # blinds is set to True only when function is called from Round __init__
        def process_action(this, action):
            action = action.lower()
            if not (action in ['call', 'check', 'fold', 'all in'] or action.startswith('raise ')): # safety
                return False

            turn_index = TABLE_DICT[len(this.table)]
            money_to_call = this.get_money_to_call()
            money_left_to_call = money_to_call - this.current_player.money_given[turn_index]

            # process RAISE (input has to be "raise X", where X is a non negative integer, by which player raises the money_to_call)
            if action.startswith('raise ') and len(action.split()) == 2 and action.split()[1].isdigit() and float(action.split()[1]).is_integer():
                raised_by = int(float(action.split()[1]))

                if raised_by + money_to_call < this.current_player.money:
                    if raised_by < this.self.big_blind: # if player didnt go all-in he should raise more than the BIG_BLIND
                        this.self.public_out(_id = 'Raise Amount Error')
                        return False
                    this.self.public_out(player_id = this.current_player.id,
                    player_name = this.current_player.name, raised = raised_by, _id = 'Player Raised')

                this.player_added_to_pot(this.current_player, money_left_to_call + raised_by)
                this.current_player.played_turn = True
                this.process_after_input()
                return True

            elif action == 'all in':
                this.player_added_to_pot(this.current_player, this.current_player.money)
                this.current_player.played_turn = True
                this.process_after_input()
                return True

            # process CALL (is the same as if player raised the others by 0)
            elif action == 'call':
                call_value = money_left_to_call if money_left_to_call < this.current_player.money else this.current_player.money
                this.self.public_out(player_id = this.current_player.id,
                player_name = this.current_player.name, called = call_value , _id = 'Player Called')
                this.player_added_to_pot(this.current_player, money_left_to_call)
                this.current_player.played_turn = True
                this.process_after_input()
                return True

            # process check if there is no money to call (same as call only for instances when you call 0)
            elif action == 'check' and money_left_to_call == 0:
                this.self.public_out(player_id = this.current_player.id,
                player_name = this.current_player.name, _id = 'Player Checked')
                this.current_player.played_turn = True
                this.process_after_input()
                return True

            # process FOLD
            elif action == 'fold':
                this.self.public_out(player_id = this.current_player.id,
                player_name = this.current_player.name, _id = 'Player Folded')
                this.current_player.is_folded = True
                this.current_player.played_turn = True
                this.process_after_input()
                return True

            # if none of the previous returns initializes input is invalid
            return False

        # resets played_turn and money_in_pot for every player. Initializes new turn based how many cards were on the table
        def turn_generator(this):
            turn_dict = {3: 'FLOP', 4: 'TURN', 5: "RIVER"}

            # For FLOP, TURN, RIVER
            for i in (3, 1, 1):
                new_cards = [next(this.deck) for _ in range(i)]
                for player in this.players:
                    player.played_turn = False
                    player.hand.add(new_cards)

                this.table.extend(new_cards)
                this.self.public_out(turn_name = turn_dict[len(this.table)], table = this.table, _id = 'New Turn')
                yield True

        # This continues the game and is called with player input
        def process_after_input(this):
            # player won, round is over
            if len(this.players.get_not_folded_players()) <= 1:
                this.deal_winnings()
                return this.close()

            # check_required tells this expression whether to end the round without player input or if player input is required, even if not needed
            # if everyone or everyone but one went all in and there is more than one player who hasnt folded input stage is over
            if len(this.players.get_active_players()) <= 1 and this.pot_is_equal() and len(this.players.get_not_folded_players()) >= 2:
                for _ in range(3 - TABLE_DICT[len(this.table)]): # user input not needed, so turns continue within this same function
                    next(this.turn_gen)
                this.deal_winnings()
                return this.close()

            # turn ends if money on the table is equal (all ins are treated differentely) and all players have played their turn (other scenarios were processed before)
            # PlayerGroup.all_played_turn checks if player is_active()
            if this.players.all_played_turn() and this.pot_is_equal():
                if len(this.table) == 5:
                    this.deal_winnings()
                    return this.close()
                else:
                    this.current_player = this.button
                    next(this.turn_gen)

            this.current_player = this.players.next_active_player_from(this.current_player)
            to_call = this.get_money_to_call() - this.current_player.money_given[TABLE_DICT[len(this.table)]]
            this.self.public_out(player_name = this.current_player.name,
            player_id = this.current_player.id, to_call = to_call, _id = 'To Call')

        def deal_winnings(this):
            # if all players leave (safety)
            if len(this.players.get_not_folded_players()) == 0:
                return None

            # if there is one player who has not folded he gets everything
            if len(this.players.get_not_folded_players()) == 1:
                winner = this.players.get_not_folded_players()[0]
                winner.money += sum(this.get_pot_size())
                this.self.public_out(winner_id = winner.id, winner_name = winner.name,
                won = sum(this.get_pot_size()), _id = 'Declare Unfinished Winner')
                return None

            for player in this.players:
                player.stake = sum(player.money_given)

            # arranges players who have gone all in by their pot contribution size (from smallest to largest)
            # player can be all in and folded if he left after going all in and had status is_folded set from outside the round instance
            all_ins_sorted = [player for _, player in sorted([[sum(player.money_given), player] for player in this.players if player.is_all_in and not player.is_folded])]
            not_all_in_active = [player for player in this.players if not (player.is_all_in or player.is_folded)]
            # players from smallest to largest stake in pot (not all_in's stake doesnt matter as long as they are last)
            # subgame means the players who are included in the competition for their bought part of the pot
            sorted_by_subgames = type(this.players)(all_ins_sorted + not_all_in_active)
            # players grouped by their pot contribution (indexes in sorted_by_subgames list)
            grouped_indexes = [0] + [i for i in range(1, len(sorted_by_subgames)) if sorted_by_subgames[i - 1].stake < sorted_by_subgames[i].stake]

            # show players' hands
            for competitor in sorted_by_subgames:
                this.self.public_out(player_id = competitor.id, player_name = competitor.name,
                player_cards = competitor.cards, _id = 'Public Show Cards')

            for i in grouped_indexes:
                subgame_competitors = sorted_by_subgames[i:] # this are the people competing for the part of the pot they bought
                winning_players = subgame_competitors.winners()

                # this is static for the loops bellow
                # (winning players need to split the static money, while taking it out at the same time so the same money doesnt get won multiple times)
                PLAYER_STAKES = [player.stake for player in this.players]
                SUBGAME_STAKE = subgame_competitors[0].stake

                for winning_split in winning_players: # give winnings to players that split the subpot
                    player_winnings = 0
                    for player, PLAYER_STAKE in zip(this.players, PLAYER_STAKES):

                        if 0 < PLAYER_STAKE <= SUBGAME_STAKE:
                            take_home = PLAYER_STAKE / len(winning_players)
                        elif 0 < SUBGAME_STAKE < PLAYER_STAKE:
                            take_home = SUBGAME_STAKE / len(winning_players)
                        else: # if SUBGAME_STAKE == 0 or PLAYER_STAKE == 0, theres nothing to collect
                            continue

                        player_winnings += take_home # winnings are added to the winner (they are added to the money later)
                        player.stake -= take_home # stakes are taken from the player

                    # if players collected any left stakes (winnings) it is added to their money, kickers set, and ou
                    if round(player_winnings):
                        winning_split.money += round(player_winnings)
                        # this block is for public_out
                        # subgame participants are players that you winning_split had to beat to get player_winnings
                        kicker = HandParser.get_kicker([player.hand for player in subgame_competitors])
                        this.self.public_out(winner_id = winning_split.id,
                        winner_name = winning_split.name, won = round(player_winnings),
                        hand_name = winning_split.hand.top_hand_name, hand_base = winning_split.hand.hand_base_cards,
                        kicker = kicker, _id = 'Declare Finished Winner')


    ### the methods from here are meant to be overriden when baseclassing this class and implementing game IO
    # private_out and public_out can implement json files containing json.dumps(kwargs)

    # is called with data that should be forwarded to player
    def private_out(self, player, *args, **kwargs):
        ...
        pass

    # is called with data that should be shared amongst all people participating in game / round
    def public_out(self, *args, **kwargs):
        ...
        pass

    # this is meant to be a helper function to outs, when hand name is constructed (game sends only hand_name and cards from which hand consists to public_out)
    @staticmethod
    def hand_repr(best_hand_name, best_hand_base, vals_repr=range(13), suits_repr=range(4)):
        status_vals = [vals_repr[best_hand_base[i][0]] for i in range(len(best_hand_base))]
        status_suit = suits_repr[best_hand_base[0][1]]

        if best_hand_name in ['One Pair', 'Three of a Kind', 'Four of a Kind']:
            return f'{best_hand_name} of {status_vals[0]}\'s'
        elif best_hand_name == 'High Card':
            return f'High Card {status_vals[0]}'
        elif best_hand_name == 'Two Pair':
            return f'Two Pair, {status_vals[0]}\'s and {status_vals[2]}\'s'
        elif best_hand_name == 'Straight':
            return f'{"Straight"} from {status_vals[-1]}\'s to {status_vals[0]}\'s'
        elif best_hand_name == 'Flush':
            return f'Flush of {status_suit} with high card {status_vals[0]}'
        elif best_hand_name == 'Full House':
            return f'Full House {status_vals[0]}\'s over {status_vals[-1]}\'s'
        elif best_hand_name == 'Straight Flush':
            return f'{"Straight Flush"} of {status_suit} from {status_vals[0]}\'s to {status_vals[-1]}\'s'
