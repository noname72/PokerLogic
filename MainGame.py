from random import shuffle
from itertools import cycle
from get_gender import get_gender
from parse_hand import HandParser, Hand

SUITS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
COLORS = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
CARDS = ['{0} of {1}'.format(suit, color) for color in COLORS for suit in SUITS]
GENDER_TRANS = {'Masculine': 'His', 'Feminine': 'Her', None: 'its'}

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

PLAYERS = ['Nejc', 'Tjasa', 'Gorazd']

# Wrapper around a list of Player objects (used onlly for getting info, not setting; PokerGame is used for manipulating/setting data to players)
class PlayerGroup(list):

    def __init__(self, l):
        assert not any([l[i - 1].name == l[i].name for i in range(1, len(l))]) # all names must differ
        super().__init__(l)

    def __getitem__(self, i):
        if isinstance(i, str):
            return [player for player in self if player.name == i][0]
        else:
            return super().__getitem__(i)

    def next_participating_player_from(self, index_player):
        assert len(self.get_participating_players()) >= 2
        cyc = cycle(self)
        for player in cyc:
            if player == index_player:
                break
        for player in cyc:
            if player.participating:
                return player

    def next_active_player_from(self, index_player):
        assert len(self.get_active_players()) >= 2
        cyc = cycle(self)
        for player in cyc:
            if player == index_player:
                break
        for player in cyc:
            if player.is_active():
                return player

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

class Player:

    def __init__(self, name):
        # static properties
        self.name = name
        self.gender = get_gender(self.name)

        # this changes through the game but never resets
        # participation status changes to false if player loses all money or leaves game
        self.money = STARTING_MONEY
        self.participating = True

        # this resets every round
        self.cards = ()
        self.is_folded = False
        self.is_all_in = False # sets to the round player went all_in
        self.money_given = [0, 0, 0, 0] # for pre-flop, flop, turn, river

        # this resets every turn
        self.played_turn = False

    def __repr__(self):
        return f"Player({self.name})"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    # private self-player see only text display (can be overriden by subclassing)
    def private_out(self, text):
        print(text)

    def is_active(self):
        return self.participating and not self.is_folded and not self.is_all_in


