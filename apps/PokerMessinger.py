# originaly made with fbchat Version 1.3.9

from sys import path
from random import choice
from pathlib import Path
from fbchat import Client
path.append(str(Path().cwd().parent)) # so i can use absolute paths
from fbchat.models import *
from lib.pokerlib import PlayerGroup, Player, PokerGame
from lib.methods import FileMethods, TimeMethods

# this can be changed to any Facebook account
DEALER_MAIL = 'amahmoh23@gmail.com'
DEALER_PASSWORD = 'ramanujan'

DATABASE = Path('data') # database of player .json files

TABLE_MONEY = 1000 # money that a new player gets
BIG_BLIND = TABLE_MONEY // 50 # big_blinds at every table

PLAYER_STARTING_MONEY = 4000 # new player gets this at the start of the game
MONEY_WAITING_PERIOD = 4 # how long until a player can re-request for money
MONEY_ADD_PER_PERIOD = 100 # how much a player gets if he requests for money

VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♠', '♣️', '♦️', '♥️']

# valid statements that a dealer receives from players (they should all be lowercase)
GAME_START = '::init' # starts game and/or round if conditions for round are met
TOGGLE_LAST_ROUND = '::lastround' # toggles the round being played
SHOW_USER_TABLE_MONEY = '::money' # shows how much money user has on the table
REFILL_USER_TABLE_MONEY = '::refill' # refills user table money to TABLE_MONEY (takes it from his main money)
WITHDRAW_USER_TABLE_MONEY = '::withdraw' # takes all the money from player's table and adds it to his main money

SHOW_USER_MONEY = 'show money' # shows player main money
REQUEST_FOR_MONEY = 'gimme moneyz' # requests for MONEY_ADD_PER_PERIOD

GAME_MANIPULATION_STATEMENTS = [GAME_START, TOGGLE_LAST_ROUND, SHOW_USER_TABLE_MONEY, REFILL_USER_TABLE_MONEY, WITHDRAW_USER_TABLE_MONEY]
PRIVATE_STATEMETNS = [SHOW_USER_MONEY, REQUEST_FOR_MONEY]
MID_GAME_STATEMENTS = ['call', 'fold', 'check', 'all in'] # these must remain the same
ALL_STATEMENTS = GAME_MANIPULATION_STATEMENTS + PRIVATE_STATEMETNS + MID_GAME_STATEMENTS

