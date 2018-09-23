# PokerLogic

## Synopsis
This is meant to be a project, enabling poker to be played at multiple locations (nothing new).

Includes a library with classes that help with hand parsing, general poker structure and game continuation.
The library's main function is for its main object PokerGame to be baseclassed, IO overriden with methods that define a specific out,
and function that gathers input, controlling the instances created from PokerGameSubclass as an external source.


## Library applications

### Messinger
One application of the Library included is made in PokerMessinger.py with a help of fbchat module.
It enables a user to log into a messinger account, which comes equipped with functions of a dealer.
Any group thread that the dealer is included in can be used as a poker table, with specific commands.
The exact commands are included in the [documentation](https://kuco23.github.io/pokermessinger/documentation.html).


## Code Example
This is a simple use of the library where poker is played on the terminal.
```python
from lib.PokerGameObject import PlayerGroup, Player, PokerGame

class MyPokerGame(PokerGame):
  def public_out(self, *args, **kwargs):
    return print(args) if args else print(kwargs)

  def private_out(self, player, *args, **kwargs):
    base_str = player.name + ' --> '
    return print(base_str + str(args)) if args else print(base_str + str(kwargs))

PLAYERS = ['Player1', 'Player2', 'Player3', ... , 'PlayerN'] # 2 <= N <= 9
player_group = PlayerGroup([Player(PLAYER) for PLAYER in PLAYERS])
game = MyPokerGame(player_group)

game.new_round()
while game.round:
  action = input(game.round.current_player.name + ': ')
  game.round.process_action(action)
```


## Tests
To-do


## License
GNU General Public License v3.0
