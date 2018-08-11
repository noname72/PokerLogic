from pathlib import Path
from fbchat import Client
from fbchat.models import *
from lib.GameObjects import PlayerGroup, Player, PokerGame
from lib.Methods import FileMethods, TimeMethods

EMOJI_DICT = {' of Spades': '♠', ' of Clubs': '♣️', ' of Diamonds': '♦️', ' of Hearts': '♥️', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'}

BASE_MONEY = 1000
SMALL_BLIND = BASE_MONEY // 100
BIG_BLIND = 2 * SMALL_BLIND

MONEY_WAITING_PERIOD = 4
MONEY_ADD_PER_PERIOD = 100

DATABASE = Path('data')
BASE_DATAFILE = lambda: {'money': BASE_MONEY, 'timestamp': TimeMethods.formatted_timestamp()}

DEALER_MAIL = 'amahmoh23@gmail.com'
DEALER_PASSWORD = 'ramanujan'
TABLE_ID = '1339347802835218'

class Dealer(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = []

    def onPeopleAdded(self, added_ids, author_id, thread_id, **kwargs):
        if author_id == self.uid:
            return None

        game = self.fetch_game_by_table_id(thread_id)
        if game:
            for added_id in added_ids:
                if added_id not in [player.fb_id for player in game.players]: # this should always be  True
                    game.players.append(FbPlayer(self.getUserInfo(added_in)))

            game.update_participating_players()
            # if game round isnt initiated because there werent enough players, and now its ok, new round can begin
            if not game.round and game.is_ok():
                game.new_round()

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        game = self.fetch_game_by_table_id(thread_id)
        if game: # if a game isnt played on the table there isnt anything to do
            if removed_id == self.uid: # if a dealer is removed, remove game on that table from games
                self.games.remove(game)
                return None

            player = game.get_player_by_attr('fb_id', removed_id)
            if removed_id == game.round.current_player.fb_id:
                game.process_action(player, 'fold')
                game.process_after_input()
                game.players.remove(player)

            elif removed_id in [player for player in game.round.players]: # if player is playing in a round, but isnt the one whose input is required set status of his hand to folded
                player.is_folded = True
                game.players.remove(player)

            if not game.round and game.is_ok():
                game.new_round()

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        if author_id == self.uid:
            return None

        # message within active round was sent
        game = self.fetch_game_by_table_id(thread_id)
        if game and game.round:
            author_player = game.round.players.get_player_by_attr('fb_id', author_id)

            # message was sent from current player in game round
            if author_player and author_id == game.round.current_player.fb_id and game.round.process_action(author_player, message):
                status = game.round.process_after_input()

                # this is where players are added or removed for the next round
                # round ends, we check if conditions for another round are met
                if status == "End Round":
                    if game.is_ok():
                        game.new_round()

        # messages sent from a group not in games
        elif not game and kwargs['thread_type'] == ThreadType.GROUP:
            if message.lower() == 'activate':
                self.add_game(thread_id)
                return None

        # messages sent privately to the dealer
        elif kwargs['thread_type'] == ThreadType.USER:
            test_path = [path for path in Path(DATABASE).iterdir() if path.suffix == '.json' and path.name.replace('.json', '') == author_id]
            assert len(test_path) <= 1
            
            # if player is inside the database
            if test_path:
                player_path = test_path[0]
                data = FileMethods.fetch_database_data(player_path)
                if message.lower() == 'show money':
                    self.sendMessage(f"You Have {data['money']} left", thread_id = author_id)

                elif message.lower() == 'gimme monneyz':
                    timestamp = TimeMethods.formatted_timestamp()
                    diff = TimeMethods.get_time_diff(timestamp, data['timestamp'])
                    if diff[0] or diff[1] >= MONEY_WAITING_PERIOD * 3600:
                        data['money'] += MONEY_ADD_PER_PERIOD
                        data['timestamp'] = timestamp
                        FileMethods.send_to_database(player_path, data)
                        send = self.sendMessage(f"{MONEY_ADD_PER_PERIOD} Successfully Added", thread_id = author_id)
                    else:
                        self.sendMessage(f"Money Can Be Requested in {diff[0]} days and {diff[1]} seconds", thread_id = author_id)

    def add_game(self, table_id, big_blind = BIG_BLIND):
        if not self.fetch_game_by_table_id(table_id):
            game = FbPokerGame(FbPlayerGroup(self.fetch_players_on_table(table_id)), big_blind, table_id)
            self.games.append(game)

            # if the conditions for a new round are met, game starts
            if game.is_ok():
                game.new_round()
        else:
            print('game already exists')

    def fetch_games_by_player_id(self, player_id):
        return [game for game in self.games if player_id in set(player.fb_id for player in game.round.players).union(set(player.fb_id for player in game.players))]
    def fetch_game_by_table_id(self, table_id):
        game = [game for game in self.games if game.table_id == table_id] or [[]]
        return game[0]
    def fetch_uids_on_table(self, table_id) -> set: # without dealer (dealer on the table is trivial)
        return {uid for uid in self.fetchGroupInfo(table_id)[table_id].participants if uid != self.uid} # set of user ids
    def fetch_players_on_table(self, table_id) -> list:
        return [FbPlayer(self.fetchUserInfo(uid)[uid]) for uid in self.fetch_uids_on_table(table_id)]

DEALER = Dealer(DEALER_MAIL, DEALER_PASSWORD)

class FbPlayerGroup(PlayerGroup):
    pass

class FbPlayer(Player):
    IO_actions = {
    'Dealt Cards': lambda kwargs: '  '.join([card for card in kwargs['cards']])}

    def __init__(self, fb_user: User): # fbchat.models.User
        self.fb_id = fb_user.uid
        self.data_path = DATABASE / (self.fb_id + '.json')

        if self.data_path.is_file():
            money = FileMethods.fetch_database_data(self.data_path)['money']
        else:
            money = BASE_MONEY
            FileMethods.create_datafile(self.data_path, BASE_DATAFILE())

        super().__init__(fb_user.name, money)

    def __eq__(self, other):
        return self.fb_id == other.fb_id

    # every time a player attr is updated or reset, it is saved in a file
    def __setattr__(self, attr_name, value):
        super().__setattr__(attr_name, value)
        if attr_name in ['money']:
            data = {attr_name: value}
            FileMethods.send_to_database(self.data_path, data)

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
    'New Round': lambda kwargs: (" Round " + str(kwargs['round_index']) + " ").center(40, '-'),
    'Small Blind': lambda kwargs: kwargs['player'] + ' posted the Small Blind',
    'Big Blind': lambda kwargs: kwargs['player'] + ' posted the Big Blind',
    'New Turn': lambda kwargs: kwargs['turn_name'] + ':\n' + '  '.join(card for card in kwargs['table']),
    'Player Went All-In': lambda kwargs: kwargs['player'] + ' went all-in with ' + str(kwargs['player_money']),
    'Declare Unfinished Winner': lambda kwargs: kwargs['winner'] + ' won ' + str(kwargs['won']),
    'Public Show Cards': lambda kwargs: kwargs['player'] + ' has ' + '  '.join(card for card in kwargs['player_cards']),
    'Declare Finished Winner': lambda kwargs: kwargs['winner'] + ' won ' + str(kwargs['won']) + ' with ' + kwargs['winner_hand'] +
    ''.join([', ' + str(kwargs['kicker']) + ' kicker' if kwargs['kicker'] else ''])
    }

    def __init__(self, players: FbPlayerGroup, big_blind: int, table_id: str): # players is a PlayerGroup object of FbPlayers
        super().__init__(players, big_blind)
        self.table_id = table_id

    def __eq__(self, other):
        return self.table_id == other.table_id

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
if __name__ == '__main__':
    DEALER.add_game(TABLE_ID)
    DEALER.listen()
