from collections import Counter
from itertools import combinations_with_replacement, product
from scipy.misc import comb



## TODO: refactor so that a hand w/ discards is its own class w/ attrs like:
## nonheld_rank_grps, held_r etc.
## TODO: refactor draw_for_ranks to take a nonheld_rank_grps input instead of held_d

class HandAnalyzer(object):
    """
    Given a string of the form 'ac2d9htskc' treat that as a 5 card poker hand:
    Ace of Clubs, Two of Diamonds, Nine of Hearts, Ten of Spades, King of Clubs".

    Analyze the counts possible winning hands based on holding or discarding any
    combination of the 5 cards. Optionally input a payout table as a dictionary
    of the form below. The default payout table is from "9-6 Jacks or Better"
    Video Poker.
    payouts = {'pair_jqka': 1, 'two_pair': 2, 'three_kind': 3,
               'straight': 4, 'flush': 6, 'full_house': 9, 'four_kind': 25,
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
        straight_ranks = 'A23456789TJQKA'
        self.__strts = [straight_ranks[ind:ind+5] for ind in range(10)]

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
                    return 0, 1
                discarded_royal_suits.add(card[1])

        if len(set(held_s)) == 1:
            return 1, exp_val_denom
        else:
            return 4 - len(discarded_royal_suits), exp_val_denom

    def straight_flush(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        ways_cnt = 0

        if len(set(held_s)) > 1:
            return 0, 1
        exp_val_denom = comb(47, 5 - len(held_r))


        #use defaultdict?
        undrawable_suits = {r: set() for r in 'A23456789TJQK'}
        for hd in held_d:
            for r, s in held_d[hd]:
                if hd == 'd':
                    undrawable_suits[r].add(s)
                elif hd == 'h':
                    # 3 of 4 suits become undrawable when 1 is held
                    converse = {'C','D','H','S'}.difference(s)
                    undrawable_suits[r].update(converse)
                else:
                    raise Exception('held_d has unexpected key: {}'.format(hd))
        po_strts, _ = self.potential_straights(held_r, include_royals = False)
        for strt in po_strts:
            if strt is not None:
                strt_miss_suits = set()
                for r in strt:
                    strt_miss_suits.update(undrawable_suits[r])
                ways_cnt += 4 - len(strt_miss_suits)

        return ways_cnt, exp_val_denom


    def flush(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        num_suits = len(set(held_s))
        if num_suits > 1:
            return 0, 1
        exp_val_denom = comb(47, 5 - len(held_r))

        ways_cnt = 0
        ways_cnt -= self.royal_flush(held_d)[0]
        ways_cnt -= self.straight_flush(held_d)[0]

        #use defaultdict
        undrawable_suit_cnt = {s:0 for s in 'CDHS'}
        for _, suit in self.__h:
            undrawable_suit_cnt[suit] += 1

        if num_suits == 1:
            ways_cnt += comb(13 - undrawable_suit_cnt[held_s[0]], len(disc_r))
        else: #no saved cards
            for suit, udc in undrawable_suit_cnt.items():
                ways_cnt += comb(13 - udc, len(disc_r))

        return ways_cnt, exp_val_denom



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
            #check for holding low pair
            lows = '23456789T'
            low_pair_bool = held_r_cnts[0][0] in lows
            #check for holding two pair
            two_pair_bool = (len(held_r_cnts) > 1) and (held_r_cnts[1][1] == 2)
            if low_pair_bool or two_pair_bool:
                return 0, 1

            #holding pair of jkqa find everything that DOESN't improve hand
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
        held_r_avail = {}
        for r in held_r:
            held_r_avail[r] = self.__draws[r]
            nonheld_ranks[r] = 0

        nonheld_rank_grps = Counter(nonheld_ranks.values())
        held_r_avail_grps = Counter(held_r_avail.values())
        draw_cnt = len(held_d['d'])
        # nothing held
        if held_r_cnts == []:
            return self.draw_2pair(nonheld_rank_grps, draw_cnt = 5), exp_val_denom
        # most common card is a singleton
        elif held_r_cnts[0][1] == 1:
            ways_cnt = 0
            if draw_cnt == 4:
                #draw two pairs from the deck
                ways_cnt += self.draw_2pair(nonheld_rank_grps, draw_cnt = 4)


                #pair up held singleton, draw a pair
                #TODO: possibly replace this block with a call to draw_for_ranks?
                held_draws = list(held_r_avail.values())[0] # ok since only holding 1
                for avail, rcnt in nonheld_rank_grps.items():
                    rways = rcnt * comb(avail, 2)
                    new_nhrg = nonheld_rank_grps.copy()
                    new_nhrg[avail] -= 1
                    kick_ways = self.count_ways2kick(new_nhrg, num_kickers = 1)
                    ways_cnt += held_draws * rways * kick_ways

                return ways_cnt, exp_val_denom
            elif draw_cnt == 3: # maybe change this block to draw_cnt in [3,2]

                for havail, hrcnt in held_r_avail_grps.items():
                    #pair up a held card
                    hrways = comb(hrcnt, 1) * comb(havail, 1)
                    #then draw a pair
                    drawways = self.draw_for_ranks(held_d, gsize=2,
                                                   draw_cnt=2,
                                                   draw_only=True,
                                                   second_pair=False)
                    ways_cnt += hrways * drawways

                    #draw a match for both held singles
                    hrways2 = comb(havail, 1) ** hrcnt
                    kick_ways = self.count_ways2kick(nonheld_rank_grps,
                                                     num_kickers=1)
                    ways_cnt += hrways2 * kick_ways
                return ways_cnt, exp_val_denom
            elif draw_cnt == 2:
                #draw a match for 2 of the 3 held singles
                return self.draw_2pair(held_r_avail_grps, draw_cnt = 2), exp_val_denom

            else:
                return 0, 1

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
        """
        helper for two_pair, originally designed for drawing 2 pairs when,
        drawing 4 or 5 cards.
        there's a mostly symmetrical case for drawing 2 cards and holding
        3 singletons and pairing up 2 of those. so if draw_cnt = 2 then
        choose 1 card from the number available within a rank. adjust this with
        the choose_in_r flag.
        """
        if draw_cnt in [4, 5]:
            choose_in_r = 2
        elif draw_cnt == 2:
            choose_in_r = 1
        else:
            exp = 'Expecting to draw 2, 4, or 5 cards, draw_cnt = {}'
            raise Exception(exp.format(draw_cnt))

        cwr = combinations_with_replacement(nonheld_rank_grps, 2)
        ways_cnt = 0
        for avail1, avail2 in cwr:
            if avail1 == avail2:
                rways = comb(nonheld_rank_grps[avail1], 2)
                rways *= comb(avail1, choose_in_r) ** 2
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
                    mixpair *= nonheld_rank_grps[av] * comb(av, choose_in_r)
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

    def full_house(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))
        nonheld_ranks = self.__draws.copy()
        held_r_avail = {}
        for r in held_r:
            held_r_avail[r] = self.__draws[r]
            nonheld_ranks[r] = 0

        nonheld_rank_grps = Counter(nonheld_ranks.values())
        held_r_avail_grps = Counter(held_r_avail.values())
        draw_cnt = len(held_d['d'])

        ways_cnt = 0
        # nothing held
        if held_r_cnts == []:
            for avail, rcnt in nonheld_rank_grps.items():

                rtrips = rcnt * comb(avail, 3)
                new_nhrg = nonheld_rank_grps.copy()
                new_nhrg[avail] -= 1

                pair_ways = 0
                for pavail, prcnt in new_nhrg.items():
                    pair_ways += prcnt * comb(pavail, 2)

                ways_cnt += rtrips * pair_ways
            return ways_cnt, exp_val_denom

        # most common card is a singleton
        elif held_r_cnts[0][1] == 1:

            if draw_cnt == 4:
                held_draws = list(held_r_avail.values())[0] # ok since only holding 1
                for heldneed, drawneed in [[1, 3], [2, 2]]:
                    up_held = comb(held_draws, heldneed)
                    draw_grp = self.draw_for_ranks(held_d, gsize = drawneed,
                                                   draw_cnt=drawneed, draw_only=True)
                    ways_cnt += up_held * draw_grp

                return ways_cnt, exp_val_denom

            elif draw_cnt == 3:
                avail1, avail2 = list(held_r_avail.values())
                ways_cnt += comb(avail1, 2) * comb(avail2, 1)
                ways_cnt += comb(avail1, 1) * comb(avail2, 2)

                return ways_cnt, exp_val_denom

            else:
                return 0, 1

        elif held_r_cnts[0][1] == 2:
            if draw_cnt in [3, 2]:
                #tripup held pair
                held_draws = self.__draws[held_r_cnts[0][0]]
                tripup_pair = comb(held_draws, 1)
                if draw_cnt == 3:
                    #draw trips to go with pair
                    ways_cnt += self.draw_for_ranks(held_d, gsize=3, draw_cnt=3,
                                                    draw_only=True)
                    #draw pair to go with tripup pair
                    draws = self.draw_for_ranks(held_d, gsize=2, draw_cnt=2,
                                                draw_only=True)
                elif draw_cnt == 2:
                    sing_avail = self.__draws[held_r_cnts[1][0]]
                    #trip up held singleton
                    ways_cnt += comb(sing_avail, 2)
                    #pair up held singleton
                    draws = comb(sing_avail, 1)

                ways_cnt += tripup_pair * draws

                return ways_cnt, exp_val_denom
            elif draw_cnt == 1:
                #check for holding two pair
                if held_r_cnts[1][1] == 2:
                    return sum(held_r_avail.values()), exp_val_denom
                else:
                    return 0, 1
            else:
                return 0, 1
        elif held_r_cnts[0][1] == 3:
            #draw pair with trips,
            if draw_cnt == 2:
                draw_pair = self.draw_for_ranks(held_d, gsize=2, draw_cnt=2,
                                                draw_only=True)
                return draw_pair, exp_val_denom
            #trips + pairup held singleton
            elif draw_cnt == 1:
                # count avail cards to pairup held singleton
                return comb(self.__draws[held_r_cnts[1][0]], 1), exp_val_denom
            elif draw_cnt == 0 and held_r_cnts[1][1] == 2:
                #holding FH
                return 1, 1
            else:
                return 0, 1

        else:
            return 0, 1


    def four_kind(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))


        draw = self.draw_for_ranks(held_d, gsize=4, cnt_held_only=False)
        return draw, exp_val_denom


    def straight(self, held_d):
        held_r, held_s, disc_r, disc_s = self.pivot_held_d(held_d)
        held_r_cnts = Counter(held_r).most_common()
        exp_val_denom = comb(47, 5 - len(held_r))

        ways_cnt = 0
        #subtract royal and straight flush from the count
        ways_cnt -= self.royal_flush(held_d)[0]
        ways_cnt -= self.straight_flush(held_d)[0]
        if held_r_cnts == []:
            for s in self.__strts:
                ways_cnt += self.prod_list([self.__draws[r] for r in s])
            return ways_cnt, exp_val_denom
        elif held_r_cnts[0][1] != 1:
            #holding a pair or more
            return 0, 1
        else:
            strts_cop, draws_cop = self.potential_straights(held_r)
            for sc in strts_cop:
                if sc is not None:
                    ways_cnt += self.prod_list([draws_cop[r] for r in sc])

            return ways_cnt, exp_val_denom


    def potential_straights(self, held_r, include_royals = True):
        """
        Switches the strings in list of strings representing straights
        e.g. 'A2345', '789TJ' to None if holding a card that is not in
        the given straight. Also sets the draws for that rank to 1.
        Returns these.
        """
        if include_royals:
            strts_cop = self.__strts[:]
            enum_strts = list(enumerate(self.__strts))
        else:
            strts_cop = self.__strts[:-1]
            enum_strts = list(enumerate(self.__strts[:-1]))

        draws_cop = self.__draws.copy()
        for r in held_r:
            draws_cop[r] = 1
            for ind, strt in enum_strts:
                if r not in strt:
                    strts_cop[ind] = None
        return strts_cop, draws_cop



    @staticmethod
    def prod_list(lst):
        accum = 1
        for el in lst:
            accum *= el
        return accum

    def draw_for_ranks(self, held_d, gsize = 3, cnt_held_only = False, pairing_jqka = False, second_pair = False, draw_cnt = None, draw_only = False):
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

        draw_cnt = len(held_d['d']) if draw_cnt is None else draw_cnt

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
        if not draw_only:
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
                        'straight_flush': self.straight_flush,
                        'four_kind': self.four_kind,
                        'full_house': self.full_house,
                        'flush': self.flush,
                        'straight': self.straight,
                        'three_kind': self.three_kind,
                        'two_pair': self.two_pair,
                        'pair_jqka': self.pair_jqka}
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

    #h2 = HandAnalyzer('qd9c8d5c2c', payouts = {'royal_flush': 800, 'three_kind': 15})
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

    #twop = HandAnalyzer('acad9h8s2c')
    #print(twop.two_pair(twop.hold([True]*2 + [False]*3)))

    #print(h2.draw_for_ranks(h2.hold([True, True, False, False, False]), gsize = 2, second_pair = True))
    #print(h2.two_pair(h2.hold([True]*2+[False]*3)))
    #print(h2.potential_straights(['Q','9']))

    junk = HandAnalyzer('ts9c8d5c2h')
    #print(junk.analyze())
