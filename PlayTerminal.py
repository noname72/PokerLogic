from lib.GameObjects import PlayerGroup, Player, PokerGame
from lib.get_gender import get_gender

sex_dict = {'male': 'his', 'female': 'her', None: 'its'}

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

PLAYERS = ['Nejc', 'Tjasa', 'Gorazd']

class TermPlayer(Player):
    def __init__(self, name, money):
        super().__init__(name, money)
        self.gender = get_gender(name)

for IO_id in PokerGame.IO_actions:
    PokerGame.IO_actions[IO_id] = lambda kwargs: print(kwargs)


if __name__ == '__main__':
    players = PlayerGroup([Player(PLAYER, STARTING_MONEY) for PLAYER in PLAYERS])
    game = PokerGame(players, BIG_BLIND)

    # initiate series of rounds while there are at least 2 players participating
    while len(players.get_participating_players()) >= 2:
        game.new_round()

        # initiate every turn during which players consider actions
        for turn in ["PRE-FLOP", "FLOP", "TURN", "RIVER"]:
            game.new_turn(turn)

            # player that is right next to button plays first
            current_player = players.next_active_player_from(game.button)

            # if all active players have not yet played or someone hasnt called turn continues (current_player inputs action)
            # if there is one player left his input doesnt matter, as he would raise or call only himself
            while (not players.all_played_turn() or not game.pot_is_equal()) and len(players.get_active_players()) >= 2 :

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
