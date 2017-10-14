import numpy as np
from scipy.misc import comb


class HandAnalyzer(object):
    """
    Given a string of the form 'ac2d9htskc' treat that as a 5 card poker hand:
    Ace of Clubs, Two of Diamonds, Nine of Hearts, Ten of Spades, King of Clubs".

    Analyze the counts possible winning hands based on holding or discarding any
    combination of the 5 cards. Optionally input a payout table as a dictionary
    of the form below. The default payout table is from "9-6 Jacks or Better"
    Video Poker.
    payouts = {'pair_jjqqkkaa': 1, '2_pair': 2, '3_of_a_kind': 3,
               'straight': 4, 'flush': 6, 'full_house': 9, '4_of_a_kind': 25,
               'straight_flush': 50, 'royal_flush': 800}

    To Do: add wild card functionality for versions like Deuces Wild, Jokers.

    INPUT:
    hand: (str) Ten character string of rank/suit for 5 cards.
            rank chars: a23456789tjqk, suit chars: cdhs. Case Insensitive.
    payouts: (dict) Amount paid for a given winning hand. Accepts any subset of
            the following keys: 'pair_jjqqkkaa', '2_pair', '3_of_a_kind',
            'straight', 'flush', 'full_house', '4_of_a_kind', 'straight_flush'
            'royal_flush'
    OUTPUT:
    None
    """

    def __init__(self, hand, payouts = None):
        if payouts is None:
            self.payouts = {'pair_jjqqkkaa': 1, '2_pair': 2, '3_of_a_kind': 3,
                            'straight': 4, 'flush': 6, 'full_house': 9,
                            '4_of_a_kind': 25, 'straight_flush': 50,
                            'royal_flush': 800}
        else:
            self.payouts = payouts

        #rewrite hand string as list of 5 cards of 2 chars
        self.hand = [hand[ind:ind+2].upper() for ind in range(0,10,2)]

        #generate lookup dict for accessing deck array
        ranks = 'A23456789TJQK'
        suits = 'CDHS'
        cells = {}
        for i, rank in enumerate(ranks):
            for j, suit in enumerate(suits):
                cells[rank+suit] = (i, j)
        self.__c2a = cells

        deck = np.zeros([13, 4])
        for card in self.hand:
            deck[cells[card]] = 1
        self.__deck = deck

    def deck_array(self):
        return self.__deck
