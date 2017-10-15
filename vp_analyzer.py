from itertools import product
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
            the following keys: 'pair_jjqqkkaa', 'two_pair', 'three_kind',
            'straight', 'flush', 'full_house', 'four_kind', 'straight_flush'
            'royal_flush'
    OUTPUT:
    None
    """

    def __init__(self, hand, payouts = None):
        if payouts is None:
            self.payouts = {'pair_jjqqkkaa': 1, 'two_pair': 2, 'three_kind': 3,
                            'straight': 4, 'flush': 6, 'full_house': 9,
                            'four_kind': 25, 'straight_flush': 50,
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
        locs = []
        for card in self.hand:
            locs.append(cells[card])
            deck[cells[card]] = 1
        self.__locs = locs
        self.__deck = deck

    def deck_array(self):
        return self.__deck

    def hold(self, held = [True]*5):
        arr = self.__deck.copy()
        for loc, held_bool in zip(self.__locs, held):
            if not held_bool:
                arr[loc] = -1
        return arr

    def suits_held(self, deck_state):
        """
        returns boolean array of shape (4,), suits are in order [Clubs, Diamonds,
        Hearts, Spades]
        """
        return ((deck_state == 1).sum(axis = 0) > 0) == 1

    def num_ranks_unseen(self, deck_state):
        """
        number of ranks with all 4 suits missing from initial deal
        """
        return ((deck_state == 0).sum(axis = 1) == 4).sum()



    def royal_flush(self, deck_state, num_discards):
        # Not holding 2-9
        if (deck_state[1:9,:] == 1).any():
            return 0
        # Holding 0 or 1 suit
        royals = deck_state[[0,9,10,11,12], :]
        suits = self.suits_held(royals)
        if suits.sum() > 1:
            return 0
        # elif not suits.any():
        #    return 4
        elif suits.sum() == 1:
            #held and discarded royal of same suit
            if (royals[:, suits == 1] == -1).any():
                return 0
            else:
                return 1
        #count suits w/o discarded high cards
        else:
            suits_no_discard = (royals == -1).sum(axis=0) == 0
            return suits_no_discard.sum()


    def three_kind(self, deck_state, num_discards):

        ranks_held = (deck_state == 1).sum(axis = 1)
        if num_discards == 0:
            #no trips or trips +
            if (ranks_held != 3).all():
                return 0
            #full house
            elif (ranks_held == 2).any():
                return 0
            else:
                return 1
        elif num_discards == 1:
            if (ranks_held == 3).any():
                return 11*4
            elif (ranks_held == 2).sum() == 1:
                (deck_state[ranks_held == 2, :] == 0) 






    def analyze(self):
        win_props = {}
        win_counters = {'royal_flush':self.royal_flush}
        for hold_l in product([True, False], repeat=5):
            deck_state = self.hold(held = hold_l)
            ways_to_win = {}
            expected_val_numerator = 0
            for win in self.payouts:
                win_count = win_counters[win](deck_state)
                expected_val_numerator += self.payouts[win] * win_count
                ways_to_win[win] = win_count

            exp_val_denom = float(comb(47, 5-sum(hold_l)))
            ways_to_win['expected_val'] = expected_val_numerator / exp_val_denom
            hand = tuple(card if held else 'X' for card, held in zip(self.hand, hold_l))
            win_props[hand] = ways_to_win

        return win_props
