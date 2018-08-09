from random import shuffle
from itertools import cycle
try:
    from HandParse import HandParser
except ModuleNotFoundError:
    from lib.HandParse import HandParser

VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
SUITS = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
CARDS = ['{0} of {1}'.format(value, suit) for suit in SUITS for value in VALUES]

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
class PlayerGroup(list):

    def __init__(self, l):
        assert not any([l[i - 1].name == l[i].name for i in range(1, len(l))]) # all names must differ
        super().__init__(l)

    def __getitem__(self, i):
        if isinstance(i, str):
            return [player for player in self if player.name == i][0]
        else:
            _return = super().__getitem__(i)
            if isinstance(_return, list):
                return PlayerGroup(_return)
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

    def get_active_players(self):
        return PlayerGroup([player for player in self if player.is_active()])

    def get_participating_players(self):
        return PlayerGroup([player for player in self if player.participating])

    def get_not_folded_players(self):
        return PlayerGroup([player for player in self if not player.is_folded and player.participating])

    def all_played_turn(self):
        for player in self:
            if not player.played_turn and player.is_active():
                return False
        return True


# in private out if list or tuple is passed it means it contains cards
class Player:
    IO_actions = {
    'Dealt Cards': lambda kwargs: None,
    'Show Money': lambda kwargs: None}

    def __init__(self, name, money):
        # static properties
        self.name = name

        # this changes through the game but never resets
        self.money = money
        self.left_game = False # signals that player should be removed from players by the end of the turn
        self.participating = True # participation status changes to false if player loses all money or chooses to not participate while still in the game

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

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return True

    def __gt__(self, other):
        return True

    def __bool__(self):
        return self.participating

    def is_active(self):
        return self.participating and not self.is_folded and not self.is_all_in

    ### the methods from here are meant to be overriden when baseclassing this class (are here just so it makes sense what PokerGame object calls)

    # private self-player see only text display (should be overriden when implementing game IO)
    def private_out(self, *args, **kwargs):
        ...
        pass


