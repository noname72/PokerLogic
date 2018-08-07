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
    glob_message = None

    # add dealer's table_id (group_id) as an instance attribute
    def __init__(self, table_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_id = table_id

    # processing input from players and saving it into glob_message
    def onMessage(self, author_id, message, thread_id, **kwargs):
        if author_id == self.uid:
            pass

        elif thread_id == self.table_id:
            Dealer.glob_message = (author_id, message)
            print(message)
            self.listening = False

        elif message.lower() == 'add me' and author_id not in self.fetch_uids_on_table():
            self.addUsersToGroup([author_id], thread_id = self.table_id)
            if len(self.fetch_uids_on_table()) == 2:
                self.listening = False

        elif message.lower() == 'remove me' and author_id in self.fetch_uids_on_table():
            self.removeUserFromGroup(author_id, thread_id = self.table_id)
            Dealer.glob_message = (author_id, 'remove')
            self.listening = False

    def fetch_uids_on_table(self): # without dealer (dealer on the table is trivial)
        return {uid for uid in self.fetchGroupInfo(self.table_id)[self.table_id].participants if uid != self.uid} # set of user ids

DEALER = Dealer(TABLE_ID, DEALER_MAIL, DEALER_PASSWORD)
PLAYERS = [DEALER.fetchUserInfo(PLAYER)[PLAYER] for PLAYER in DEALER.fetch_uids_on_table()]

class FbPlayerGroup(PlayerGroup):
    def save_data(self, attr: str):
        for player in self:
            with open(player.data_path, 'w') as raw:
                print(player.__dict__[attr], file=raw)


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

    # every time a player attr is updated or reset, it is logged in a file
    def __setattr__(self, attr_name, value):
        object.__setattr__(self, attr_name, value)
        if attr_name == 'money':
            with open(self.data_path, 'w') as raw:
                print(self.money, file=raw)


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

    def create_datafile(self):
        with open(self.data_path, 'a') as raw:
            print(FbPlayer.base_money, file=raw)
        print(f"creating {self.name} database")

    def fetch_money_from_database(self):
        with open(self.data_path, 'r') as raw:
            data = raw.readlines()
        return int(data[0].strip())


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

    def __init__(self, players: FbPlayerGroup, big_blind: int, dealer: Dealer): # players is a PlayerGroup objects of FbPlayers
        super().__init__(players, big_blind)
        self.dealer = dealer

    # check if any new player has joined
    def update_players(self):
        # check if someone else joined or left the group and add or remove them
        old_ids = {player.fb_id for player in self.players}
        current_ids = self.dealer.fetch_uids_on_table()
        if current_ids != old_ids:
            for _id in old_ids.union(current_ids):
                if _id in current_ids and _id not in old_ids:
                    new_player = FbPlayer(self.dealer.fetchUserInfo(_id)[_id]) # here an explicit FbPlayer object is created
                    self.add_player(new_player)

                elif _id not in current_ids and _id in old_ids:
                    self.remove_player_by_id(_id)

    # remove player by his _id
    def remove_player_by_id(self, _id):
        for player in self.players:
            if player.fb_id == _id:
                self.players.remove(player)

    def public_out(self, text = None, **kwargs):
        send = None
        if text:
            send = text
        elif kwargs['_id'] in FbPokerGame.IO_actions:
            send = FbPokerGame.IO_actions[kwargs['_id']](kwargs)

        # using fb emojis to display suits
        for suit in EMOJI_DICT:
            send = send.replace(suit, EMOJI_DICT[suit])

        self.dealer.sendMessage(send, thread_id = self.dealer.table_id, thread_type = ThreadType.GROUP)


# PLAYERS THAT WANT TO LEAVE THE TABLE MUST SEND "remove me" TO THE DEALER OR IF "add me" IF THEY WANT TO BE ADDED TO TABLE
# game continuation
if __name__ == '__main__':
    players = FbPlayerGroup([FbPlayer(PLAYER) for PLAYER in PLAYERS])
    game = FbPokerGame(players, BIG_BLIND, DEALER)

    # initiate series of rounds while there are at least 2 players participating
    while True:
        game.update_players() # update players that left or that came (hue hue)

        # if there is one or 0 or 1 or > 9 (max players) players in group (not including the dealer) game should be in standby mode til more players join
        if not 2 <= len(game.players.get_participating_players()) <= 9:
            game.dealer.listen()
            continue

        game.new_round()
        # initiate every turn during which players consider actions
        for turn in ["PRE-FLOP", "FLOP", "TURN", "RIVER"]:
            game.new_turn(turn)

            # player that is right next to button plays first
            current_player = game.button

            # if all active players have not yet played or someone hasnt called turn continues (current_player inputs action)
            # if there is one player left his input doesnt matter, as he would raise or call only himself (buut there can be active not folded player that hasnt called an all_in player)
            while (not game.players.all_played_turn() or not game.pot_is_equal()) and (len(players.get_active_players()) >= 2 or not game.pot_is_equal()) and len(players.get_not_folded_players()) >= 2:

                # current player inputs action, which gets processed and validated or rejected
                current_player = game.players.next_active_player_from(current_player)

                # out how much money there is for a player to call
                to_call = game.get_money_to_call() - current_player.money_given[DIC[len(game.table)]]
                to_call_str = "\n" + str(to_call) + " to call" if to_call != 0 else ''
                game.public_out(current_player.name + to_call_str)
                while True:
                    game.dealer.listen()

                    # if player wants to be removed and player is in the game
                    if Dealer.glob_message and Dealer.glob_message[1] == 'remove' and Dealer.glob_message[0] in [player.fb_id for player in game.players]:
                        # set participation to false and wait for the end of roud for player to be removed
                        player_remove = [player for player in game.players if player.fb_id == Dealer.glob_message[0]][0]
                        player_remove.is_folded = True
                        player_remove.participating = False

                        if Dealer.glob_message[0] == current_player.fb_id: # if current_player left break the loop asking for his input
                            break

                    # player responded with action
                    elif Dealer.glob_message and Dealer.glob_message[0] == current_player.fb_id and game.process_action(current_player, Dealer.glob_message[1]):
                        Dealer.glob_message = None
                        break

            # everyone but one folded after playing actions so the winner
            if len(players.get_not_folded_players()) <= 1:
                break

        if len(game.players.get_not_folded_players()) >= 1:
            game.deal_winnings() # process winners and deal winnings to round winners
