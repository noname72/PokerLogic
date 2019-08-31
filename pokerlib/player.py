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

        self.stake = 0
        self.turn_stake = [0, 0, 0, 0]

        self.played_turn = False

    @property
    def is_active(self):
        return not (self.is_folded or self.is_all_in)

    def __repr__(self):
        return f"Player({self.name}, {self.money})"
        
    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.hand < other.hand

    def __gt__(self, other):
        return self.hand > other.hand

    def __eq__(self, other):
        return self.hand == other.hand

    def reset(self):
        self.cards = tuple()
        self.hand = None
        self.is_folded = False
        self.is_all_in = False
        self.turn_stake = [0, 0, 0, 0]
        self.played_turn = False

class PlayerGroup(list):

    def __getitem__(self, i):
        ret = super().__getitem__(i)
        isl = isinstance(ret, list)
        return type(self)(ret) if isl else ret

    def getPlayerById(self, _id):
        for player in self:
            if player.id == _id:
                return player

    def previousActivePlayer(self, i):
        j = self.previousActiveIndex(i)
        return self[j]

    def nextActivePlayer(self, i):
        j = self.nextActiveIndex(i)
        return self[j]

    def previousActiveIndex(self, i):
        n = len(self)
        rn = reversed(range(i + 1, i + n))
        for k in map(lambda j: j % n, rn):
            if self[k].is_active: return k

    def nextActiveIndex(self, i):
        n = len(self)
        rn = range(i + 1, i + n)
        for k in map(lambda j: j % n, rn):
            if self[k].is_active: return k

    def getActivePlayers(self):
        return type(self)(filter(
            lambda player: player.is_active,
            self
        ))

    def getNotFoldedPlayers(self):
        return type(self)(filter(
            lambda player: not player.is_folded,
            self
        ))

    def allPlayedTurn(self):
        for player in self:
            if not player.played_turn and player.is_active:
                return False
        return True

    def winners(self):
        winner = max(self)
        return type(self)(
            [player for player in self if player == winner]
        )
