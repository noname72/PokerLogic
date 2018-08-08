from pathlib import Path
from fbchat import Client
from fbchat.models import *
from lib.GameObjects import PlayerGroup, Player, PokerGame

SEX_DICT = {'male': 'his', 'female': 'her', None: 'its'}
EMOJI_DICT = {' of Spades': '♠', ' of Clubs': '♣️', ' of Diamonds': '♦️', ' of Hearts': '♥️', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'}
DIC = {0:0, 3: 1, 4: 2, 5: 3}

STARTING_MONEY = 1000
SMALL_BLIND = STARTING_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

DEALER_MAIL = 'amahmoh23@gmail.com'
DEALER_PASSWORD = 'ramanujan'
TABLE_ID = '1339347802835218'

class Dealer(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = []

    def onPeopleAdded(self, added_ids, author_id, thread_id, **kwargs):
        if author_id == self.uid:
            self.add_game(thread_id)
        else:
            game = self.fetch_game_by_table_id(thread_id)
            for added_id in added_ids:
                game.players.append(FbPlayer(self.getUserInfo(added_id)))

            # if game was paused because there werent enough players, and now its ok, new round can begin
            if game.on_standby and game.is_ok():
                game.on_standby = False
                game.new_round()

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        assert removed_id != self.uid

        game = self.fetch_game_by_table_id(thread_id)
        if not game:
            raise Exception('person removed from table containing dealer, but not the game')

        player = game.get_player_by_attr('fb_id', removed_id)
        if removed_id == game.current_player.fb_id:
            self.onMessage(removed_id, 'fold', thread_id)
        else:
            player.is_folded = True

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        if author_id == self.uid:
            return None

        elif thread_id in [game.table_id for game in self.games]:
            game = self.fetch_game_by_table_id(thread_id)
            author_player = game.get_player_by_attr('fb_id', author_id)

            if author_id == game.current_player.fb_id and game.on_standby == False and game.process_action(author_player, message):
                status = game.process_after_input()

                # this is where players are added or removed for the next round
                # round ends, we check if conditions for another round are met
                if status == "End Round":
                    self.update_players_in_game(game)
                    if game.is_ok():
                        game.new_round()
                    else:
                        game.on_standby = True

            return None

        elif thread_id != author_id and message.lower() == 'activate':
            self.add_game(self, thread_id)
            return None

        user_game = self.searchForPlayer(thread_id)
        if user_game is not None and message.lower() == 'show money':
            user_player = user_game.get_player_by_attr('fb_id', thread_id)
            user_player.private_out(player_money = user_player.money, _id = 'Show Money')


    def add_game(self, table, big_blind = BIG_BLIND):
        if not self.fetch_game_by_table_id(table):
            game = FbPokerGame(FbPlayerGroup(self.fetch_players_on_table(table)), big_blind, table)
            self.games.append(game)

            # if the conditions for a new round are met game starts
            if game.is_ok():
                game.new_round()
            else:
                game.on_standby = True
            return game

    def update_players_in_game(self, game):
        players_on_table = self.fetch_players_on_table(game.table_id)
        for player_in_game in game.players:
            if player_in_game not in players_on_table:
                game.players.remove(player)

    def searchForPlayer(self, player_id):
        for game in self.games:
            if player_id in [player.fb_id for player in game.players]:
                return game

    def fetch_game_by_table_id(self, table_id):
        game = [game for game in self.games if game.table_id == table_id] or [[]]
        return game[0]
    def fetch_uids_on_table(self, table_id) -> set: # without dealer (dealer on the table is trivial)
        return {uid for uid in self.fetchGroupInfo(table_id)[table_id].participants if uid != self.uid} # set of user ids
    def fetch_players_on_table(self, table_id) -> list:
        return [FbPlayer(self.fetchUserInfo(uid)[uid]) for uid in self.fetch_uids_on_table(table_id)]

DEALER = Dealer(DEALER_MAIL, DEALER_PASSWORD)

class FbPlayerGroup(PlayerGroup):
    def save_data(self, attr: str):
        for player in self:
            with open(player.data_path, 'w') as raw:
                print(player.__getattribute__(attr), file=raw)

class FbPlayer(Player):
    base_money = STARTING_MONEY
    database = Path('data')
    IO_actions = {
    'Dealt Cards': lambda kwargs: '  '.join([card for card in kwargs['cards']]),
    'Show Money': lambda kwargs: 'You have ' + str(kwargs['player_money']) + ' left'}

    def __init__(self, fb_user: User): # fbchat.models.User
        self.fb_id = fb_user.uid
        self.gender = fb_user.gender.split('_')[0]
        self.data_path = FbPlayer.database / (self.fb_id + '.txt')

        if self.data_path.is_file():
            money = self.fetch_money_from_database()
        else:
            money = FbPlayer.base_money
            self.create_datafile()

        super().__init__(fb_user.name, money)

    def __eq__(self, other):
        return self.fb_id == other.fb_id

    # every time a player attr is updated or reset, it is logged in a file
    def __setattr__(self, attr_name, value):
        super().__setattr__(attr_name, value)
        if attr_name == 'money':
            with open(self.data_path, 'w') as raw:
                print(self.money, file=raw)

    def create_datafile(self):
        with open(self.data_path, 'a') as raw:
            print(FbPlayer.base_money, file=raw)
        print(f"creating {self.name} database")

    def fetch_money_from_database(self):
        with open(self.data_path, 'r') as raw:
            data = raw.readlines()
        return int(data[0].strip())

    def private_out(self, text = None, **kwargs):
        send = None
        if text:
            send = text
        elif kwargs['_id'] in FbPlayer.IO_actions:
            send = FbPlayer.IO_actions[kwargs['_id']](kwargs)

        # using fb emojis to display suits
        for color in EMOJI_DICT:
            send = send.replace(color, EMOJI_DICT[color])

        DEALER.sendMessage(send, thread_id = self.fb_id, thread_type = ThreadType.USER)


class FbPokerGame(PokerGame):
    IO_actions = {
    'New Round': lambda kwargs: (" Round " + str(kwargs['round_index']) + " ").center(20, '-'),
    'Small Blind': lambda kwargs: kwargs['player'] + ' posted the Small Blind',
    'Big Blind': lambda kwargs: kwargs['player'] + ' posted the Big Blind',
    'New Turn': lambda kwargs: kwargs['turn_name'] + ':\n' + '  '.join(card for card in kwargs['table']),
    'Player Went All-In': lambda kwargs: kwargs['player'] + ' went all-in with ' + str(kwargs['player_money']),
    'Declare Unfinished Winner': lambda kwargs: kwargs['winner'] + ' won ' + str(kwargs['won']),
    'Declare Finished Winner': lambda kwargs: kwargs['winner'] + ' won ' + str(kwargs['won']) + ' with ' + kwargs['winner_hand'],
    'Public Show Cards': lambda kwargs: kwargs['player'] + ' has ' + '  '.join(card for card in kwargs['player_cards'])}

    def __init__(self, players: FbPlayerGroup, big_blind: int, table_id: int): # players is a PlayerGroup objects of FbPlayers
        super().__init__(players, big_blind)
        self.table_id = table_id

    def public_out(self, text = None, **kwargs):
        send = None
        if text:
            send = text
        elif kwargs['_id'] in FbPokerGame.IO_actions:
            send = FbPokerGame.IO_actions[kwargs['_id']](kwargs)

        # using fb emojis to display suits
        for suit in EMOJI_DICT:
            send = send.replace(suit, EMOJI_DICT[suit])

        DEALER.sendMessage(send, thread_id = self.table_id, thread_type = ThreadType.GROUP)

# game continuation
DEALER.add_game(TABLE_ID)
if __name__ == '__main__':
    DEALER.listen()
