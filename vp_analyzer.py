from collections import Counter
from itertools import combinations_with_replacement
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
        self.__h = [(card[0], card[1]) for card in self.hand]

        self.__ranks = 'A23456789TJQK'
        self.__suits = 'CDHS'

        self.__draws = Counter(self.__ranks*4) - Counter([c[0] for c in self.__h])

    def draws(self):
        return self.__draws

    def hold(self, held = [True]*5):
        held_d = {'h':[], 'd':[]}
        for card, held_bool in zip(self.__h, held):
            if held_bool:
                held_d['h'].append(card)
            else:
                held_d['d'].append(card)
        return held_d


    @staticmethod
    def pivot_held_d(held_d):
        ranks_suits = []
        for key in ['h', 'd']:
            if held_d[key] != []:
                ranks_suits.extend(list(zip(*held_d[key])))
            else:
                ranks_suits.extend([(), ()])
        return ranks_suits

    def royal_flush(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        holding_2to9 = set(held_r).intersection(set('23456789')) != set()
        exp_val_denom = comb(47, 5 - len(held_r))
        if holding_2to9 or (len(set(held_s)) > 1):
            return 0

        discarded_royal_suits = set()
        for card in held_d['d']:
            if (card[0] in 'AKQJT'):
                #check if held and discarded royal of same suit
                #already checked for multiple held suits, hence held_s[0]
                if (len(held_s) > 0) and (card[1] == held_s[0]):
                    return 0
                discarded_royal_suits.add(card[1])

        if len(set(held_s)) == 1:
            return 1, exp_val_denom
        else:
            return 4 - len(discarded_royal_suits), exp_val_denom

    def three_kind(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))
        # nothing held
        if held_r_cnts == []:
            draw5 = self.draw_for_ranks(held_d, gsize=3, cnt_held_only=False)
            return draw5, exp_val_denom
        # most common card is a singleton
        elif held_r_cnts[0][1] == 1:
            draws = self.draw_for_ranks(held_d, gsize=3, cnt_held_only=False)
            return draws, exp_val_denom
        elif held_r_cnts[0][1] == 2:

            #check for holding two pair, avoid counting FH
            if (len(held_r_cnts) > 1) and (held_r_cnts[1][1] == 2):
                return 0, 1

            drawp = self.draw_for_ranks(held_d, gsize=3, cnt_held_only=True)
            #if holding a pair and a 3rd card, e.g. 'AA7', drawing '77' will be
            #counted by draw_for_ranks, but this is FH, so subtract this.
            if (len(held_r_cnts) == 2) and (held_r_cnts[1][1] == 1):
                rext_avail = self.__draws[held_r_cnts[1][0]]
                return drawp - comb(rext_avail, 2), exp_val_denom
            else:
                return drawp, exp_val_denom
        elif held_r_cnts[0][1] == 3:
            #check for holding FH
            if (len(held_r_cnts) == 2) and (held_r_cnts[1][1] == 2):
                return 0, 1
            else:
                return 1, 1
        else:
            return 0, 1



    def draw_for_ranks(self, held_d, gsize = 2, cnt_held_only = False):
        """
        Given held cards and discards count ways to draw for pairs/3kind/4_of_a_kind
        based on collecting them purely from draw pile or adding to the held cards

        gsize: (2, 3, or 4) Size of group of cards to be made. e.g. pair = 2

        cnt_held_only: (bool). True: Obtain group by adding to held cards only,
            rather than drawing a group. e.g. a 'AA742' hand where you hold the
            aces and count 3kinds would include the:
            comb(9,1)*comb(4,3)+comb(3,1)*comb(3,3)=39
            ways of drawing trips that result in a full house.
            To avoid this, set False.

        """

        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        draw_cnt = len(held_d['d'])
        nonheld_ranks = self.__draws.copy()
        for r in held_r:
            nonheld_ranks[r] = 0

        nonheld_rank_grps = Counter(nonheld_ranks.values())
        ways_cnt = 0

        #add up ways of making group with all draw cards
        if not cnt_held_only:
            for avail, rcnt in nonheld_rank_grps.items():
                # count ranks that we can select 3 cards from.
                if gsize <= draw_cnt:
                    rways = rcnt * comb(avail, gsize)
                    kickers = draw_cnt - gsize
                    if kickers > 0:
                        new_nhrg = nonheld_rank_grps.copy()
                        new_nhrg[avail] -= 1
                        kick_ways = self.count_ways2kick(new_nhrg,
                                                         num_kickers = kickers)
                    else:
                        kick_ways = 1
                    #print(rcnt, avail, kick_ways, rways)
                    ways_cnt += rways * kick_ways
                else:
                    continue

        #add up ways of adding to the held cards
        for r, hcnt in Counter(held_r).items():
            needed = gsize - hcnt
            if needed <= draw_cnt:
                hways = comb(self.__draws[r], needed)
                kickers = draw_cnt - needed
                if kickers > 0:
                    kick_ways = self.count_ways2kick(nonheld_rank_grps,
                                                     num_kickers = kickers)
                else:
                    kick_ways = 1
                print(hcnt, kickers, kick_ways, hways)

                ways_cnt += hways * kick_ways
            else:
                continue

        return ways_cnt



    @staticmethod
    def count_ways2kick(nonheld_rank_grps, num_kickers = 1):
        # possible combinations, if num_kickers = 2 and there are 8 ranks with 4
        # cards to draw one elem will be (4, 4), so run counter on this to get things
        # to work properly. then comb(8, 2)*comb(4, 1)**2
        kick_cnt = 0
        for suit_cnt_tup in combinations_with_replacement(nonheld_rank_grps, num_kickers):
            multiplier = 1
            for suit_cnt_key, cnt in Counter(suit_cnt_tup).items():
                num_ranks = nonheld_rank_grps[suit_cnt_key]
                multiplier *= comb(num_ranks, cnt) * suit_cnt_key ** cnt
            kick_cnt += multiplier
        return kick_cnt


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










    # def hold(self, held = [True]*5):
    #     arr = self.__deck.copy()
    #     for loc, held_bool in zip(self.__locs, held):
    #         if not held_bool:
    #             arr[loc] = -1
    #     return arr
    #
    # def suits_held(self, deck_state):
    #     """
    #     returns boolean array of shape (4,), suits are in order [Clubs, Diamonds,
    #     Hearts, Spades]
    #     """
    #     return ((deck_state == 1).sum(axis = 0) > 0) == 1
    #
    # def num_ranks_unseen(self, deck_state):
    #     """
    #     number of ranks with all 4 suits missing from initial deal
    #     """
    #     return ((deck_state == 0).sum(axis = 1) == 4).sum()
    #
    #
    #
    # def royal_flush(self, deck_state):
    #     # Not holding 2-9
    #     if (deck_state[1:9,:] == 1).any():
    #         return 0
    #     # Holding 0 or 1 suit
    #     royals = deck_state[[0,9,10,11,12], :]
    #     suits = self.suits_held(royals)
    #     if suits.sum() > 1:
    #         return 0
    #     # elif not suits.any():
    #     #    return 4
    #     elif suits.sum() == 1:
    #         #held and discarded royal of same suit
    #         if (royals[:, suits == 1] == -1).any():
    #             return 0
    #         else:
    #             return 1
    #     #count suits w/o discarded high cards
    #     else:
    #         suits_no_discard = (royals == -1).sum(axis=0) == 0
    #         return suits_no_discard.sum()
    #
    #
    # def three_kind(self, deck_state, num_discards):
    #
    #     ranks_held = (deck_state == 1).sum(axis = 1)
    #     if num_discards == 0:
    #         #no trips or trips +
    #         if (ranks_held != 3).all():
    #             return 0
    #         #full house
    #         elif (ranks_held == 2).any():
    #             return 0
    #         else:
    #             return 1
    #     elif num_discards == 1:
    #         if (ranks_held == 3).any():
    #             return 11*4
    #         elif (ranks_held == 2).sum() == 1:
    #             (deck_state[ranks_held == 2, :] == 0)








if __name__ == '__main__':
    #h1 = HandAnalyzer('ahjcts7s4h', payouts = {'royal_flush':800})
    #print(h1.analyze())
    #x = h1.hold([True, False, False, False, False])
    #print(h1.pivot_held_d(h1.hold([False]*5)))

    #h2 = HandAnalyzer('qd9c8d5c2c', payouts = {'royal_flush': 800})
    #print(h2.three_kind(h2.hold([False]*5)))
    #print(h2.draw_for_ranks(h2.hold([True, False, False, False, False]), gsize = 3))

    #h3 = HandAnalyzer('qd9c8dacad', payouts = {'royal_flush': 800})
    #print(h3.draw_for_ranks(h3.hold([False, False, False, True, True]), gsize = 3))
    #this gives 1893, correct is 1854, it counts some full houses, need to check for that...
    all_true = [True]*5
    h3 = HandAnalyzer('qdqcqh2s2d', payouts = {'royal_flush': 800})
    #print(h3.draw_for_ranks(h3.hold([True]*3+[False]*2), gsize = 3, cnt_held_only=True))
    print(h3.three_kind(h3.hold([True]*5+[False]*0)))
