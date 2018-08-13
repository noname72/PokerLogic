from lib.GameObjects import PlayerGroup, Player, PokerGame

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

PLAYERS = ['Nejc', 'Tjasa', 'Gorazd']

class TermPlayer(Player):
    def private_out(self, *args, **kwargs):
        if args:
            print(f"{self.name} --> {args}")
        print(f"{self.name} --> {kwargs}")

class TermPokerGame(PokerGame):
    def public_out(self, *args, **kwargs):
        if args:
            return print(args)
        print(kwargs)


if __name__ == '__main__':
    game = TermPokerGame(PlayerGroup([TermPlayer(player, STARTING_MONEY) for player in PLAYERS]), BIG_BLIND)
    game.new_round()
    while game.round:
        action = input(game.round.current_player.name + ': ')
        if game.round.process_action(game.round.current_player, action):
            game_status = game.round.process_after_input()
            if game_status == 'End Round' and game.is_ok():
                game.new_round()
