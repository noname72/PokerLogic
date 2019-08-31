from enum import IntEnum

class Value(IntEnum):
    TWO = 0
    THREE = 1
    FOUR = 2
    FIVE = 3
    SIX = 4
    SEVEN = 5
    EIGHT = 6
    NINE = 7
    TEN = 8
    JACK = 9
    QUEEN = 10
    KING = 11
    ACE = 12

class Suit(IntEnum):
    SPADE = 0
    CLUB = 1
    DIAMOND = 2
    HEART = 3

class Hand(IntEnum):
    HIGHCARD = 0
    ONEPAIR = 1
    TWOPAIR = 2
    THREEOFAKIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULLHOUSE = 6
    FOUROFAKIND = 7
    STRAIGHTFLUSH = 8
    

class Turn(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3

class PlayerAction(IntEnum):
    FOLD = 0
    CHECK = 1
    CALL = 2
    RAISE = 3
    ALLIN = 4

class PrivateOutId(IntEnum):
    DEALTCARDS = 0

class PublicOutId(IntEnum):
    NEWTURN = 0
    WENTALLIN = 1
    SMALLBLIND = 2
    BIGBLIND = 3
    PLAYERRAISED = 4
    PLAYERCALLED = 5
    PLAYERCHECKED = 6
    PLAYERAMOUNTTOCALL = 7
    DECLAREUNFINISHEDWINNER = 8
    
