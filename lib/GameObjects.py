from numpy.random import shuffle
from itertools import cycle
try:
    from HandParse import HandParser
except ModuleNotFoundError:
    from lib.HandParse import HandParser

# this was just needed constantly within PokerGame
TABLE_DICT = {0: 0, 3: 1, 4: 2, 5: 3}

# player Hand
class Hand(HandParser):
    def __init__(self, name, hand):
        super().__init__(hand)
        self.name = name

    @staticmethod
    def max(hands: list) -> list:
        winner = max(hands)
        return [hand.name for hand in hands if hand == winner]

# Wrapper around a list of Player objects (used onlly for getting info, not setting; PokerGame is used for manipulating/setting data to players)
# type(self) is used if this class should be baseclassed
class PlayerGroup(list):

    def __init__(self, players: list):
        assert not any([players[i - 1].name == players[i].name for i in range(1, len(players))]) # all names must differ
        super().__init__(players)

    def __getitem__(self, i):
        if isinstance(i, str):
            return [player for player in self if player.name == i][0]
        else:
            _return = super().__getitem__(i)
            if isinstance(_return, list):
                return type(self)(_return)
            else:
                return _return

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

    def next_player_with_money_from(self, index_player):
        assert len(self.get_players_with_money()) >= 1
        cyc = cycle(self)
        for player in cyc:
            if player == index_player:
                break
        for player in cyc:
            if player.money > 0:
                return player

    def get_player_by_attr(self, attr, value):
        for player in self:
            if player.__getattribute__(attr) == value:
                return player

    def get_active_players(self):
        return type(self)([player for player in self if player.is_active()])

    def get_players_with_money(self):
        return type(self)([player for player in self if player.money > 0])

    def get_not_folded_players(self):
        return type(self)([player for player in self if not player.is_folded])

    def all_played_turn(self):
        for player in self:
            if not player.played_turn and player.is_active():
                return False
        return True

# Game is made so that it is controled from input function, where the Game logic from this object must be combined
# in private out if list or tuple is passed it means it contains cards
class Player:

    def __init__(self, name: str, money: int):
        # static properties
        self.name = name

        # this changes through the game but never resets
        self.money = money

        # this resets every round
        self.cards = ()
        self.is_folded = False
        self.is_all_in = False # sets to the round player went all_in
        self.money_given = [0, 0, 0, 0] # for pre-flop, flop, turn, river
        self.stake = 0 # its just a sum of money_given needed when processing winners

        # this resets every turn
        self.played_turn = False

    def __repr__(self):
        return f"Player({self.name})"

    def __str__(self):
        return self.name

    # two players shouldnt share the same name
    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return True

    def is_active(self):
        return self.money > 0 and not self.is_folded and not self.is_all_in