# in public out if an list or tuple is passed it means it contains cards
class PokerGame:
    # these define how a classmethod public_out will respond with given arguments (important when public_out is overriden)
    # these methods must be overriden to have IO support for the game
    IO_actions = {
    'New Round': lambda kwargs: None,
    'Small Blind': lambda kwargs: None,
    'Big Blind': lambda kwargs: None,
    'New Turn': lambda kwargs: None,
    'Player Went All-In': lambda kwargs: None,
    'Declare Unfinished Winner': lambda kwargs: None,
    'Declare Finished Winner': lambda kwargs: None,
    'Public Show Cards': lambda kwargs: None}

    # accepts PlayerGroup as players and big_blinds
    def __init__(self, players, big_blind):
        self.on_standby = False

        self.big_blind = big_blind
        self.players = players # players playing the current round
        self.new_players = [] # players that will be added by the rounds end

        self.rounds_played = 0

        # changes during game, resets every round
        self.button = players[0] # player that posts big blind (starts with the first one)
        self.deck = []
        self.table = []

        self.current_player = None # player whose turn it is

    def is_ok(self):
        self.update_participating_players()
        if not 2 <= len(self.players.get_participating_players()) <= 9:
            return False
        return True

    def get_player_by_attr(self, attr, value):
        for player in self.players + self.new_players:
            if player.__getattribute__(attr) == value:
                return player

    # set participation status of players without money to 0
    def update_participating_players(self):
        for player in self.players + self.new_players:
            if player.money == 0:
                player.participating = False

    def update_players_in_game(self):
        self.players.extend(self.new_players)
        for player in self.players:
            if player.left_game:
                self.players.remove(player)

    # money other players have to call (or go all_in) to continiue to the next turn
    def get_money_to_call(self):
        return max(player.money_given[TABLE_DICT[len(self.table)]] for player in self.players)

    # returns [a,b,c,d] for pot invested on every turn during round (for pre-flop, flop, turn, river)
    def get_pot_size(self):
        return [sum(player.money_given[i] for player in self.players) for i in range(4)]

    # this is used to see whether round can continue to another turn
    # checks if all active players have given equal amount of money, and those that have gone all in have less money in that those who are active
    def pot_is_equal(self):
        all_ins_money = [player.money_given[TABLE_DICT[len(self.table)]] for player in self.players if player.is_all_in] or [0] # so max returns 0 or max money_given
        active_money = [player.money_given[TABLE_DICT[len(self.table)]] for player in self.players if player.is_active()] or [float('Inf')] # so the second boolean expression works
        return len(set(active_money)) == 1 and active_money[0] >= max(all_ins_money)

    # sets new button player and new deck; resets players cards, money_in_pot, folded and all_in status
    # method must be called every beginning of a new round (even first)
    def new_round(self):
        self.rounds_played += 1
        self.table = []
        self.deck = CARDS.copy()
        shuffle(self.deck)

        self.public_out(round_index = self.rounds_played, _id = 'New Round')
        for player in self.players:
            player.participating = False if player.money == 0 else True # this is checked at deal winnings or fold
            player.cards = tuple(self.deck.pop(0) for _ in range(2)) if player.participating else ()
            player.money_given, player.stake = [0, 0, 0, 0], 0
            player.played_turn = False
            player.is_folded = False
            player.is_all_in = False
            player.private_out(cards = player.cards, _id = 'Dealt Cards')

        self.button = self.players.next_active_player_from(self.button)
        self.current_player = self.players.next_active_player_from(self.button)

        prev_player = self.players.previous_active_player_from(self.button)
        self.process_action(prev_player, f"RAISE {self.big_blind // 2}")
        prev_player.played_turn = False
        self.public_out(player = prev_player.name, _id = 'Small Blind')
        self.process_action(self.button, f"RAISE {self.big_blind // 2}") # BIG_BLIND = SMALL_BLIND raised by SMALL_BLIND
        self.button.played_turn = False
        self.public_out(player = self.button.name, _id = 'Big Blind')

        to_call = self.get_money_to_call() - self.current_player.money_given[TABLE_DICT[len(self.table)]]
        to_call_str = str(to_call) + " to call" if to_call != 0 else ''
        self.public_out(self.current_player.name + "\n" + to_call_str)

    # resets played_turn and money_in_pot for every player. Initializes new turn based how many cards were on the table
    def new_turn(self, turn=None):
        turn = {0: 'FLOP', 3: 'TURN', 4: "RIVER"}[len(self.table)]

        # FLOP
        if turn == "FLOP":
            self.table.extend([self.deck.pop(0) for _ in range(3)])

        # TURN
        elif turn == "TURN" :
            self.table.append(self.deck.pop(0))

        # RIVER
        elif turn == "RIVER":
            self.table.append(self.deck.pop(0))

        for player in self.players:
            player.played_turn = False

        self.public_out(turn_name = turn, table = self.table, _id = 'New Turn')

    # process raise, call or fold and return true or false whether input is valid
    def process_action(self, player, action):
        action = action.lower()
        if not (action in ['call', 'check', 'fold', 'all in'] or action.startswith('raise ')):
            return False

        turn_index = TABLE_DICT[len(self.table)]
        money_to_call = self.get_money_to_call()

        # process RAISE (input has to be "raise X", where X is a non negative integer, by which player raises the money_to_call)
        if action.startswith('raise ') and len(action.split()) == 2 and self.isint(action.split()[1]):
            raised_by = int(float(action.split()[1]))

            # money by which player raised + money left to call  - money already given this turn < all the money player has left
            if 0 <= raised_by + money_to_call - player.money_given[turn_index] < player.money:
                player.money -= money_to_call + raised_by - player.money_given[turn_index] # subtract player's raised money
                player.money_given[turn_index] = money_to_call + raised_by # add given money to attribute (this is important with deal_winnings)
                player.played_turn = True

            # if player raises more than he has it is considered as going all in
            else:
                self.public_out(player = player.name, player_money = player.money, _id = 'Player Went All-In')
                player.is_all_in = True
                player.money_given[turn_index] += player.money
                player.money = 0

            return True

        elif action == 'all in':
            return self.process_action(player, "raise " + str(player.money))

        # process CALL (is the same as if player raised the others by 0)
        elif action == 'call':
            return self.process_action(player, "raise 0")

        # process check if there is no money to call (same as call only for instances when you call 0)
        elif action == 'check' and money_to_call - player.money_given[turn_index] == 0:
            return self.process_action(player, "raise 0")

        # process FOLD
        elif action == 'fold':
            player.is_folded = True
            player.played_turn = True
            return True

        # if none of the previous returns initializes input is invalid
        return False

    # This continues the game and is called with player input
    # this function speculates that amount of participating players in game is adequate, outer functions should deal with that
    def process_after_input(self):

        # player won, round is over
        if len(self.players.get_not_folded_players()) == 1:
            self.deal_winnings()
            return "End Round"

        # if everyone or everyone but one went all in and there is more than one player who hasnt folded input stage is over
        if len(self.players.get_active_players()) <= 1 and self.pot_is_equal() and len(self.players.get_not_folded_players()) >= 2:
            for _ in range(3 - TABLE_DICT[len(self.table)]): # user input not needed, so turns continue within this same function
                self.new_turn()
            self.deal_winnings()
            return "End Round"

        # turn ends if money on the table is equal (all ins are treated differentely) and all players have played their turn (other scenarios were processed before)
        if self.players.all_played_turn() and self.pot_is_equal():
            if len(self.table) == 5:
                self.deal_winnings()
                return "End Round"
            else:
                self.current_player = self.button
                self.new_turn()

        self.current_player = self.players.next_active_player_from(self.current_player)
        to_call = self.get_money_to_call() - self.current_player.money_given[TABLE_DICT[len(self.table)]]
        to_call_str = str(to_call) + " to call" if to_call != 0 else ''
        self.public_out(self.current_player.name + "\n" + to_call_str)
        return None


    def deal_winnings(self):
        # this matters only for later use of this function
        for player in self.players:
            player.stake = sum(player.money_given)

        # if there is one player who has not folded he gets everything
        if len(self.players.get_not_folded_players()) == 1:
            winner = self.players.get_not_folded_players()[0]
            winner.money += sum(self.get_pot_size())
            self.update_participating_players()

            self.public_out(winner = winner.name, won = sum(self.get_pot_size()), _id = 'Declare Unfinished Winner')
            return None

        # arranges players who have gone all in by their pot contribution size (from smallest to largest)
        all_ins_sorted = [player for _, player in sorted([[sum(player.money_given), player] for player in self.players if player.is_all_in])]
        not_all_in_active = [player for player in self.players if player.is_active()] # is_active covers people not all_in, participating and not folded
        active_and_sorted_all_ins = PlayerGroup(all_ins_sorted + not_all_in_active) # players from smallest to largest stake in pot (not all_in players' stake doesnt matter as long as they are last)
        participating_players = self.players.get_participating_players() # all participating players, so even those who folded

        # hand objects of winning players' hands
        player_hands = [Hand(player.name, list(player.cards) + self.table) for player in active_and_sorted_all_ins]
        static_hands = player_hands.copy()

        # show players' hands
        for stayed_in in active_and_sorted_all_ins:
            self.public_out(player = stayed_in.name, player_cards = stayed_in.cards, _id = 'Public Show Cards')

        for stayed_in in active_and_sorted_all_ins: # here the loop order (sorting of active_and_sorted_all_ins) is mucho importante
            winning_player_names = Hand.max(player_hands)
            winning_hand_name = [hand for hand in player_hands if hand.name in winning_player_names][0].best_hand_repr() # name of the winning hand
            winning_players = PlayerGroup([active_and_sorted_all_ins[player_name] for player_name in winning_player_names])

            if stayed_in.name in winning_player_names:
                # this is static for the loops bellow (winning players need to split the static money, while taking it out at the same time so the same money doesnt get won multiple times)
                PLAYER_STAKES = [player.stake for player in participating_players]
                STAYED_IN_STAKE = stayed_in.stake

                for winning_split in winning_players: # give winnings to players that split the subpot
                    player_winnings = 0
                    for player, PLAYER_STAKE in zip(participating_players, PLAYER_STAKES):

                        if 0 < PLAYER_STAKE <= STAYED_IN_STAKE: # it all depends on stayed in as he has the lowest stakes, the rest will collect later
                            player_winnings += PLAYER_STAKE // len(winning_players)
                            winning_split.money += PLAYER_STAKE // len(winning_players) # still working with fixed copy
                            player.stake -= PLAYER_STAKE // len(winning_players) # money updates

                        elif 0 < STAYED_IN_STAKE < PLAYER_STAKE:
                            player_winnings += STAYED_IN_STAKE // len(winning_players)
                            winning_split.money += STAYED_IN_STAKE // len(winning_players)
                            player.stake -= STAYED_IN_STAKE // len(winning_players)

                    # if players collected any left stakes (winnings) it is logged
                    if player_winnings:
                        subgame_participants = [player.name for player in active_and_sorted_all_ins if player.stake >= winning_split.stake] # subgame participants
                        _kicker = Hand.get_kicker([hand for hand in static_hands if hand.name in subgame_participants])
                        self.public_out(winner = winning_split.name,  won = player_winnings, winner_hand = winning_hand_name, kicker = _kicker, _id = 'Declare Finished Winner')

            # remove hands of players with lower stakes, as they are not competing in the same stake range (they already collected their bet equivalence if won)
            player_hands = [player_hand for player_hand in player_hands if player_hand.name != stayed_in.name]

        # this is done when the round ends and deal winnings is always the last function called before the round ends
        self.update_participating_players()
        self.update_players_in_game()


    @staticmethod
    def isint(string):
        return string.isdigit() and float(string) == int(float(string))

    ### methods from here on should be overriden when baseclassing this class

    # this should be overriden when implementing a game IO
    @classmethod
    def public_out(cls, *args, **kwargs):
        ...
        pass
