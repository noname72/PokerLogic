# PokerLogic

## Intro
This is meant to be a project, enabling poker to be played at multiple locations (nothing new).

Includes a library with classes that help with hand parsing, poker round and game continuation.
The library's main function is for its main class PokerGame to be baseclassed, IO overriden with methods that define a specific out,
and function that gathers input, controlling the instances created from PokerGameSubclass as an external source.


## Library applications

### Messinger
One application of the library included is made in pokermessinger.py with a help of fbchat module.
It enables a user to log into a messinger account, which comes equipped with functions of a dealer.
Any group thread that the dealer is included in can be initialized as a poker table, with specific commands.
The exact rules are included in the [documentation](https://kuco23.github.io/pokermessinger/documentation.html).


## Code Example
This is a simple use of the library where poker is played on the terminal,
with raw data being sent to the terminal about the game.
```python
from pokerlib.game import PlayerGroup, Player, PokerGame

BIG_BLIND = 20
PLAYER_MONEY = 50 * BIG_BLIND

class MyPokerGame(PokerGame):
  def public_out(self, *args, **kwargs):
    return print(args) if args else print(kwargs)

  def private_out(self, player, *args, **kwargs):
    base_str = player.name + ' --> '
    return print(base_str + str(args)) if args else print(base_str + str(kwargs))

PLAYERS = ['Player1', 'Player2', 'Player3', ... , 'PlayerN'] # 2 <= N <= 9
player_group = PlayerGroup([Player(PLAYER, PLAYER_MONEY) for PLAYER in PLAYERS])
game = MyPokerGame(player_group, BIG_BLIND)

game.new_round()
while game.round:
  action = input(game.round.current_player.name + ': ')
  game.round.process_action(action)
```


## Tests
To-do


## License
GNU General Public License v3.0
