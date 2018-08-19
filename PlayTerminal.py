from lib.PokerGameObjects import PlayerGroup, Player, PokerGame

PLAYERS = ['Nejc', 'Tjasa', 'Gorazd']

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

class TermPokerGame(PokerGame):

    def private_out(self, player, *args, **kwargs):
        if args:
            return print(f"{player.name} --> {args}")
        print(f"{player.name} --> {kwargs}")

    def public_out(self, *args, **kwargs):
        if args:
            return print(args)
        print(kwargs)


if __name__ == '__main__':
    game = TermPokerGame(PlayerGroup([Player(player, STARTING_MONEY // (i + 1)) for i, player in enumerate(PLAYERS)]), BIG_BLIND)
    game.new_round()
    while game.round:
        action = input(game.round.current_player.name + ': ')
        if game.round.process_action(game.round.current_player, action):
            game_status = game.round.process_after_input()
            if game_status is 1 and game.is_ok():
                game.new_round()
