from random import shuffle
from get_gender import get_gender

SUITS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
COLORS = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
CARDS = ['{0} of {1}'.format(suit, color) for color in COLORS for suit in SUITS]
GENDER_TRANS = {'Masculine': 'His', 'Feminine': 'Her', None: 'its'}

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

PLAYERS = ['Nejc', 'Tjasa']

# Wrapper around Player object
class PlayerGroup:

    def __init__(self, player_list):
        self.player_list = player_list

    def __getitem__(self, i):
        if isinstance(i, int):
            return self.player_list[i]
        elif isinstance(i, str):
            return [player for player in self.player_list if player.name == name][0]

    def __len__(self):
        return len(self.player_list)

    def __iter__(self):
        for elt in self.player_list:
            yield elt

    def __str__(self):
        return repr(self.player_list)

    def pop(self, i):
        return self.player_list.pop(i)

    def reset_player_status(self):
        for player in self.player_list:
            player.money_in_pot = 0
            player.is_folded = False
            player.is_all_in = False

    def get_participating_players(self):
        return PlayerGroup([player for player in self.player_list if player.is_participating()])

    def money_in_pot_equal(self):
        still_in = self.get_participating_players()
        if len(still_in) >= 2:
            _compare = still_in[0].money_in_pot
            for player in still_in:
                if player.money_in_pot != _compare:
                    return False
            return True
        else:
            print('{0} won the pot'.format(still_in[0].name))
            return still_in[0]

    def all_played_turn(self):
        for player in self.player_list:
            if not player.played_turn and player.is_participating():
                return False
        return True

    # resets played_turn and money_in_pot
    def new_turn(self):
        for player in self.player_list:
            player.played_turn = False
            player.money_in_pot = 0

class Player:

    def __init__(self, name):
        # static properties
        self.name = name
        self.gender = get_gender(self.name)

        # this changes through the game but never resets
        # active status changes to false if player loses all money
        self.money = STARTING_MONEY
        self.active = True

        # this resets every round
        self._cards = ()
        self.is_folded = False
        self.is_all_in = False

        #this resets every turn
        self.money_in_pot = 0
        self.played_turn = False

    def is_participating(self):
        return self.active and not self.is_folded and not self.is_all_in

    def deal_cards(self, cards):
        self._cards = cards
        print('{0} cards: {1}\n'.format(self.name, self._cards))

    def give_blind(self, _blind):
        given_blind = _blind if self.money >= _blind else self.money
        if self.money == given_blind:
            print('Code within give_blind not yet completed')
            self.is_all_in = True
        self.money -= given_blind
        self.money_in_pot += given_blind
        print('{0} gave blind {1}\n'.format(self.name, given_blind))
        return given_blind

    def all_in(self):
        self.money_in_pot += self.money
        self.money = 0
        self.is_all_in = True



class PokerRound:

    def __init__(self, players, button):
        self.deck = CARDS.copy()
        shuffle(self.deck)
        self.table = []

        self.players = players
        self.button = button
        self.pot = 0

        self.players.reset_player_status()
        for player in self.players:
            player.deal_cards(tuple(self.deck.pop(0) for _ in range(2)))

    def the_pre_flop(self):
        # take blinds
        self.pot += self.players[self.button].give_blind(BIG_BLIND)
        self.pot += self.players[(self.button + 1) % len(players)].give_blind(SMALL_BLIND)
        return None
    def the_flop(self):
        self.table.extend([self.deck.pop(0) for _ in range(3)])
        return self.table
    def the_turn(self):
        self.table.append(self.deck.pop(0))
        return self.table
    def the_river(self):
        self.table.append(self.deck.pop(0))
        return self.table

    def is_winner(self, player):
        player.money += self.pot
        self.players.reset_player_status()
        print("{0} has won the pot of {1}".format(player.name, self.pot))

    def repr_table(self, text):
        print(text + ' : ' + ', '.join([card for card in self.table]) + "\n")



if __name__ == '__main__':
    players = PlayerGroup([Player(PLAYER) for PLAYER in PLAYERS])
    button = -1
    button = (button + 1) % len(players)

    while True:
        money_to_call = BIG_BLIND
        round_ = PokerRound(players, button)

        for deal in zip(["PRE-FLOP", "FLOP", "TURN", "RIVER"], [round_.the_pre_flop, round_.the_flop, round_.the_turn, round_.the_river]):
            cards = deal[1]()
            round_.repr_table(deal[0])

            turn = (button + 1) % len(players)
            while not players.money_in_pot_equal() or not players.all_played_turn():

                current_player = players[turn % len(players)]
                while not current_player.is_participating():
                    current_player = players[turn % len(players)]
                    turn += 1

                while True:
                    inp = input('{0}:\n\n'.format(current_player.name))

                    # player raised by inp
                    if inp.isdigit():
                        if int(inp) + money_to_call - current_player.money_in_pot <= current_player.money and int(inp) > 0 and float(inp) == int(inp):
                            print('{0} raised {1}, {2} money_in_pot now {3}\n'.format(current_player.name, int(inp), GENDER_TRANS[current_player.gender], int(inp) + money_to_call))
                            money_to_call += int(inp)
                            round_.pot += money_to_call - current_player.money_in_pot
                            current_player.money -= money_to_call - current_player.money_in_pot
                            current_player.money_in_pot = money_to_call
                            current_player.all_in = True if current_player.money == 0 else False
                            break
                        else:
                            print('Not enough money to raise, or not a valid raise amount')
                            print(inp + ' ' + str(money_to_call) + ' ' + str(current_player.money_in_pot))
                            continue

                    # player called
                    elif inp.lower() == 'call':
                        if money_to_call - current_player.money_in_pot <= current_player.money:
                            print('{0} called {1}\n'.format(current_player.name, current_player.money_in_pot))
                            round_.pot += money_to_call - current_player.money_in_pot
                            current_player.money -= money_to_call - current_player.money_in_pot
                            current_player.money_in_pot = money_to_call
                            current_player.all_in = True if current_player.money == 0 else False
                            break
                        else:
                            # all in option not yet initiated
                            print('Not enough moneny')
                            continue

                    elif inp.lower() == 'fold':
                        current_player.is_folded = True
                        break

                    statements = {'show cards': '{0} has {1}'.format(current_player.name, current_player._cards),
                    'show money': '{0} has {1}'.format(current_player.name, current_player.money),
                    'show money_in_pot': '{0} has {1} in this pot'.format(current_player.name, current_player.money_in_pot)}
                    if inp.lower() in statements:
                        print(statements[inp.lower()])

                if len(players.get_participating_players()) == 1:
                    break

                print("-------------- {0}'s turn is over -----------------\n".format(current_player.name))
                current_player.played_turn = True
                turn += 1

            money_to_call = 0
            players.new_turn()
            _check_win = players.money_in_pot_equal()
            if isinstance(_check_win, Player):
                round_.is_winner(_check_win)
                print('\n\n\n')
                break