class Dealer(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = {} # dict {thread_id: game_object}

    def onPeopleAdded(self, added_ids, author_id, thread_id, **kwargs):
        if thread_id in self.games:
            game = self.games[thread_id]
            for added_id in added_ids:
                if added_id in [player.fb_id for player in game.all_players] or added_id == self.uid:
                    continue
                user_info = self.getUserInfo(added_in)
                game.on_player_join(FbPlayer(user_info.name, user_info.uid, game.table_id))

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        if thread_id in self.games: # if a game isnt played on the table there isnt anything to do
            if removed_id == self.uid: # if a dealer is removed, remove game on that table from games
                self.make_threat(author_id) # make a threat so user will remember not to remove you from the game ever again
                self.remove_game(thread_id) # this is where game is removed and ended forcibly (SHOULDN'T HAPPEN)

            elif author_id != removed_id: # player only can remove himself
                self.addUsersToGroup([removed_id], thread_id = thread_id)
            else:
                game = self.games[thread_id]
                player = game.players.get_player_by_attr('fb_id', removed_id)
                if player:
                    game.on_player_leave(player)
                    player.resolve()

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        message = message.lower()
        if author_id == self.uid or (message not in ALL_STATEMENTS and not message.startswith('raise ')):
            return None

        game = self.games[thread_id] if thread_id in self.games else None

        # messages sent from a group (game manipulation messages)
        if kwargs['thread_type'] == ThreadType.GROUP and message in GAME_MANIPULATION_STATEMENTS:
            if message == GAME_START:
                if not game:
                    self.add_game(thread_id)
                if not self.start_round(thread_id):
                    self.sendMessage("A new round couldn't be started", thread_id = thread_id, thread_type = ThreadType.GROUP)
                return None

            # from now on everything requires for a game to be played and that a player in that game wrote the message
            player = game.all_players.get_player_by_attr('fb_id', author_id) if game else None
            if not player:
                return None

            if message == TOGGLE_LAST_ROUND:
                if game.round:
                    game.round.exit_after_this = not game.round.exit_after_this
                    _send = 'game will end after this round' if game.round.exit_after_this else 'game will continue'
                    self.sendMessage(_send, thread_id = thread_id, thread_type = ThreadType.GROUP)

            # player wants to refill his money on the playing table
            elif message == REFILL_USER_TABLE_MONEY:
                if not game.round or player not in game.round.players or player.is_folded:
                    money_filled = player.refill_money()
                    if money_filled is not False:
                        self.sendMessage('Money successfully refilled by ' + str(money_filled) + ' to ' + str(player.money),
                        thread_id = thread_id, thread_type = ThreadType.GROUP)

            # player wants to get all money out of the table (player has to be folded or rounds not played)
            elif message == WITHDRAW_USER_TABLE_MONEY:
                if (not game.round or player.is_folded) and player.money > 0:
                    money = player.money
                    player.withdraw_money()
                    _send = str(money) + ' successfully withdrawn'
                elif player.money == 0:
                    _send = 'You have no money on this table'
                else:
                    _send = 'Your hand has to be folded or no rounds active in orded for you to whitdraw money, so theres no funny bussiness'
                self.sendMessage(_send, thread_id = thread_id, thread_type = ThreadType.GROUP)

            # player requested to see the money in a specific game he is playing (THIS SHOULD BE GONE when a better solution arises)
            elif message == SHOW_USER_TABLE_MONEY:
                self.sendMessage('You Have ' + str(player.money), thread_id = thread_id, thread_type = ThreadType.GROUP)

        # message within active round was sent (game continuation)
        elif game and game.round:

            # message was sent from current player in game round
            if author_id == game.round.current_player.fb_id:
                game.round.process_action(message) # game continuation

        # messages sent privately to the dealer (data requests / data modification requests)
        elif kwargs['thread_type'] == ThreadType.USER and message in PRIVATE_STATEMETNS:
            test_path = [path for path in Path(DATABASE).iterdir() if path.suffix == '.json' and path.name[:-5] == author_id]
            assert len(test_path) <= 1

            # if the author is not inside the database notify the author and end the execution
            if not test_path:
                return self.sendMessage('You are not in the database', thread_id = thread_id)

            confirmed_path = test_path[0]
            data = FileMethods.fetch_database_json(confirmed_path)

            # player requested to see the money from the database
            if message.lower() == SHOW_USER_MONEY:
                self.sendMessage(f"You have {data['money']} left", thread_id = author_id, thread_type = ThreadType.USER)

            elif message.lower() == REQUEST_FOR_MONEY:
                timestamp = TimeMethods.formatted_timestamp()
                diff = TimeMethods.get_time_diff(timestamp, data['timestamp'])

                if diff['days'] or diff['hours'] >= MONEY_WAITING_PERIOD:
                    data['timestamp'] = timestamp
                    data['money'] += MONEY_ADD_PER_PERIOD
                    FileMethods.send_to_database(confirmed_path, data)
                    self.sendMessage(str(MONEY_ADD_PER_PERIOD) + " successfully added", thread_id = thread_id)
                else:
                    remainder = TimeMethods.get_time_remainder(timestamp, data['timestamp'], MONEY_WAITING_PERIOD)
                    to_wait = ', '.join([str(remainder[timeframe]) + ' ' + timeframe for timeframe in remainder if remainder[timeframe]])
                    self.sendMessage("Money Can Be Requested in " + to_wait, thread_id = thread_id)

    def add_game(self, table_id, big_blind = BIG_BLIND):
        if table_id not in self.games:
            self.games[table_id] = FbPokerGame(PlayerGroup(self.fetch_players_on_table(table_id)), big_blind, table_id)
            return True
        return False

    # this happens ONLY when the game is forcibly ended by removing the dealer mid-game
    def remove_game(self, table_id):
        for player in self.games.pop(table_id).all_players:
            player.resolve()

    def start_round(self, table_id):
        game = self.games[table_id]
        if not game.round and game.is_ok():
            game.new_round()
            return True
        return False

    def fetch_uids_on_table(self, table_id) -> set: # without dealer (dealer on the table is trivial)
        return {uid for uid in self.fetchGroupInfo(table_id)[table_id].participants if uid != self.uid} # set of user ids
    def fetch_players_on_table(self, table_id) -> list:
        return [FbPlayer(user_info.name, user_info.uid, table_id) for user_info in [self.fetchUserInfo(uid)[uid] for uid in self.fetch_uids_on_table(table_id)]]

    ## these functions serve non-essential purpuse of dealer interaction with single user

    # this makes a random threat to user_id if there are threats
    def make_threat(self, user_id):
        pth = Path('quotes')
        if pth.is_dir():
            user_name = self.fetchUserInfo(user_id)[user_id].name.split()[0]
            choice_list = list(pth.iterdir())
            if choice_list:
                file_name = choice(choice_list)
                send = FileMethods.fetch_database_txt(file_name)
                return self.sendMessage(send.format(name = user_name), thread_id = user_id, thread_type = ThreadType.USER)


class FbPlayer(Player):

    def __init__(self, name: str, fb_id: str, table_id: str):
        self.data_path = DATABASE / (fb_id + '.json')

        self.name = name
        self.fb_id = fb_id
        self.table_id = table_id

        if self.data_path.is_file():
            file_data = FileMethods.fetch_database_json(self.data_path)
            money = TABLE_MONEY if file_data['money'] >= TABLE_MONEY else available_money['money']
            file_data['money'] -= money
            file_data['table_money'][self.table_id] = money
            FileMethods.send_to_database(self.data_path, file_data)
        else: # new player
            money = TABLE_MONEY
            FileMethods.create_datafile(self.data_path, self.get_base_datafile())

        super().__init__(self.name, money)
        self.id = fb_id

    @property
    def money(self):
        return self.__money

    @money.setter
    def money(self, value):
        self.__money = value
        data = FileMethods.fetch_database_json(self.data_path)
        data['table_money'][self.table_id] = value
        FileMethods.send_to_database(self.data_path, data)

    def get_base_datafile(self):
        return dict(
        name = self.name,
        money = PLAYER_STARTING_MONEY - TABLE_MONEY,
        table_money = {self.table_id: TABLE_MONEY},
        timestamp = TimeMethods.formatted_timestamp())

    def refill_money(self):
        if self.money >= TABLE_MONEY:
            return False

        file_data = FileMethods.fetch_database_json(self.data_path)
        __money = file_data['money']
        money_to_fill = TABLE_MONEY - self.money

        if __money >= money_to_fill:
            self.money += money_to_fill
            file_data['money'] -= money_to_fill
            return money_to_fill
        else:
            self.money += __money
            file_data['money'] = 0
            return __money

    def withdraw_money(self):
        file_data = FileMethods.fetch_database_json(self.data_path)
        file_data['money'] += file_data['table_money'][self.table_id]
        file_data['table_money'][self.table_id] = 0
        FileMethods.send_to_database(self.data_path, file_data)
        self.money = 0

    # called when player leaves the table (or game ends)
    def resolve(self):
        file_data = FileMethods.fetch_database_json(self.data_path)
        file_data['money'] += file_data['table_money'][self.table_id]
        file_data['table_money'].pop(self.table_id)
        FileMethods.send_to_database(self.data_path, file_data)
        self.money = 0


class FbPokerGame(PokerGame):
    IO_actions = {
    'Dealt Cards': lambda cards: FbPokerGame.style_cards(cards),
    'Raise Amount Error': lambda: 'Raising less than big blind is not allowed unless going all in',
    'New Round': lambda round_index: (" Round " + str(round_index) + " ").center(40, '-'),
    'Small Blind': lambda player_id, player_name, given: player_name + ' posted the Small Blind of ' + str(given),
    'Big Blind': lambda player_id, player_name, given: player_name + ' posted the Big Blind of ' + str(given),
    'New Turn': lambda turn_name, table: turn_name + ':\n' + FbPokerGame.style_cards(table),
    'To Call': lambda player_name, player_id, to_call: player_name + str(to_call) if to_call > 0 else player_name,
    'Player Went All-In': lambda player_id, player_name, player_money: player_name + ' went all-in with ' + str(player_money),
    'Declare Unfinished Winner': lambda winner_id, winner_name, won: winner_name + ' won ' + str(won),
    'Public Show Cards': lambda player_id, player_name, player_cards: player_name + ' has ' + FbPokerGame.style_cards(player_cards),
    'Declare Finished Winner': lambda winner_id, winner_name, won, hand_name, hand_base, kicker: winner_name + ' won ' + str(won) + ' with ' +
     FbPokerGame.hand_repr(hand_name, hand_base, VALUES, SUITS) + ''.join([', ' + FbPokerGame.style_cards(kicker, True) + ' kicker' if kicker else ''])
    }

    @staticmethod
    def style_cards(cards, kicker=False):
        if kicker is False:
            return '  '.join(VALUES[val] + SUITS[suit] for val, suit in cards)
        else:
            return '+'.join(VALUES[kick] for kick in cards)

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
            send = FbPokerGame.IO_actions[kwargs.pop('_id')](**kwargs)

        if send:
            DEALER.sendMessage(send, thread_id = player.fb_id, thread_type = ThreadType.USER)

    def public_out(self, text = None, **kwargs):
        send = None
        if text:
            send = text
        elif kwargs['_id'] in FbPokerGame.IO_actions:
            send = FbPokerGame.IO_actions[kwargs.pop('_id')](**kwargs)

        if send:
            DEALER.sendMessage(send, thread_id = self.table_id, thread_type = ThreadType.GROUP)


# this has to be done before every game
def collect_leftover_money():
    for file in Path(DATABASE).iterdir():
        if file.suffix == '.json':
            file_data = FileMethods.fetch_database_json(file)
            file_data['money'] += sum(file_data['table_money'][table] for table in file_data['table_money'])
            file_data['table_money'] = {}
            FileMethods.send_to_database(file, file_data)

collect_leftover_money()

# game continuation
if __name__ == '__main__':
    DATABASE.mkdir(parents=True, exist_ok=True) # make the directory if one doesn't exist
    DEALER = Dealer(DEALER_MAIL, DEALER_PASSWORD)
    DEALER.listen()
