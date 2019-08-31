from operator import add
from math import inf
from random import sample

from pokerlib.enums import *
from pokerlib.player import Player, PlayerGroup
from pokerlib.handparser import HandParser, HandParserGroup

# Round doesn't check for:
# - all in calls,
# - all in raises,
# - unvalid checks (check when call is needed)
# - button identifying an active player

# Round argument players should be
# - players should be implemented singletons

class Round:
    __deck = [[value, suit] for suit in Suit for value in Value]

    def __init__(self, players, button, small_blind, big_blind):
        self.big_blind = big_blind
        self.small_blind = small_blind
        
        self.players = players
        self.button = button
        self.current_index = button
        
        self.table = list()
        self.deck = self.deckIterator()

        self.turn = None
        self.turn_generator = self.turnGenerator()

        for player in self.players:
            player.reset()
            player.cards = (next(self.deck), next(self.deck))
            player.hand = HandParser(list(player.cards))

            self.privateOut(
                PrivateOutId.DEALTCARDS,
                player.id,
                cards = player.cards
            )     

        next(self.turn_generator)
        self.dealBlinds()
        self.processState()

    @property
    def current_player(self):
        return self.players[self.current_index]

    @property
    def turn_stake(self):
        return max(map( 
            lambda player: player.turn_stake[self.turn],
            self.players
        ))

    @property
    def pot_size(self):
        return list(map(lambda i: sum(map(
            lambda player: player.turn_stake[i],
            self.players
            ))
        ))

    @property
    def pots_balanced(self):
        active_pots = [
            player.turn_stake[self.turn]
            for player in self.players
            if player.is_active
        ] or [inf]
        
        all_in_max_pot = max([
            player.turn_stake[self.turn]
            for player in self.players
            if player.is_all_in
        ] or [0])
        
        return (
            len(set(active_pots)) == 1 and
            active_pots[0] >= all_in_max_pot
        )
    
    def deckIterator(self):
        ncards = len(self.players) * 2 + 5
        return iter(sample(self.__deck, ncards))

    def turnGenerator(self):
        for i, turn in zip((0,3,1,1), Turn):
            self.turn = turn   
            new_cards = [next(self.deck) for _ in range(i)]
                                      
            for player in self.players:
                player.played_turn = False
                player.hand.addCards(new_cards)
                player.hand.parse()

            self.table.extend(new_cards)
            
            self.publicOut(
                PublicOutId.NEWTURN,
                turn_name = turn,
                table = self.table
            )
                                
            yield


    def shiftCurrentPlayer(self):
        i = self.current_index
        self.current_index = self.players.nextActiveIndex(i)
            
    def addToPot(self, player, money):
        if 0 <= money < player.money:
            player.money -= money
            player.turn_stake[self.turn] += money
            player.stake += money
        else:
            player.turn_stake[self.turn] += player.money
            player.stake += player.money
            player.money = 0
            player.is_all_in = True
            
            self.publicOut(
                PublicOutId.PLAYERALLIN,
                player_id = player.id
            )

    def dealBlinds(self):
        i = self.current_index
        
        previous_player = self.players.previousActivePlayer(i)
        self.addToPot(previous_player, self.small_blind)
        
        self.publicOut(
            PublicOutId.SMALLBLIND,
            player_id = previous_player.id,
            turn_stake = previous_player.turn_stake[0]
        )

        self.addToPot(self.current_player, self.big_blind)
        
        self.publicOut(
            PublicOutId.BIGBLIND,
            player_id = self.current_player.id,
            turn_stake = self.current_player.turn_stake[0]
        )

    def dealPrematureWinnings(self):
        winner = self.players.getNotFoldedPlayers()[0]
        won = sum(self.pot_size)
        winner.money += won

        self.publicOut(
            PublicOutId.DECLAREPREMATUREWINNER,
            player_id = winner.id,
            won = won,
        )

    def dealWinnings(self):
        stake_sorted = type(self.players)(add(
            sorted(
                [player for player in self.players if player.is_all_in],
                key = lambda player: player.stake
            ),
            sorted(
                [player for player in self.players if player.is_active],
                key = lambda player: player.stake
            )
        ))

        for competitor in stake_sorted:
            self.publicOut(
                PublicOutId.PUBLICCARDSHOW,
                player_id = competitor.id
            )

        grouped_indexes = [0]
        for i in range(1, len(stake_sorted)):
            if stake_sorted[i - 1].stake < stake_sorted[i].stake:
                grouped_indexes.append(i)

        for i in grouped_indexes:
            subgame_competitors = stake_sorted[i:]
            subgame_stake = subgame_competitors[0].stake

            hands = [p.hand for p in subgame_competitors]
            hands = HandParserGroup(hands)
            kickers = hands.getGroupKickers()
            
            winning_players = subgame_competitors.winners()
            nsplit = len(winning_players)
            
            take_from = []
            for player in self.players:
                if 0 < player.stake <= subgame_stake:
                    take_from.append(player.stake / nsplit)
                elif 0 < subgame_stake <= player.stake:
                    take_from.append(subgame_stake / nsplit)
                else: take_from.append(0)
            
            for win_split in winning_players:
                win_took = 0
                
                for player, take in zip(self.players, take_from):
                    win_took += take
                    player.stake -= take

                if round(win_took):
                    win_split.money += round(win_took)

                    self.publicOut(
                        PublicOutId.DECLAREFINISHEDWINNER,
                        winner_id = win_split.id,
                        won = round(win_took),
                        kicker = kickers
                    )
                        

    def processAction(self, action, raise_by=0):
        current_player = self.current_player
                 
        turn_stake = self.turn_stake
        to_call = turn_stake - current_player.turn_stake[self.turn]

        if action == PlayerAction.FOLD:
            self.current_player.is_folded = True

            self.publicOut(
                PublicOutId.PLAYERFOLD,
                player_id = current_player.id
            )

        elif action == PlayerAction.CHECK:
            self.publicOut(
                PublicOutId.PLAYERCHECK,
                player_id = current_player
            )
            
        elif action == PlayerAction.CALL:
            self.addToPot(current_player, to_call)

            self.publicOut(
                PublicOutId.PLAYERCALL,
                player_id = current_player.id,
                called = to_call
            )

        elif action == PlayerAction.RAISE:
            self.addToPot(current_player, turn_stake + raise_by)

            self.publicOut(
                PublicOutId.PLAYERRAISE,
                player_id = current_player,
                raised_by = raise_by
            )

        elif action == PlayerAction.ALLIN:
            self.addToPot(current_player, current_player.money)

        current_player.played_turn = True
        self.processState()
                
    def processState(self):
        active = len(self.players.getActivePlayers())
        not_folded = len(self.players.getNotFoldedPlayers())
        pots_balanced = self.pots_balanced

        if not_folded == 0:
            return self.close()
        
        elif not_folded == 1:
            self.dealPrematureWinnings()
            return self.close()

        elif active <= 1 and pots_balanced:
            for _ in self.turn_generator: pass
            self.dealWinnings()
            return self.close()

        elif self.players.allPlayedTurn() and pots_balanced:
            if self.turn == Turn.RIVER:
                self.dealWinnings()
                return self.close()
            else:
                self.current_index = self.button
                next(self.turn_generator)

        self.shiftCurrentPlayer()
        called = self.current_player.turn_stake[self.turn]

        self.publicOut(
            PublicOutId.PLAYERAMOUNTTOCALL,
            player_id = self.current_player.id,
            to_call = self.turn_stake - called
        )


    def close(self):
        return

        
    def privateOut(self, user_id, out_id, **kwargs):
        print(user_id, out_id, kwargs)
        # insert action
        return
    
    def publicOut(self, out_id, **kwargs):
        print(out_id, kwargs)
        # insert action
        return
