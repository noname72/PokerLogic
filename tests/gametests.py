from pathlib import Path
from sys import path
path.append(str(Path().cwd().parent))
from pokerlib.handparser import HandParser
from pokerlib.game import PlayerGroup, Player, PokerGame

PLAYERS = ['Nejc', 'Tjasa']

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

class TerminalPokerGame(PokerGame):

    def private_out(self, player, *args, **kwargs):
        if args:
            return print(f"{player.name} --> {args}")
        print(f"{player.name} --> {kwargs}")

    def public_out(self, *args, **kwargs):
        if args:
            return print(args)
        print(kwargs)


if __name__ == '__main__':
    players = PlayerGroup([Player(player, STARTING_MONEY)
                           for i, player in enumerate(PLAYERS)])
    game = TerminalPokerGame(players, BIG_BLIND)
    game.new_round()
    while game.round:
        action = input(game.round.current_player.name + ': ')
        game.round.process_action(action)
