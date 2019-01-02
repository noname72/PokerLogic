# originaly made with fbchat Version 1.3.9

from sys import path
from random import choice
from pathlib import Path
from fbchat import Client
path.append(str(Path().cwd().parent)) # so i can use absolute paths
from fbchat.models import *
from lib import sqlmeths, timemeths
from lib.pokerlib import PlayerGroup, Player, PokerGame

# this is the documentation and the link is sent to every new player
DOCUMENTATION_URL = 'https://kuco23.github.io/pokermessinger/documentation.html'

DATABASE = Path('data') # database of player .json files

TABLE_MONEY = 1000 # money that a new player gets
BIG_BLIND = TABLE_MONEY // 50 # big_blinds at every table

PLAYER_STARTING_MONEY = 4000 # new player gets this at the start of the game
MONEY_WAITING_PERIOD = 4 # how long until a player can re-request for money
MONEY_ADD_PER_PERIOD = 100 # how much a player gets if he requests for money

VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = ['♠', '♣️', '♦️', '♥️']

# valid statements that a dealer receives from players (they should all be lowercase)
INITIALIZE_GAME = '::init' # adds a FbPokerGame object to the Dealer instance attribute dict
START_GAME = '::start' # executes a series of round
TOGGLE_LAST_ROUND = '::lastround' # toggles the round being played

BUY_IN = '::buyin' # adds player to the game
LEAVE_TABLE = '::leave' # removes player from game / folds his hand before if he is participating in a round
REFILL_TABLE_MONEY = '::refill' # refills user table money to TABLE_MONEY (takes it from his main money)
SHOW_USER_TABLE_MONEY = '::money' # shows how much money user has on the table

INITIALIZE_PLAYER = 'sign up' # initializes player and gives him the starting money
SHOW_USER_MONEY = 'show money' # shows player main money
REQUEST_FOR_MONEY = 'gimme moneyz' # requests for MONEY_ADD_PER_PERIOD

GAME_MANIPULATION_STATEMENTS = [INITIALIZE_GAME, START_GAME, TOGGLE_LAST_ROUND, LEAVE_TABLE, BUY_IN, REFILL_TABLE_MONEY, SHOW_USER_TABLE_MONEY]
PRIVATE_STATEMETNS = [SHOW_USER_MONEY, REQUEST_FOR_MONEY, INITIALIZE_PLAYER]
MID_GAME_STATEMENTS = ['call', 'fold', 'check', 'all in'] # these must remain the same
STATEMENTS = GAME_MANIPULATION_STATEMENTS + PRIVATE_STATEMETNS + MID_GAME_STATEMENTS

