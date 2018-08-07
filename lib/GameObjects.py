from random import shuffle
from itertools import cycle
try:
    from HandParse import HandParser
except ModuleNotFoundError:
    from lib.HandParse import HandParser

VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
SUITS = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
CARDS = ['{0} of {1}'.format(value, suit) for suit in SUITS for value in VALUES]

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

    def next_participating_player_from(self, index_player):
        assert len(self.get_participating_players()) >= 1
        cyc = cycle(self)
        for player in cyc:
            if player == index_player:
                break
        for player in cyc:
            if player.participating:
                return player

    def previous_participating_player_from(self, index_player):
        return self[::-1].next_participating_player_from(index_player)

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
        # participation status changes to false if player loses all money or leaves game
        self.money = money
        self.participating = True

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
        return False

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
        self.players = players
        self.big_blind = big_blind

        self.button = players[0] # player that posts big blind (starts with the first one)
        self.rounds_played = 0

        # changes during game, resets every round
        self.deck = []
        self.table = []

    # sets new button player and new deck; resets players cards, money_in_pot, folded and all_in status
    # method must be called every beginning of a new round (even first)
    def new_round(self):
        self.rounds_played += 1
        self.table = []
        self.button = self.players.next_participating_player_from(self.button)
        self.deck = CARDS.copy()
        shuffle(self.deck)

        self.public_out(round_index = self.rounds_played, _id = 'New Round')
        for player in self.players:
            player.cards = tuple(self.deck.pop(0) for _ in range(2)) if player.participating else ()
            player.money_given = [0, 0, 0, 0]
            player.stake = 0
            player.is_folded = False
            player.is_all_in = False
            player.participating = False if player.money == 0 else True # this is checked at deal winnings or fold
            player.private_out(cards = player.cards, _id = 'Dealt Cards')

    # resets played_turn and money_in_pot for every player. Must also be called every new turn
    def new_turn(self, turn):
        # PRE-FLOP
        if turn == "PRE-FLOP":
            # take blinds
            self.process_action(self.players.next_active_player_from(self.button), f"RAISE {self.big_blind // 2}")
            self.public_out(player = self.players.previous_active_player_from(self.button).name, _id = 'Small Blind')
            self.process_action(self.button, f"RAISE {self.big_blind // 2}") # BIG_BLIND = SMALL_BLIND raised by SMALL_BLIND
            self.public_out(player = self.button.name, _id = 'Big Blind')

        # FLOP
        elif turn == "FLOP":
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

    # adds player to players from an external source
    def add_player(self, player):
        self.players.append(player)

    # removes player from players from an external source
    def remove_player(self, name):
        for player in self.players:
            if player.name == name:
                self.players.remove(player)

    # set participation status of players without money to 0
    def update_participating_players(self):
        for player in self.players:
            if player.money == 0:
                player.participating = False

    # checks if all active players (not all_in or folded and participating) have given equal amount of money, so called
    def pot_is_equal(self):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        all_ins_money = [player.money_given[dic[len(self.table)]] for player in self.players if player.is_all_in] + [0] # so max returns 0 or max money_given
        active_money = [player.money_given[dic[len(self.table)]] for player in self.players if player.is_active]
        return len(set(active_money)) <= 1 and active_money[0] >= max(all_ins_money)

    # money other players have to call (or go all_in) to continiue to the next turn
    def get_money_to_call(self):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        return max(player.money_given[dic[len(self.table)]] for player in self.players)

    # returns [a,b,c,d] for pot invested on every turn during round (for pre-flop, flop, turn, river)
    def get_pot_size(self):
        return [sum(player.money_given[i] for player in self.players.get_participating_players()) for i in range(4)]

    # process raise, call or fold and return true or false whether input is valid
    def process_action(self, player, action):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        turn_index = dic[len(self.table)]
        money_to_call = self.get_money_to_call()

        # process RAISE (input has to be "raise X", where X is a non negative integer, by which player raises the money_to_call)
        if action.lower().startswith('raise ') and len(action.split()) == 2 and self.isint(action.split()[1]):
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

        elif action.lower() == 'all in':
            return self.process_action(player, "raise " + str(player.money))

        # process CALL (is the same as if player raised the others by 0)
        elif action.lower() == 'call':
            return self.process_action(player, "raise 0")

        # process check if there is no money to call (same as call only for instances when you call 0)
    elif action.lower() == 'check' and money_to_call - player.money_given[turn_index] == 0:
            return self.process_action(player, "raise 0")

        # process FOLD
        elif action.lower() == 'fold':
            player.is_folded = True
            player.played_turn = True
            return True

        actions = {'show money': lambda: player.private_out(player_money = player.money, _id = 'Show Money')}
        if action.lower() in actions:
            actions[action.lower()]()
            return False

        # if none of the previous returns initializes input is invalid
        return False

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
                        self.public_out(winner = winning_split.name,  won = player_winnings, winner_hand = winning_hand_name, _id = 'Declare Finished Winner')

            # remove hands of players with lower stakes, as they are not competing in the same stake range (they already collected their bet equivalence if won)
            player_hands.remove([player_hand for player_hand in player_hands if player_hand.name == stayed_in.name][0])

        self.update_participating_players()

    @staticmethod
    def isint(string):
        return string.isdigit() and float(string) == int(float(string))

    ### methods from here on should be overriden when baseclassing this class

    # this should be overriden when implementing a game IO
    @classmethod
    def public_out(cls, *args, **kwargs):
        ...
        pass