# everything in here returns cards represented as [value_index, suit_index] to public/private outs
class PokerGame:
    # these define how a classmethod public_out will respond with given arguments (important when public_out is overriden)
    # these methods must be overriden to have IO support for the game
    IO_actions = {
    'Dealt Cards': lambda kwargs: None,
    'New Round': lambda kwargs: None,
    'Small Blind': lambda kwargs: None,
    'Big Blind': lambda kwargs: None,
    'New Turn': lambda kwargs: None,
    'Player Went All-In': lambda kwargs: None,
    'Declare Unfinished Winner': lambda kwargs: None,
    'Declare Finished Winner': lambda kwargs: None,
    'Public Show Cards': lambda kwargs: None}
    # this shouldn't be changed
    __deck = [[value, suit] for suit in range(4) for value in range(12)]

    # accepts PlayerGroup as players and big_blinds
    def __init__(self, players: PlayerGroup, big_blind: int):
        self.big_blind = big_blind
        self.players = players # players playing the current round

        self.round = None
        self.rounds_played = 0

        # changes during game, resets every round
        self.button = players[0] # player that posts big blind (starts with the first one)

    @property
    def deck(self):
        shuffle(self.__deck)
        return (card for card in self.__deck) # returns a generator

    def on_player_join(self, player):
        self.players.append(player)

    def on_player_leave(self, player):
        if self.round and player in self.round.players and player.is_active(): # if round is being played and if player is playing in it (all_ins bugs)
            self.public_out(player.name + "'s Hand is Folded")
            if player == self.round.current_player:
                self.round.process_action(player, 'fold')
                self.round.process_after_input()
            elif player.is_active():
                player.is_folded = True
                if len(self.round.players.get_not_folded_players()) == 1:
                    self.round.process_action(self.round.current_player, 'call')
                    self.round.process_after_input()
        self.players.remove(player)

    def is_ok(self):
        if not 2 <= len(self.players.get_players_with_money()) <= 9:
            return False
        return True

    def new_round(self):
        assert self.round is None and self.is_ok() # round should be None and game should be OK to start another round (external processes should cover this)

        self.rounds_played += 1
        self.public_out(round_index = self.rounds_played, _id = 'New Round')
        self.button = self.players.next_player_with_money_from(self.button) # players from which the button is set should be those that round is going to include

        # if your money > 0 you are playing in the round
        self.round = self.Round(type(self.players)(self.players.get_players_with_money()), self.button, self)

    class Round:

        def __init__(this, players, button, game_ref):
            this.self = game_ref # reference from this to self. Has to stay, because of public out
            this.exit_after_this = False

            this.players = players
            this.button = button

            this.table = []
            this.deck = this.self.deck
            this.turn_gen = this.turn_generator()

            this.current_player = this.button

            for player in this.players:
                player.money_given, player.stake = [0, 0, 0, 0], 0
                player.is_folded = False
                player.is_all_in = False
                player.played_turn = False
                player.stake = 0

                assert player.money > 0
                player.cards = tuple(next(this.deck) for _ in range(2))
                this.self.private_out(player, cards = player.cards, _id = 'Dealt Cards')

            # set blinds in a lazy way
            previous_player = this.players.previous_active_player_from(this.button)
            this.process_action(previous_player, f"RAISE {this.self.big_blind // 2}")
            previous_player.played_turn = False
            this.self.public_out(player = previous_player.name, _id = 'Small Blind')
            this.process_action(this.button, f"RAISE {this.self.big_blind // 2}") # BIG_BLIND = SMALL_BLIND raised by SMALL_BLIND
            this.button.played_turn = False
            this.self.public_out(player = this.button.name, _id = 'Big Blind')

            this.process_after_input()

        # deletes itself from game attributes, resets everything and returns whether the game should be continued
        def close(this):
            this.self.round = None
            for player in this.players:
                player.money_given, player.stake = [0, 0, 0, 0], 0
                player.is_folded = False
                player.is_all_in = False
                player.played_turn = False
                player.stake = 0

            # 0 - new round should not begin; 1 - new round should begin
            return int(not this.exit_after_this)

        # money other players have to call (or go all_in) to continiue to the next turn
        def get_money_to_call(this):
            return max(player.money_given[TABLE_DICT[len(this.table)]] for player in this.players)

        # returns [a,b,c,d] for pot invested on every turn during round (for pre-flop, flop, turn, river)
        def get_pot_size(this):
            return [sum(player.money_given[i] for player in this.players) for i in range(4)]

        # this is used to see whether round can continue to another turn
        # checks if all active players have given equal amount of money, and those that have gone all in have less money in that those who are active
        def pot_is_equal(this):
            all_ins_money = [player.money_given[TABLE_DICT[len(this.table)]] for player in this.players if player.is_all_in] or [0] # so max returns 0 or max money_given
            active_money = [player.money_given[TABLE_DICT[len(this.table)]] for player in this.players if player.is_active()] or [float('Inf')] # so the second boolean expression works
            return len(set(active_money)) == 1 and active_money[0] >= max(all_ins_money)

        # resets played_turn and money_in_pot for every player. Initializes new turn based how many cards were on the table
        def turn_generator(this):
            turn_dict = {3: 'FLOP', 4: 'TURN', 5: "RIVER"}

            # For FLOP, TURN, RIVER
            for i in (3, 1, 1):
                for player in this.players:
                    player.played_turn = False

                this.table.extend([next(this.deck) for _ in range(i)])
                this.self.public_out(turn_name = turn_dict[len(this.table)], table = this.table, _id = 'New Turn')
                yield True

        # process raise, call or fold and return true or false whether input is valid
        def process_action(this, player, action):
            action = action.lower()
            if not (action in ['call', 'check', 'fold', 'all in'] or action.startswith('raise ')):
                return False

            turn_index = TABLE_DICT[len(this.table)]
            money_to_call = this.get_money_to_call()

            # process RAISE (input has to be "raise X", where X is a non negative integer, by which player raises the money_to_call)
            if action.startswith('raise ') and len(action.split()) == 2 and this.isint(action.split()[1]):
                raised_by = int(float(action.split()[1]))

                # money by which player raised + money left to call  - money already given this turn < all the money player has left
                if 0 <= raised_by + money_to_call - player.money_given[turn_index] < player.money:
                    player.money -= money_to_call + raised_by - player.money_given[turn_index] # subtract player's raised money
                    player.money_given[turn_index] = money_to_call + raised_by # add given money to attribute (this is important with deal_winnings)
                    player.played_turn = True

                # if player raises more than he has it is considered as going all in
                else:
                    this.self.public_out(player = player.name, player_money = player.money, _id = 'Player Went All-In')
                    player.money_given[turn_index] += player.money
                    player.money = 0
                    player.played_turn = True # doesnt matter as player will not be asked for input again (but it should be noted)
                    player.is_all_in = True

                return True

            elif action == 'all in':
                return this.process_action(player, "raise " + str(player.money))

            # process CALL (is the same as if player raised the others by 0)
            elif action == 'call':
                return this.process_action(player, "raise 0")

            # process check if there is no money to call (same as call only for instances when you call 0)
            elif action == 'check' and money_to_call - player.money_given[turn_index] == 0:
                return this.process_action(player, "raise 0")

            # process FOLD
            elif action == 'fold':
                player.is_folded = True
                player.played_turn = True
                return True

            # if none of the previous returns initializes input is invalid
            return False

        # This continues the game and is called with player input
        def process_after_input(this):

            # player won, round is over
            if len(this.players.get_not_folded_players()) <= 1:
                this.deal_winnings()
                return this.close()

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
            to_call_str = str(to_call) + " to call" if to_call != 0 else ''
            this.self.public_out(this.current_player.name + "\n" + to_call_str)
            return None


        def deal_winnings(this):

            # if all players leave
            if len(this.players.get_not_folded_players()) == 0:
                return None

            # if there is one player who has not folded he gets everything
            if len(this.players.get_not_folded_players()) == 1:
                winner = this.players.get_not_folded_players()[0]
                winner.money += sum(this.get_pot_size())
                this.self.public_out(winner = winner.name, won = sum(this.get_pot_size()), _id = 'Declare Unfinished Winner')
                return None

            # this matters only for later use of this function
            for player in this.players:
                player.stake = sum(player.money_given)

            # arranges players who have gone all in by their pot contribution size (from smallest to largest)
            all_ins_sorted = [player for _, player in sorted([[sum(player.money_given), player] for player in this.players if player.is_all_in])]
            not_all_in_active = [player for player in this.players if player.is_active()] # is_active covers people not all_in, wwith money and not folded
            # players from smallest to largest stake in pot (not all_in's stake doesnt matter as long as they are last)
            active_and_sorted_all_ins = type(this.players)(all_ins_sorted + not_all_in_active)

            # hand objects of winning players' hands
            player_hands = [Hand(player.name, list(player.cards) + this.table) for player in active_and_sorted_all_ins]
            static_hands = player_hands.copy()

            # show players' hands
            for stayed_in in active_and_sorted_all_ins:
                this.self.public_out(player = stayed_in.name, player_cards = stayed_in.cards, _id = 'Public Show Cards')

            for stayed_in in active_and_sorted_all_ins: # here the loop order (sorting of active_and_sorted_all_ins) is mucho importante
                winning_player_names = Hand.max(player_hands)
                winning_players = type(this.players)([active_and_sorted_all_ins[player_name] for player_name in winning_player_names])

                if stayed_in.name in winning_player_names:
                    # this is static for the loops bellow (winning players need to split the static money, while taking it out at the same time so the same money doesnt get won multiple times)
                    PLAYER_STAKES = [player.stake for player in this.players]
                    STAYED_IN_STAKE = stayed_in.stake

                    for winning_split in winning_players: # give winnings to players that split the subpot
                        player_winnings = 0
                        for player, PLAYER_STAKE in zip(this.players, PLAYER_STAKES):

                            if 0 < PLAYER_STAKE <= STAYED_IN_STAKE: # it all depends on stayed in as he has the lowest stakes, the rest will collect later
                                take_home = PLAYER_STAKE / len(winning_players)
                            elif 0 < STAYED_IN_STAKE < PLAYER_STAKE:
                                take_home = STAYED_IN_STAKE / len(winning_players)
                            else: # if STAYED_IN_STAKE == 0 or PLAYER_STAKE == 0, theres nothing to collect
                                continue

                            player_winnings += take_home # winnings are added to the winner (they are added to the money later)
                            player.stake -= take_home # stakes are taken from the player

                        # if players collected any left stakes (winnings) it is added to their money, kickers set, and ou
                        if player_winnings:
                            winning_split.money += round(player_winnings)

                            # this block is for public_out
                            subgame_participants = [player.name for player in active_and_sorted_all_ins if player.stake >= winning_split.stake] # subgame participants
                            kicker = Hand.get_kicker([hand for hand in static_hands if hand.name in subgame_participants])
                            winner_hand = [hand for hand in player_hands if hand.name == winning_split.name][0]
                            this.self.public_out(winner = winning_split.name, won = player_winnings, hand_name = winner_hand.best_hand_name,
                            hand_base = winner_hand.hand_base, kicker = kicker, _id = 'Declare Finished Winner')

                # remove hands of players with lower stakes, as they are not competing in the same stake range (they already collected their bet equivalence if won)
                player_hands = [player_hand for player_hand in player_hands if player_hand.name != stayed_in.name]


        @staticmethod
        def isint(string):
            return string.isdigit() and float(string) == int(float(string))


    ### the methods from here are meant to be overriden when baseclassing this class and implementing game IO

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