class Dealer(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = {} # dict {thread_id: game_object}

    def onPersonRemoved(self, removed_id, author_id, thread_id, **kwargs):
        if thread_id in self.games: # if a game isnt played on the table there isnt anything to do
            if removed_id == self.uid: # if a dealer is removed, remove game on that table from games
                self.make_threat(author_id) # make a threat so user will remember not to remove you from the game ever again
                self.remove_game(thread_id) # this is where game is removed and ended forcibly (SHOULDN'T HAPPEN)

            elif author_id != removed_id: # player only can remove himself
                self.addUsersToGroup([removed_id], thread_id = thread_id)
            else:
                game = self.games[thread_id]
                player = game.players['fb_id', removed_id]
                if player:
                    game.on_player_leave(player)
                    player.resolve()

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        message = message.lower()
        if author_id == self.uid or (message not in STATEMENTS and not message.startswith('raise ')):
            return None

        game = self.games[thread_id] if thread_id in self.games else None

        # messages sent from a group (game manipulation messages)
        if kwargs['thread_type'] == ThreadType.GROUP and message in GAME_MANIPULATION_STATEMENTS:

            if message == INITIALIZE_GAME:
                if not game:
                    self.games[thread_id] = FbPokerGame(PlayerGroup([]), BIG_BLIND, thread_id)
                    self.sendMessage('This group was initialized as a poker table', thread_id = thread_id, thread_type = ThreadType.GROUP)
                else:
                    self.sendMessage("This group is already initialized as a poker table", thread_id = thread_id, thread_type = ThreadType.GROUP)

            elif message == START_GAME:
                if not game:
                    self.sendMessage('This group had not yet been initialized as a poker table', thread_id = thread_id, thread_type = ThreadType.GROUP)
                elif game and game.round:
                    self.sendMessage('Rounds are already being played on this table', thread_id = thread_id, thread_type = ThreadType.GROUP)
                elif game and not game.round:
                    if not game.is_ok():
                        self.sendMessage('Not enough players have bought into the game. To buy in, type "buy in"',
                        thread_id = thread_id, thread_type = ThreadType.GROUP)
                    else:
                        self.sendMessage(f'A series of rounds will start. End them by typing "{TOGGLE_LAST_ROUND}"',
                        thread_id = thread_id, thread_type = ThreadType.GROUP)
                        game.new_round()

            elif message == BUY_IN:
                if not game:
                    self.sendMessage('This group had not yet been initialized as a poker table',
                    thread_id = thread_id, thread_type = ThreadType.GROUP)
                elif game.players['fb_id', author_id]:
                    self.sendMessage('You are already playing in this game. If you wish to refill your money use "{REFILL_TABLE_MONEY}" statement',
                    thread_id = thread_id, thread_type = ThreadType.GROUP)
                elif len(game.all_players) >= 9:
                    self.sendMessage('There is already a maximum amount of players playing on this table',
                    thread_id = thread_id, thread_type = ThreadType.GROUP)
                else:
                    user_info = self.fetchUserInfo(author_id)[author_id]
                    try:
                        player = FbPlayer(user_info.name, user_info.uid, thread_id)
                        game.on_player_join(player)
                        self.sendMessage(user_info.name + ' has bought into the game with ' + str(player.money),
                        thread_id = thread_id, thread_type = ThreadType.GROUP)
                    except AssertionError:
                        self.sendMessage('You have not signed up yet', thread_id = thread_id, thread_type = ThreadType.GROUP)
                        return None

            # from now on everything requires for a game to be played and that a player in that game wrote the message
            player = game.all_players['fb_id', author_id] if game else None
            if not player:
                return None

            if message == TOGGLE_LAST_ROUND:
                if game.round:
                    game.round.exit_after_this = not game.round.exit_after_this
                    _send = 'game will end after this round' if game.round.exit_after_this else 'game will continue'
                    self.sendMessage(_send, thread_id = thread_id, thread_type = ThreadType.GROUP)

            # player wants to get all money out of the table (player has to be folded or rounds not played)
            elif message == LEAVE_TABLE:
                self.sendMessage(player.name + ' has left the game', thread_id = thread_id, thread_type = ThreadType.GROUP)
                game.on_player_leave(player)
                player.resolve()

            # player wants to refill his money on the playing table
            elif message == REFILL_TABLE_MONEY:
                if not game.round or player not in game.round.players or player.is_folded:
                    money_filled = player.refill_money()
                    if money_filled is not False:
                        self.sendMessage('Money successfully refilled by ' + str(money_filled) + ' to ' + str(player.money),
                        thread_id = thread_id, thread_type = ThreadType.GROUP)

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
            with sqlmeths.connect(DATABASE) as connection:
                assert connection
                sql_data = sqlmeths.getasdict(connection, 'fbid', thread_id)

            # player wants to be signed up
            if message == INITIALIZE_PLAYER:
                if sql_data:
                    self.sendMessage('You are already in the database',
                    thread_id = thread_id)
                else:
                    sqlmeths.insert(DATABASE, 'players',
                        name = self.fetchUserInfo(author_id)[author_id].name,
                        money = PLAYER_STARTING_MONEY,
                        timestamp = timemeths.formatted_timestamp()
                    )
                    self.sendMessage(f'''
                    Welcome {user_info.name}!,
                    {PLAYER_STARTING_MONEY} was added to your account.\n
                    For more info about the game check the documentation\n
                    {DOCUMENTATION_URL}''',
                    thread_id = thread_id)

            # if the author is not inside the database
            # notify the author and end the execution
            elif not sql_data:
                return self.sendMessage(f'''You are not in the database,
                type "{INITIALIZE_PLAYER}" to be added''',
                thread_id = thread_id)

            # player requested to see the money from the database
            if message == SHOW_USER_MONEY:
                self.sendMessage(f"You have {sql_data['money']} left",
                thread_id = author_id, thread_type = ThreadType.USER)

            elif message == REQUEST_FOR_MONEY:
                timestamp = timemeths.formatted_timestamp()
                diff = timemeths.get_time_diff(timestamp, sql_data['timestamp'])

                if diff['days'] or diff['hours'] >= MONEY_WAITING_PERIOD:
                    sql_data['timestamp'] = timestamp
                    sql_data['money'] += MONEY_ADD_PER_PERIOD
                    sqlmeths.update(DATABASE, 'players', sql_data, {'fbid': thread_id})
                    self.sendMessage(str(MONEY_ADD_PER_PERIOD) + " successfully added",
                    thread_id = thread_id)
                else:
                    remainder = timemeths.get_time_remainder(timestamp, data['timestamp'], MONEY_WAITING_PERIOD)
                    to_wait = ', '.join([str(remainder[timeframe]) + ' ' + timeframe for timeframe in remainder if remainder[timeframe]])
                    self.sendMessage("Money Can Be Requested in " + to_wait, thread_id = thread_id)

    # this happens ONLY when the game is forcibly ended by removing the dealer mid-game
    def remove_game(self, table_id):
        for player in self.games.pop(table_id).all_players:
            player.resolve()

    ## these functions serve non-essential purpuse of dealer interaction with single user

    # this makes a random threat to user_id if there are threats
    def make_threat(self, user_id):
        pth = Path('quotes')
        if pth.is_dir():
            user_name = self.fetchUserInfo(user_id)[user_id].name.split()[0]
            choice_list = list(pth.iterdir())
            if choice_list:
                file_name = choice(choice_list)
                with open(file_name, 'r', encoding='UTF-8') as file:
                    send = ''.join(file.readlines())
                return self.sendMessage(send.format(name = user_name),
                thread_id = user_id, thread_type = ThreadType.USER)

class FbPlayer(Player):

    def __init__(self, name: str, fb_id: str, table_id: str):

        self.name = name
        self.fb_id = fb_id
        self.table_id = table_id

        db_data = sqlmeths.getasdict(DATABASE, 'players', 'fbid', fb_id)
        money = TABLE_MONEY if db_data['money'] >= TABLE_MONEY else db_data['money']
        db_data['money'] -= money
        #db_data['table_money'][self.table_id] = money
        sqlmeths.update(DATABASE, 'people', db_data, {'fbid': fbi_id})

        super().__init__(self.name, money)
        self.id = fb_id

    @property
    def money(self):
        return self.__money

    #############
    @money.setter
    def money(self, value):
        self.__money = value
        data = sqlmeths.getasdict(DATABASE, 'tablemoneys', 'fbid': self.fb_id)
        data['table_money'][self.table_id] = value
        sqlmeths.update(self.data_path, data)

    def refill_money(self):
        if self.money >= TABLE_MONEY:
            return False

        file_data = sqlmeths.getasdict(DATABASE, 'players', 'fbid': self.fb_id)
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

    # called when player leaves the table (or game ends)
    ##########
    def resolve(self):
        pl_data = sqlmeths.getasdict(DATABASE, 'players', 'fbid': self.fb_id)
        tblmoney_data = sqlmeths.getdicts(DATABASE, 'playermoneys', 'fbid': self.fb_id)
        pl_data['money'] += pl_data['table_money'][self.table_id]
        self.money = 0
        pl_data['table_money'].pop(self.table_id)
        sqlmeths.send_to_database(self.data_path, pl_data)


class FbPokerGame(PokerGame):
    IO_actions = {
    'Dealt Cards': lambda cards: FbPokerGame.style_cards(cards),
    'Raise Amount Error': lambda: 'Raising less than big blind is not allowed unless going all in',
    'New Round': lambda round_index: (" Round " + str(round_index) + " ").center(40, '-'),
    'Small Blind': lambda player_id, player_name, given: player_name + ' posted the Small Blind of ' + str(given),
    'Big Blind': lambda player_id, player_name, given: player_name + ' posted the Big Blind of ' + str(given),
    'New Turn': lambda turn_name, table: turn_name + ':\n' + FbPokerGame.style_cards(table),
    'To Call': lambda player_name, player_id, to_call: player_name + '\n' + str(to_call) + ' to call' if to_call > 0 else player_name,
    'Player Went All-In': lambda player_id, player_name, player_money: player_name + ' went all-in with ' + str(player_money),
    'Declare Unfinished Winner': lambda winner_id, winner_name, won: winner_name + ' won ' + str(won),
    'Public Show Cards': lambda player_id, player_name, player_cards: player_name + ' has ' + FbPokerGame.style_cards(player_cards),
    'Declare Finished Winner': lambda winner_id, winner_name, won, hand_name, hand_base, kicker: winner_name + ' won ' + str(won) + ' with ' +
     FbPokerGame.hand_repr(hand_name, hand_base, VALUES, SUITS) + ''.join([', ' + FbPokerGame.style_cards(kicker, True) + ' kicker' if kicker else '']),
    'Player Lost Money': lambda player_id, player_name: player_name + ' has been removed from the game'
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
for file in Path(DATABASE).iterdir():
    if file.suffix == '.json':
        file_data = sqlmeths.fetch_database_json(file)
        file_data['money'] += sum(file_data['table_money'][table] for table in file_data['table_money'])
        file_data['table_money'] = {}
        sqlmeths.send_to_database(file, file_data)

players_sql = '''
CREATE TABLE IF NOT EXISTS players(
    id integer PRIMARY KEY,
    fbid integer NOT NULL,
    name text NOT NULL,
    money integer,
    timestamp text
)
'''
tablemoneys_sql = '''
CREATE TABLE IF NOT EXISTS tablemoneys(
    id integer PRIMARY KEY,
    fbid integer NOT NULL,
    tblid integer NOT NULL,
    money integer
)
'''
# game continuation
if __name__ == '__main__':
    DEALER_MAIL = input('Dealer email: ')
    DEALER_PASSWORD = input('Dealer password: ')
    DEALER = Dealer(DEALER_MAIL, DEALER_PASSWORD)
    DEALER.listen()
