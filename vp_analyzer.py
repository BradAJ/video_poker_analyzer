from collections import Counter
from itertools import combinations_with_replacement, product
from scipy.misc import comb


class HandAnalyzer(object):
    """
    Given a string of the form 'ac2d9htskc' treat that as a 5 card poker hand:
    Ace of Clubs, Two of Diamonds, Nine of Hearts, Ten of Spades, King of Clubs".

    Analyze the counts possible winning hands based on holding or discarding any
    combination of the 5 cards. Optionally input a payout table as a dictionary
    of the form below. The default payout table is from "9-6 Jacks or Better"
    Video Poker.
    payouts = {'pair_jqka': 1, '2_pair': 2, '3_of_a_kind': 3,
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
            self.payouts = {'pair_jqka': 1, 'two_pair': 2, 'three_kind': 3,
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
            return 0, 1

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


    def pair_jqka(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))
        # nothing held
        if held_r_cnts == []:
            draw5 = self.draw_for_ranks(held_d, gsize=2, cnt_held_only=False,
                                        pairing_jqka=True)
            return draw5, exp_val_denom
        # most common card is a singleton
        elif held_r_cnts[0][1] == 1:
            draws = self.draw_for_ranks(held_d, gsize=2, cnt_held_only=False,
                                        pairing_jqka=True)
            return draws, exp_val_denom
        elif held_r_cnts[0][1] == 2:

            #check for holding two pair
            if (len(held_r_cnts) > 1) and (held_r_cnts[1][1] == 2):
                return 0, 1
            else:
                #find everything that DOESN't improve hand
                #DRY this up (in three_kind too)
                draw_cnt = len(held_d['d'])
                nonheld_ranks = self.__draws.copy()
                for r in held_r:
                    nonheld_ranks[r] = 0
                nonheld_rank_grps = Counter(nonheld_ranks.values())
                return self.count_ways2kick(nonheld_rank_grps, draw_cnt), exp_val_denom


    def two_pair(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))
        nonheld_ranks = self.__draws.copy()
        for r in held_r:
            nonheld_ranks[r] = 0
        nonheld_rank_grps = Counter(nonheld_ranks.values())
        # nothing held
        if held_r_cnts == []:
            return self.draw_2pair(nonheld_rank_grps, draw_cnt = 5), exp_val_denom
        # most common card is a singleton
        elif held_r_cnts[0][1] == 1:
            ways_cnt = 0
            if len(held_r) == 1:
                #draw two pairs from the deck
                ways_cnt += self.draw_2pair(nonheld_rank_grps, draw_cnt = 4)

                #add to the held singleton, and get another pair
                held_c = held_r_cnts[0][0]
                held_c_avail = self.__draws[held_c]
                kick_ways = 0
                for avail, rcnt in nonheld_rank_grps.items():
                    rways = rcnt * comb(avail, 2)
                    new_nhrg = nonheld_rank_grps.copy()
                    new_nhrg[avail] -= 1
                    kick_ways = self.count_ways2kick(new_nhrg, num_kickers = 1)
                    ways_cnt += held_c_avail * rways * kick_ways

                return ways_cnt, exp_val_denom

            ##TODO: hold two non paired cards
            ##TODO: hold three non paired cards







        elif held_r_cnts[0][1] == 2:

            #check for holding two pair
            if (len(held_r_cnts) > 1) and (held_r_cnts[1][1] == 2):
                #find everything that DOESN't improve hand
                #DRY this up (in three_kind too)
                draw_cnt = len(held_d['d'])

                return (self.count_ways2kick(nonheld_rank_grps, draw_cnt),
                        exp_val_denom)
            else:

                #holding a pair. take it out of consideration and look for another
                return (self.draw_for_ranks(held_d, gsize=2, second_pair=True),
                        exp_val_denom)

        else:
            return 0, 1



    def draw_2pair(self, nonheld_rank_grps, draw_cnt = 4):
        if draw_cnt not in [4,5]:
            exp = 'Need to draw 4,5 cards to get 2 pairs, draw_cnt ='
            raise Exception(exp.format(draw_cnt))
        ways_cnt = 0
        cwr = combinations_with_replacement(nonheld_rank_grps, 2)

        for avail1, avail2 in cwr:
            if avail1 == avail2:
                rways = comb(nonheld_rank_grps[avail1], 2) * comb(avail1, 2) ** 2
                if draw_cnt == 5:
                    new_nhrg = nonheld_rank_grps.copy()
                    new_nhrg[avail1] -= 2
                    kick_ways = self.count_ways2kick(new_nhrg, num_kickers = 1)
                else:
                    kick_ways = 1
                ways_cnt += rways * kick_ways
            else:
                mixpair = 1
                for av in (avail1, avail2):
                    mixpair *= nonheld_rank_grps[av] * comb(av, 2)
                if draw_cnt == 5:
                    new_nhrg = nonheld_rank_grps.copy()
                    new_nhrg[avail1] -= 1
                    new_nhrg[avail2] -= 1
                    kick_ways = self.count_ways2kick(new_nhrg, num_kickers = 1)
                else:
                    kick_ways = 1

                ways_cnt += mixpair * kick_ways


        return ways_cnt






    def three_kind(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))
        # nothing held or most common card is a singleton
        if held_r_cnts == [] or held_r_cnts[0][1] == 1:
            draw = self.draw_for_ranks(held_d, gsize=3, cnt_held_only=False)
            return draw, exp_val_denom

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
                #find everything that DOESN't improve hand
                #DRY this up
                draw_cnt = len(held_d['d'])
                nonheld_ranks = self.__draws.copy()
                for r in held_r:
                    nonheld_ranks[r] = 0
                nonheld_rank_grps = Counter(nonheld_ranks.values())
                return self.count_ways2kick(nonheld_rank_grps, draw_cnt), exp_val_denom
        else:
            return 0, 1


    def four_kind(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))


        draw = self.draw_for_ranks(held_d, gsize=4, cnt_held_only=False)
        return draw, exp_val_denom


#copy of draw_for_ranks with flags for two_pair work commented out. just in case...
    # def draw_for_ranks(self, held_d, gsize = 3, cnt_held_only = False, pairing_jqka = False):
    #     """
    #     Given held cards and discards count ways to draw for pairs/3kind/4_of_a_kind
    #     based on collecting them purely from draw pile or adding to the held cards
    #
    #     gsize: (2, 3, or 4) Size of group of cards to be made. e.g. pair = 2
    #
    #     cnt_held_only: (bool). True: Obtain group by adding to held cards only,
    #         rather than drawing a group. e.g. a 'AA742' hand where you hold the
    #         aces and count 3kinds would include the:
    #         comb(9,1)*comb(4,3)+comb(3,1)*comb(3,3)=39
    #         ways of drawing trips that result in a full house.
    #         To avoid this, set False.
    #
    #     pairing_jqka: (bool). True: only consider pairs of Jacks, Queens, Kings, Aces
    #
    #     """
    #
    #     held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
    #     draw_cnt = len(held_d['d'])
    #     nonheld_ranks = self.__draws.copy()
    #     ### if second_pair:
    #     ###     nonheld_ranks = self.__draws - Counter({held_r_cnts[0][0]: 2})
    #     for r in held_r:
    #         nonheld_ranks[r] = 0
    #
    #
    #     nonheld_rank_grps = Counter(nonheld_ranks.values())
    #     #remove everything but JQKA if only considering those pairs
    #     if pairing_jqka:
    #         nonheld_jqka = nonheld_ranks - Counter('23456789T'*4)
    #         nonheld_jqka_grps = Counter(nonheld_jqka.values())
    #         nonheld_jqka_grps
    #         draw_grp_iter = nonheld_jqka_grps.items()
    #     else:
    #         draw_grp_iter = nonheld_rank_grps.items()
    #
    #     ways_cnt = 0
    #
    #     #add up ways of making group with all draw cards
    #     if not cnt_held_only:
    #         for avail, rcnt in draw_grp_iter:
    #             # count ranks that we can select 3 cards from.
    #             if gsize <= draw_cnt:
    #                 rways = rcnt * comb(avail, gsize)
    #                 kickers = draw_cnt - gsize
    #                 if kickers > 0:
    #                     new_nhrg = nonheld_rank_grps.copy()
    #                     new_nhrg[avail] -= 1
    #                     kick_ways = self.count_ways2kick(new_nhrg,
    #                                                      num_kickers = kickers)
    #                 else:
    #                     kick_ways = 1
    #                 #print(rcnt, avail, kick_ways, rways)
    #                 ways_cnt += rways * kick_ways
    #             else:
    #                 continue
    #
    #     #add up ways of adding to the held cards
    #     for r, hcnt in Counter(held_r).items():
    #         #skip if only pairing up JQKA
    #         pair_jqka_cond = pairing_jqka and (r not in 'JQKA')
    #         ### second_pair_cond = second_pair and (hcnt == 2)
    #         ### if pair_jqka_cond or second_pair_cond:
    #         ###     continue
    #         if pair_jqka_cond:
    #             continue
    #
    #         needed = gsize - hcnt
    #         if needed <= draw_cnt:
    #             hways = comb(self.__draws[r], needed)
    #             kickers = draw_cnt - needed
    #             if kickers > 0:
    #                 ### if not second_pair:
    #                 kick_ways = self.count_ways2kick(nonheld_rank_grps,
    #                                                  num_kickers = kickers)
    #                 ### else:
    #                 ###     sp_nhrg = nonheld_rank_grps - Counter({nonheld_ranks[r]:1})
    #                 ###     kick_ways = self.count_ways2kick(sp_nhrg, num_kickers = kickers)
    #             else:
    #                 kick_ways = 1
    #             #print(hcnt, kickers, kick_ways, hways)
    #
    #             ways_cnt += hways * kick_ways
    #         else:
    #             continue
    #
    #     return ways_cnt

    def draw_for_ranks(self, held_d, gsize = 3, cnt_held_only = False, pairing_jqka = False, second_pair = False):
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

        pairing_jqka: (bool). True: only consider pairs of Jacks, Queens, Kings, Aces

        second_pair: (bool). True: Remove from consideration a pair of cards.
                        Used for counting two_pair when holding a pair

        """

        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        draw_cnt = len(held_d['d'])
        #dealing with two_pair stuff
        if not second_pair:
            nonheld_ranks = self.__draws.copy()
        else:
            rmv_held_pair = Counter({Counter(held_r).most_common(1)[0]: 2})
            nonheld_ranks = self.__draws - rmv_held_pair
        for r in held_r:
            nonheld_ranks[r] = 0


        nonheld_rank_grps = Counter(nonheld_ranks.values())
        #remove everything but JQKA if only considering those pairs
        if pairing_jqka:
            nonheld_jqka = nonheld_ranks - Counter('23456789T'*4)
            nonheld_jqka_grps = Counter(nonheld_jqka.values())
            nonheld_jqka_grps
            draw_grp_iter = nonheld_jqka_grps.items()
        else:
            draw_grp_iter = nonheld_rank_grps.items()

        ways_cnt = 0

        #add up ways of making group with all draw cards
        if not cnt_held_only:
            for avail, rcnt in draw_grp_iter:
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
            #skip if only pairing up JQKA
            pair_jqka_cond = pairing_jqka and (r not in 'JQKA')
            second_pair_cond = second_pair and (hcnt == 2)
            if pair_jqka_cond or second_pair_cond:
                continue

            needed = gsize - hcnt
            if needed <= draw_cnt:
                hways = comb(self.__draws[r], needed)
                kickers = draw_cnt - needed
                if kickers > 0:
                    if not second_pair:
                        kick_ways = self.count_ways2kick(nonheld_rank_grps,
                                                     num_kickers = kickers)
                    else:
                        sp_nhrg = nonheld_rank_grps - Counter({nonheld_ranks[r]:1})
                        kick_ways = self.count_ways2kick(sp_nhrg, num_kickers = kickers)
                else:
                    kick_ways = 1
                #print(hcnt, kickers, kick_ways, hways)

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
        win_counters = {'royal_flush': self.royal_flush,
                        'three_kind': self.three_kind}
        for hold_l in product([True, False], repeat=5):
            deck_state = self.hold(held = hold_l)
            ways_to_win = {}
            expected_val = 0
            for win in self.payouts:
                wins_denom = win_counters[win](deck_state)
                expected_val += self.payouts[win] * wins_denom[0] / wins_denom[1]
                ways_to_win[win] = wins_denom

            ways_to_win['expected_val'] = expected_val
            hand = tuple(card if held else 'X' for card, held in zip(self.hand, hold_l))
            win_props[hand] = ways_to_win

        return win_props



if __name__ == '__main__':
    #h1 = HandAnalyzer('ahjcts7s4h', payouts = {'royal_flush':800})
    #print(h1.analyze())
    #x = h1.hold([True, False, False, False, False])
    #print(h1.pivot_held_d(h1.hold([False]*5)))

    h2 = HandAnalyzer('qd9c8d5c2c', payouts = {'royal_flush': 800, 'three_kind': 15})
    #print(h2.three_kind(h2.hold([False]*5)))
    #print(h2.draw_for_ranks(h2.hold([True, False, False, False, False]), gsize = 2, pairing_jqka = True))
    #print(h2.four_kind(h2.hold([True]*1+[False]*4)))

    #h3 = HandAnalyzer('qd9c8dacad', payouts = {'royal_flush': 800})
    #print(h3.draw_for_ranks(h3.hold([False, False, False, True, True]), gsize = 3))
    #this gives 1893, correct is 1854, it counts some full houses, need to check for that...
    #all_true = [True]*5
    #h3 = HandAnalyzer('qdqcqh2s2d', payouts = {'royal_flush': 800})
    #print(h3.draw_for_ranks(h3.hold([True]*3+[False]*2), gsize = 3, cnt_held_only=True))
    #print(h3.three_kind(h3.hold([True]*5+[False]*0)))

    twop = HandAnalyzer('acad9h8s2c')
    #print(twop.two_pair(twop.hold([True]*2 + [False]*3)))

    #print(h2.draw_for_ranks(h2.hold([True, False, False, False, False]), gsize = 2, second_pair = True))
    print(h2.two_pair(h2.hold([False]*5)))
