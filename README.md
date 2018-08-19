# PokerLogic

## Synopsis
This is meant to be a project, enabling poker to be played at multiple locations (nothing new).

Includes a library with classes that help with hand parsing, general poker structure and game continuation.
The library's main function is for its main object PokerGame to be baseclassed, IO overriden with methods that define a specific out,
and function that gathers input controlling the instances created from PokerGameSubclass as an external source.


## Library applications

### Messinger
One application of the Library included is made in PlayMessinger.py with a help of fbchat module.
It enables a user to log into messinger account, which has the function of a dealer.
Any group thread that dealer is included in can be used as a poker table, with specific commands.
The exact commands are included in the documentation.


## Code Example
This is a simple use of the library where poker is played on the terminal.
'''python
from lib.PokerGameObject import PlayerGroup, Player, PokerGame

PLAYERS = ['Player1', 'Player2', 'Player3', ... , 'PlayerN'] \# N <= 9
player_group = PlayerGroup([Player(PLAYER) for PLAYER in PLAYERS])
game = PokerGame(player_group)

while True:
  action = input(game.round.current_player.name + ': ')
  if game.round.process_action(action): \# action should be inputed by game.round.current_player
    game_status = game.round.process_after_input() \# returns 0 if game should be ended and 1 if game should continue
    if game_status is 1 and game.is_ok():
      game.new_round()
'''


## Tests
To-do


## License
GNU General Public License v3.0