# meant to be a singleton instance class
class PokerGame:

    def __init__(self, players):
        self.players = players
        self.button = players[0] # player that posts big blind (starts with the first one)
        self.rounds_played = 0

        # changes during game, resets every round
        self.deck = []
        self.table = []

        # resets every turn
        self.pot = [0, 0, 0, 0] # for pre-flop, flop, turn, river

    # sets new button player and new deck; resets players cards, money_in_pot, folded and all_in status
    # method must be called every beginning of a new round (even first)
    def new_round(self):
        self.rounds_played += 1
        self.pot = [0, 0, 0, 0]
        self.table = []
        self.button = self.players.next_participating_player_from(self.button)
        self.deck = CARDS.copy()
        shuffle(self.deck)

        self.public_out(f"\n\n--- Round {self.rounds_played} ---\n\n")
        for player in self.players:
            player.cards = tuple(self.deck.pop(0) for _ in range(2)) if player.participating else ()
            player.money_given = [0, 0, 0, 0]
            player.is_folded = False
            player.is_all_in = False
            if player.money == 0:
                player.participating = False
            player.private_out('{0}\'s cards: {1}'.format(player.name, player.cards))

    # resets played_turn and money_in_pot for every player. Must also be called every new turn
    def new_turn(self, turn):
        # PRE-FLOP
        if turn == "PRE-FLOP":
            # take blinds
            self.process_action(self.players.next_active_player_from(self.button), f"RAISE {SMALL_BLIND}")
            self.public_out(f"\n{self.players.next_active_player_from(self.button)} gave small blind of {SMALL_BLIND}")
            self.process_action(self.button, f"RAISE {SMALL_BLIND}") # BIG_BLIND = SMALL_BLIND raised by SMALL_BLIND
            self.public_out(f"{self.button} gave big blind of {BIG_BLIND}")

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

        self.public_out(f'\n{turn}: {self.table}\n')

    # checks if all active players (not all_in or folded and participating) have given equal amount of money, so called
    def pot_is_equal(self):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        return len(set([player.money_given[dic[len(self.table)]] for player in self.players if player.is_active()])) == 1

    # money other players have to call (or go all_in) to continiue to the next turn
    def get_money_to_call(self):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        return max(player.money_given[dic[len(self.table)]] for player in self.players)

    # process raise, call or fold and return true or false whether input is valid
    def process_action(self, player, action):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        turn_index = dic[len(self.table)]
        money_to_call = self.get_money_to_call()

        # process RAISE (input has to be "raise X", where X is a non negative integer, by which player raises the money_to_call)
        if action.lower().startswith('raise ') and len(action.split()) == 2 and action.split()[1].isdigit() and int(float(action.split()[1])) == float(action.split()[1]) >= 0:
            raised_by = int(float(action.split()[1]))

            # money by which player raised + money left to call  - money already given this turn < all the money player has left
            if 0 <= raised_by + money_to_call - player.money_given[turn_index] < player.money:
                player.money -= money_to_call + raised_by - player.money_given[turn_index] # subtract player's raised money
                player.money_given[turn_index] = money_to_call + raised_by # add given money to attribute (this is important with deal_winnings)
                player.played_turn = True

            # if player raises more than he has it is considered as going all in
            else:
                player.private_out(f"{player.name} went all in with {player.money}")
                player.is_all_in = True
                player.money_given[turn_index] = player.money
                player.money = 0

            return True

        # process CALL (is the same as if player raised the others by 0)
        elif action.lower() == 'call':
            return self.process_action(player, "raise 0")

        # process FOLD
        elif action.lower() == 'fold':
            player.is_folded = True
            player.played_turn = True
            return True

        actions = {'show money': lambda: player.private_out(player.money), 'exit status code 200': lambda: exit()}
        if action in actions:
            actions[action]()
            return False

        # if none of the previous returns initializes input is invalid
        return False

    def deal_winnings(self):
        self.pot = [sum(player.money_given[i] for player in self.players.get_participating_players()) for i in range(4)]
        # if there is one player who has not folded he gets everything
        if len(self.players.get_not_folded_players()) == 1:
            winner = self.players.get_not_folded_players()[0]
            winner.money += sum(self.pot)
            self.public_out(f"{winner} won the pot of {sum(self.pot)}")
            return None

        # arranges players who have gone all in by pot contribution size (from smallest to largest)
        all_ins = [player for player in self.players if player.is_all_in] # players that are all in
        all_in_stakes = [sorted([[player.money_given[i], player] for player in all_ins if player.money_given[i] != 0]) for i in range(4)] # sorted by turns and money given that turn
        sorted_all_ins = []
        for list_players in all_in_stakes:
            for player in list_players:
                if player not in sorted_all_ins:
                    sorted_all_ins.append(player)
                else:
                    sorted_all_ins.remove(player)
                    sorted_all_ins.append(player)

        not_all_in_active = [player for player in self.players if player.is_active()] # is_active covers people not all_in, participating and not folded
        active_and_sorted_all_ins = PlayerGroup(sorted_all_ins + not_all_in_active) # players from smallest to largest stake in pot (not all_in players' stake doesnt matter as long as they are last)
        participating_players = self.players.get_participating_players() # all participating players, so even those who folded

        # hand objects of winning players' hands
        player_hands = [Hand(player.name, list(player.cards) + self.table) for player in active_and_sorted_all_ins]

        for stayed_in in active_and_sorted_all_ins: # here the loop order (sorting of active_and_sorted_all_ins) is mucho importante
            winning_player_names = Hand.max(player_hands)
            winning_hand_name = [hand for hand in player_hands if hand.name in winning_player_names][0].best_hand_repr() # name of the winning hand
            winning_players = PlayerGroup([active_and_sorted_all_ins[player_name] for player_name in winning_player_names])

            if stayed_in.name in winning_player_names:
                participating_players_fixed = participating_players.copy() # this is static, while the real values of part_players.money_given change
                stayed_in_fixed_money = stayed_in.money_given.copy()

                for participating_player, participating_player_fixed in zip(participating_players, participating_players_fixed): # take the winnings from all of the participating_players
                    for i in range(4): # for every turn that money was given split it between players
                        for stayed_in_split in winning_players: # give winnings to players that split the subpot

                            if 0 < participating_player_fixed.money_given[i] <= stayed_in_fixed_money[i]: # it all depends on stayed in as he has the lowest stakes, the rest will collect later
                                self.public_out(f"{stayed_in_split.name} won {participating_player_fixed.money_given[i] // len(winning_players)} with {winning_hand_name}")
                                stayed_in_split.money += participating_player_fixed.money_given[i] // len(winning_players) # still working with fixed copy
                                participating_player.money_given[i] -= participating_player_fixed.money_given[i] // len(winning_players) # money updates

                            elif 0 < stayed_in_fixed_money[i] < participating_player_fixed.money_given[i]:
                                self.public_out(f"{stayed_in_split.name} won {stayed_in.money_given[i] // len(winning_players)} with {winning_hand_name}")
                                stayed_in_split.money += stayed_in.money_given[i] // len(winning_players)
                                participating_player.money_given[i] -= stayed_in.money_given[i] // len(winning_players)

            player_hands.remove([player_hand for player_hand in player_hands if player_hand.name == stayed_in.name][0])

    # public text display for all players in game (can be overriden by subclassing)
    def public_out(self, text):
        print(text)


if __name__ == '__main__':
    players = PlayerGroup([Player(PLAYER) for PLAYER in PLAYERS])
    game = PokerGame(players)

    # initiate series of rounds while there are at least 2 players participating
    while len(players.get_participating_players()) >= 2:
        game.new_round()

        # initiate every turn during which players consider actions
        for turn in ["PRE-FLOP", "FLOP", "TURN", "RIVER"]:
            game.new_turn(turn)

            # player that is right next to button plays first
            current_player = players.next_active_player_from(game.button)

            # if all active players have not yet played or someone hasnt called turn continues (current_player inputs action)
            while not players.all_played_turn() or not game.pot_is_equal():

                # if there is one player left his input doesnt matter
                if len(players.get_active_players()) == 1:
                    break

                # current player inputs action, which gets processed and validated or rejected
                current_player = players.next_active_player_from(current_player)
                while True:
                    action = input(f"{current_player.name}: Raise X, Call or Fold: ")
                    if game.process_action(current_player, action):
                        break

            # everyone but one folded after playing actions so the winner
            if len(players.get_not_folded_players()) == 1:
                break

        # process winners and deal winnings to round winners
        game.deal_winnings()
