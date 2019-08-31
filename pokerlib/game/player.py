class User:
    
    def __init__(self, name, _id, money):
        self.name = name
        self.id = _id
        self.money = money
        
        self.__players = dict()

    def __repr__(self):
        return f"Player({self.name}, {self.money})"
    
    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.id == other.id

    def __getitem__(self, _id):
        return self.__players.get(_id)

    def __iadd__(self, arg):
        player, _id = arg
        self.__players[_id] = player
        return self

class Player:
        
    def __init__(self, _id, name, money):
        self.name = name
        self.id = _id
             
        self.money = money

        self.cards = tuple()
        self.hand = None
        self.is_folded = False
        self.is_all_in = False
        self.turn_stake = [0, 0, 0, 0]

        self.played_turn = False

    @property
    def is_active(self):
        return not (self.is_folded or self.is_all_in)

    def __repr__(self):
        return f"Player({self.name}, {self.money})"
        
    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.id == other.id

    def reset(self):
        self.cards = tuple()
        self.hand = None
        self.is_folded = False
        self.is_all_in = False
        self.turn_stake = [0, 0, 0, 0]
        self.played_turn = False

class PlayerSprite:

    def __init__(self, player_list):
        self.__player_list = player_list

    def __len__(self):
        return len(self.__player_list)

    def __getitem__(self, i):
        return self.__player_list[i]

    def __iter__(self):
        return iter(self.__player_list)

    def __iadd__(self, player):
        self.__player_list.append(player)
        return self

    def getPlayerById(self, _id):
        for player in self.__player_list:
            if player.id == _id:
                return player

    def previousActivePlayer(self, i):
        i = self.getPreviousActiveIndex()
        return self.__player_list[i]

    def nextActivePlayer(self):
        i = self.getNextActiveIndex()
        return self.__player_list[i]

    def previousActiveIndex(self, i):
        i, n = self.current_index, len(self)
        for j in reversed(range(i + 1, i + n)):
            player = self.__player_list[j % n]
            if player.is_active: return j

    def nextActiveIndex(self, i):
        i, n = self.current_index, len(self)                      
        for j in range(i + 1, i + n):
            player = self.__player_list[j % n]
            if player.is_active: return j

    def getActivePlayers(self):
        active_player = filter(
            lambda player: player.is_active,
            self.__player_list
        )
        return type(self)(list(active_players))

    def getNotFoldedPlayers(self):
        not_folded_players = filter(
            lambda player: not player.is_folded,
            self.__player_list
        )
        return type(self)(list(not_folded_players))

    def allPlayedTurn(self):
        for player in self.__player_list:
            if not player.played_turn and player.is_active:
                return False
        return True
