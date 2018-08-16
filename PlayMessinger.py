from pathlib import Path
from fbchat import Client
from fbchat.models import *
from lib.GameObjects import PlayerGroup, Player, PokerGame
from lib.Methods import FileMethods, TimeMethods

# this can be changed to any Facebook account
DEALER_MAIL = 'amahmoh23@gmail.com'
DEALER_PASSWORD = 'ramanujan'

VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♠', '♣️', '♦️', '♥️']

BASE_MONEY = 1000 # money that a new player gets
BIG_BLIND = BASE_MONEY // 50 # big_blinds at every table

MONEY_WAITING_PERIOD = 4 # how long until a player can re-request for money
MONEY_ADD_PER_PERIOD = 100 # how much a player gets if he requests for money

DATABASE = Path('data') # database of player .json files

MESSAGE_STATEMENTS = [
'call', 'fold', 'check',
'show money', 'gimme moneyz',
'game::activate', 'last round', 'cancel last round']

class Dealer(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = {} # dict {thread_id: game_object}

    def onPeopleAdded(self, added_ids, author_id, thread_id, **kwargs):
        if thread_id in self.games:
            game = self.games[thread_id]
            for added_id in added_ids:
                assert added_id not in [player.fb_id for player in game.players] and added_id != self.uid
                user_info = self.getUserInfo(added_in)
                game.on_player_join(FbPlayer(user_info.uid, user_info.name))

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        if thread_id in self.games: # if a game isnt played on the table there isnt anything to do
            if removed_id == self.uid: # if a dealer is removed, remove game on that table from games
                ...
                self.games.pop(thread_id)
                return None
            elif author_id != removed_id: # player only can remove himself
                return self.addUsersToGroup([removed_id], thread_id = thread_id)

            game = self.games[thread_id]
            player = game.players.get_player_by_attr('fb_id', removed_id)
            return game.on_player_leave(player) if player else None

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        message = message.lower()
        if author_id == self.uid or (message not in MESSAGE_STATEMENTS and not message.startswith('raise ')):
            return None

        # message within active round was sent
        game = self.games[thread_id] if thread_id in self.games else None
        if game and game.round:
            author_player = game.round.players.get_player_by_attr('fb_id', author_id)
            if not author_player: # player has to be in round for the following processes
                return None

            elif message == 'last round' or 'cancel last round':
                game.round.exit_after_this = not game.round.exit_after_this
                _send = 'game will end after this round' if game.round.exit_after_this else 'game will continue'
                self.sendMessage(_send, thread_id = thread_id, thread_type = ThreadType.GROUP)

            # message was sent from current player in game round
            elif author_id == game.round.current_player.fb_id and game.round.process_action(author_player, message):
                status = game.round.process_after_input()

                # this is where players are added or removed for the next round
                # round ends, we check if conditions for another round are met
                if status is 1 and game.is_ok():
                    game.new_round()

        # messages sent from a group not in games or group in games where rounds aren't being played
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
        if table_id not in self.games:
            self.games[table_id] = FbPokerGame(PlayerGroup(self.fetch_players_on_table(table_id)), big_blind, table_id)
            return True
        else:
            return False

    def start_round(self, table_id):
        game = self.games[table_id]
        assert game
        if not game.round and game.is_ok():
            game.new_round()
        else:
            game.public_out('Could Not Start A New Round')

    def fetch_uids_on_table(self, table_id) -> set: # without dealer (dealer on the table is trivial)
        return {uid for uid in self.fetchGroupInfo(table_id)[table_id].participants if uid != self.uid} # set of user ids
    def fetch_players_on_table(self, table_id) -> list:
        return [FbPlayer(user_info.uid, user_info.name) for user_info in [self.fetchUserInfo(uid)[uid]) for uid in self.fetch_uids_on_table(table_id)]]


class FbPlayer(Player):

    def __init__(self, fb_id: str, name: str): # fbchat.models.User
        self.fb_id = fb_id
        self.data_path = DATABASE / (self.fb_id + '.json')

        if self.data_path.is_file():
            self.money = FileMethods.fetch_database_data(self.data_path)['money']
        else:
            self.money = BASE_MONEY
            FileMethods.create_datafile(self.data_path, self.base_datafile)

        super().__init__(name, self.money)

    @property
    def base_datafile(self):
        return {'name': self.name, 'money': BASE_MONEY, 'timestamp': TimeMethods.formatted_timestamp()}

    def __eq__(self, other):
        return self.fb_id == other.fb_id

    # every time a player attr is updated or reset, it is saved in a file
    def __setattr__(self, attr_name, value):
        super().__setattr__(attr_name, value)
        if attr_name in ['money']:
            data = {attr_name: value}
            FileMethods.send_to_database(self.data_path, data)


class FbPokerGame(PokerGame):
    IO_actions = {
    'Dealt Cards': lambda kwargs: FbPokerGame.style_cards(kwargs['cards']),
    'New Round': lambda kwargs: (" Round " + str(kwargs['round_index']) + " ").center(40, '-'),
    'Small Blind': lambda kwargs: kwargs['player'] + ' posted the Small Blind',
    'Big Blind': lambda kwargs: kwargs['player'] + ' posted the Big Blind',
    'New Turn': lambda kwargs: kwargs['turn_name'] + ':\n' + FbPokerGame.style_cards(kwargs['table']),
    'Player Went All-In': lambda kwargs: kwargs['player'] + ' went all-in with ' + str(kwargs['player_money']),
    'Declare Unfinished Winner': lambda kwargs: kwargs['winner'] + ' won ' + str(kwargs['won']),
    'Public Show Cards': lambda kwargs: kwargs['player'] + ' has ' + FbPokerGame.style_cards(kwargs['player_cards']),
    'Declare Finished Winner': lambda kwargs: kwargs['winner'] + ' won ' + str(kwargs['won']) + ' with ' +
     FbPokerGame.hand_repr(kwargs['hand_name'], kwargs['hand_base'], VALUES, SUITS) +
    ''.join([', ' + FbPokerGame.style_cards(kwargs['kicker']) + ' kicker' if kwargs['kicker'] else ''])
    }

    @staticmethod
    def style_cards(cls, cards, kicker=False):
        if kicker is False:
            return '  '.join(VALUES[val] + SUITS[suit] for val, suit in cards)
        else:
            return '+'.join(VALUES[kick] for kick in kicker)

    def __init__(self, players: PlayerGroup, big_blind: int, table_id: str): # players is a PlayerGroup object of FbPlayers
        super().__init__(players, big_blind)
        self.table_id = table_id

    def __eq__(self, other):
        return self.table_id == other.table_id

    def private_out(self, player, text = None, **kwargs):
        send = None
        if text:
            send = text
        elif kwargs['_id'] in FbPokerGame.IO_actions:
            send = FbPokerGame.IO_actions[kwargs['_id']](kwargs)

        DEALER.sendMessage(send, thread_id = player.fb_id, thread_type = ThreadType.USER)

    def public_out(self, text = None, **kwargs):
        send = None
        if text:
            send = text
        elif kwargs['_id'] in FbPokerGame.IO_actions:
            send = FbPokerGame.IO_actions[kwargs['_id']](kwargs)

        DEALER.sendMessage(send, thread_id = self.table_id, thread_type = ThreadType.GROUP)

# game continuation
if __name__ == '__main__':
    DEALER = Dealer(DEALER_MAIL, DEALER_PASSWORD)
    DEALER.listen()
