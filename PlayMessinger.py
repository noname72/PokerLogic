from pathlib import Path
from fbchat import Client
from fbchat.models import *
from lib.GameObjects import PlayerGroup, Player, PokerGame
from lib.Methods import FileMethods, TimeMethods

EMOJI_DICT = {' of Spades': '♠', ' of Clubs': '♣️', ' of Diamonds': '♦️', ' of Hearts': '♥️', 'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'}

BASE_MONEY = 1000
BIG_BLIND = BASE_MONEY // 50

MONEY_WAITING_PERIOD = 4
MONEY_ADD_PER_PERIOD = 100

DATABASE = Path('data')
BASE_DATAFILE = lambda: {'money': BASE_MONEY, 'timestamp': TimeMethods.formatted_timestamp()}

DEALER_MAIL = 'amahmoh23@gmail.com'
DEALER_PASSWORD = 'ramanujan'

MESSAGE_STATEMENTS = [
'call', 'fold', 'check',
'show money', 'gimme moneyz',
'game::activate', 'last round']

class Dealer(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = []
        for thread in self.fetchThreadList():
            if thread.type == ThreadType.GROUP:
                self.add_game(thread.uid)

    def onPeopleAdded(self, added_ids, author_id, thread_id, **kwargs):
        game = self.fetch_game_by_table_id(thread_id)
        if self.uid in added_ids and not game:
            self.add_game(thread_id)

        elif game:
            for added_id in added_ids:
                assert added_id not in [player.fb_id for player in game.players] and added_id != self.uid
                game.players.append(FbPlayer(self.getUserInfo(added_in)))

            game.update_participating_players()

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        game = self.fetch_game_by_table_id(thread_id)
        if game: # if a game isnt played on the table there isnt anything to do
            if removed_id == self.uid: # if a dealer is removed, remove game on that table from games
                self.games.remove(game)
                return None

            player = game.players.get_player_by_attr('fb_id', removed_id)
            if not player:
                return None

            if game.round and player in game.round.players and player.is_active(): # if round is being played and if player is playing in it
                self.sendMessage(round_player.name + "'s Hand is Folded", thread_id = thread_id, thread_type = ThreadType.GROUP)
                if round_player.id == game.round.current_player.fb_id:
                    game.round.process_action(player, 'fold')
                    game.round.process_after_input()
                else:
                    round_player.is_folded = True

            game.players.remove(player)
            self.start_round(thread_id)

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        message = message.lower()
        if author_id == self.uid or (message not in MESSAGE_STATEMENTS and not message.startswith('raise ')):
            return None

        # message within active round was sent
        game = self.fetch_game_by_table_id(thread_id)
        if game and game.round:
            author_player = game.round.players.get_player_by_attr('fb_id', author_id)
            if not author_player: # player has to be in round for the following processes
                return None

            elif message == 'last round':
                game.round.exit_after_this = True
                self.sendMessage('game will end after this round', thread_id = thread_id, thread_type = ThreadType.GROUP)

            # message was sent from current player in game round
            elif author_id == game.round.current_player.fb_id and game.round.process_action(author_player, message):
                status = game.round.process_after_input()

                # this is where players are added or removed for the next round
                # round ends, we check if conditions for another round are met
                if status is 1 and game.is_ok():
                    game.new_round()

        # messages sent from a group not in games
        elif kwargs['thread_type'] == ThreadType.GROUP:
            if message.lower() == 'game::activate':
                if not game:
                    self.add_game(thread_id)
                self.start_round(thread_id)
                return None

        # messages sent privately to the dealer (does not deal with game objects)
        elif kwargs['thread_type'] == ThreadType.USER:
            test_path = [path for path in Path(DATABASE).iterdir() if path.suffix == '.json' and path.name[:-5] == author_id]
            assert len(test_path) <= 1

            # if player is inside the database
            if test_path:
                player_path = test_path[0]
                data = FileMethods.fetch_database_data(player_path)
                if message.lower() == 'show money':
                    self.sendMessage(f"You Have {data['money']} left", thread_id = author_id, thread_type = ThreadType.USER)

                elif message.lower() == 'gimme moneyz':
                    timestamp = TimeMethods.formatted_timestamp()
                    diff = TimeMethods.get_time_diff(timestamp, data['timestamp'])

                    if diff['days'] or diff['hours'] >= MONEY_WAITING_PERIOD:
                        data['money'] += MONEY_ADD_PER_PERIOD
                        data['timestamp'] = timestamp
                        FileMethods.send_to_database(player_path, data)
                        send = self.sendMessage(str(MONEY_ADD_PER_PERIOD) + " Successfully Added", thread_id = author_id, thread_type = ThreadType.USER)
                    else:
                        remainder = TimeMethods.get_time_remainder(timestamp, data['timestamp'], MONEY_WAITING_PERIOD)
                        to_wait = ', '.join([str(remainder[timeframe]) + ' ' + timeframe for timeframe in remainder if remainder[timeframe]])
                        self.sendMessage("Money Can Be Requested in " + to_wait, thread_id = author_id, thread_type = ThreadType.USER)

    def add_game(self, table_id, big_blind = BIG_BLIND):
        if not self.fetch_game_by_table_id(table_id):
            self.games.append(FbPokerGame(FbPlayerGroup(self.fetch_players_on_table(table_id)), big_blind, table_id))
            return True
        else:
            return False

    def start_round(self, table_id):
        game = self.fetch_game_by_table_id(table_id)
        assert game
        if not game.round and game.is_ok():
            game.new_round()

    def fetch_game_by_table_id(self, table_id):
        game = [game for game in self.games if game.table_id == table_id] or [[]]
        return game[0]
    def fetch_uids_on_table(self, table_id) -> set: # without dealer (dealer on the table is trivial)
        return {uid for uid in self.fetchGroupInfo(table_id)[table_id].participants if uid != self.uid} # set of user ids
    def fetch_players_on_table(self, table_id) -> list:
        return [FbPlayer(self.fetchUserInfo(uid)[uid]) for uid in self.fetch_uids_on_table(table_id)]

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
    ''.join([', ' + '+'.join(kwargs['kicker']) + ' kicker' if kwargs['kicker'] else ''])
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
    DEALER = Dealer(DEALER_MAIL, DEALER_PASSWORD)
    DEALER.listen()
