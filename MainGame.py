from random import shuffle
from itertools import cycle
from get_gender import get_gender
from parse_hand import HandParser

SUITS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
COLORS = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
CARDS = ['{0} of {1}'.format(suit, color) for color in COLORS for suit in SUITS]
GENDER_TRANS = {'Masculine': 'His', 'Feminine': 'Her', None: 'its'}

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

PLAYERS = ['Nejc', 'Tjasa']

# Wrapper around a list of Player objects (used onlly for getting info, not setting)
class PlayerGroup(list):

    def __getitem__(self, i):
        if isinstance(i, str):
            return [player for player in self if player.name == name][0]
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
        cyc = cycle(self):
        for player in cyc:
            if player == index_player:
                break
        for player in cyc:
            if player.is_active():
                return player

    def get_active_players(self):
        return PlayerGroup([player for player in self if player.is_active()])

    def get_participating_players(self):
        return PlayerGroup([player for player in self.players if player.participating])

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

        # this resets every turn
        self.money_given = [0, 0, 0, 0] # for pre-flop, flop, turn, river
        self.played_turn = False

    def __eq__(self, other):
        return self.name == other.name

    def is_active(self):
        return self.participating and not self.is_folded and not self.is_all_in

    def is_valid_action(self, action):
        if action.lower().startswith('raise') and len(action.split()) == 2 and action.split()[1].isdigit() and float(arg) == int(float(arg)):
            ...
            # need to sort out what raise should be




# meant to be singleton instance class
class PokerGame:

    def __init__(self, players):
        self.players = players
        self.button = players[0] # player that posts big blind (starts with the first one)
        self.deck = []

        # changes during game
        self.table = []

        # resets every turn
        self.money_to_call = [0, 0, 0, 0] # for pre-flop, flop, turn, river
        self.pot = [0, 0, 0, 0] # for pre-flop, flop, turn, river

    # sets new button player and new deck; resets players cards, money_in_pot, folded and all_in status
    # method must be called every beginning of a new round (even first)
    def new_round(self):
        self.button = self.players.next_participating_player_from(self.button)
        self.deck = CARDS.copy()
        shuffle(self.deck)
        for player in self.players:
            player.cards = tuple(self.deck.pop(0) for _ in range(2)) if player.participating else ()
            player.money_in_pot = [0, 0, 0, 0]
            player.is_folded = False
            player.is_all_in = False

            print('{0} cards: {1}\n'.format(player.name, player.cards))

    # resets played_turn and money_in_pot for every player. Must also be called every new turn
    def new_turn(self, turn):
        for player in self:
            player.played_turn = False

    def PRE_FLOP(self):
        # take blinds
        self.pot += self.button.give_money(BIG_BLIND)
        self.pot += self.players.next_active_player_from(self.button).give_money(SMALL_BLIND)

    def FLOP(self):
        self.table.extend([self.deck.pop(0) for _ in range(3)])

    def TURN(self):
        self.table.append(self.deck.pop(0))

    def RIVER(self):
        self.table.append(self.deck.pop(0))

    def repr_table(self, text):
        print(text + ' : ' + ', '.join([card for card in self.table]) + "\n")

    def pot_is_equal(self):
        dic = {0: 0, 3: 1, 4: 2, 5: 3}
        return len(set([player.money_given[dic[len(self.table)]] for player in self.players if player.is_active()])) == 1



if __name__ == '__main__':
    players = PlayerGroup([Player(PLAYER) for PLAYER in PLAYERS])
    game = PokerGame(players)

    # initiate series of rounds
    while True:
        game.new_round()

        # initiate every turn during which players consider actions
        for turn in ["PRE_FLOP", "FLOP", "TURN", "RIVER"]:
            game.__getattribute__(turn)()
            print(f'{turn}: {game.table}\n')

            # player that is right next to button plays first
            current_player = self.next_active_player_from_button(game.button)

            # if all active players have not yet played or someone hasnt called turn continues
            while not players.all_played_turn() or not game.pot_is_equal():

                # check if input action os valid
                while True:
                    action = input()
                    if current_player.is_valid_action(action):
                        break
