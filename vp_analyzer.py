from collections import Counter
from itertools import combinations_with_replacement, product
from scipy.misc import comb

# GLOBALS
RANKS = 'A23456789TJQK'
SUITS = 'cdhs'
STRAIGHTS = [list(RANKS+'A')[ind:ind+5] for ind in range(10)]


class HandAnalyzer(object):
    """
    Given a string of the form 'ac2d9htskc' treat that as a 5 card poker hand:
    Ace of Clubs, Two of Diamonds, Nine of Hearts, Ten of Spades, King of Clubs.

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
            the following keys: 'pair_jqka', 'two_pair', 'three_kind',
            'straight', 'flush', 'full_house', 'four_kind', 'straight_flush'
            'royal_flush', 'four_kind7', 'four_kindA8'
    OUTPUT:
    None
    """

    def __init__(self, hand, payouts = None):
        self.__specials = '' #special 4kinds ranks see: DiscardValue._four_kind_special()
        if payouts is None:
            #Payout for "9-6 Jacks or Better Video Poker"
            self.payouts = {'pair_jqka': 1, 'two_pair': 2, 'three_kind': 3,
                            'straight': 4, 'flush': 6, 'full_house': 9,
                            'four_kind': 25, 'straight_flush': 50,
                            'royal_flush': 800}
        else:
            #Bonus four_kind: (A8, 7 in Aces and Eights), (A, 234, in Triple Bonus Plus)
            bonuses = ['A8', '7', 'A', '234']
            for bonus in bonuses:
                fourk_bonus = 'four_kind' + bonus
                if fourk_bonus in payouts:
                    self.__specials += bonus
            self.payouts = payouts

        #rewrite hand string as list of 5 cards of 2 chars
        self.hand = []
        for ind in range(0, 10, 2):
            self.hand.append(hand[ind:ind+1].upper() + hand[ind+1:ind+2].lower())

        self.__h = [(card[0], card[1]) for card in self.hand]
        #self.__draws = Counter(self.__ranks*4) - Counter([c[0] for c in self.__h])


    def hold(self, held = [True]*5):
        """
        Given a list of 5 bools, one for each card (True means hold the card),
        return a dict of card tuples with keys 'h' for hold and 'd' for discard.
        """
        held_d = {'h':[], 'd':[]}
        for card, held_bool in zip(self.__h, held):
            if held_bool:
                held_d['h'].append(card)
            else:
                held_d['d'].append(card)
        return held_d


    def analyze(self, return_full_analysis = True):
        """
        From each of the 32 possible hold/discard situations for a hand,
        calculate the number of ways of making each hand in self.payouts,
        use these counts (and the payouts) to calculate the expected value of
        each discard strategy for the hand.

        INPUT:
        return_full_analysis (bool, default = True) See OUTPUT for explanation.

        OUTPUT:
        return_full_analysis == True: Return a nested dict, where each
            discard strategy contains a dict of count info as a tuple of
            (count, total number of results) for each winning hand.
                             == False: Only return the discard strategy with the
            highest expected value (prefer more discards in case of ties) and
            that expected value as a tuple. This minimal return size is useful
            for work that analyzes large numbers of hands.

            In both cases the discard strategy is represented as a 10 character
            string, where the discarded cards are represented by 'XX'.
        """

        win_props = {}

        count_wins_kwargs = {'wins': self.payouts.keys()}
        if self.__specials != []:
            count_wins_kwargs['specials'] = self.__specials

        for hold_l in product([True, False], repeat=5):
            deck_state = DiscardValue(held_d=self.hold(held = hold_l))
            ways_to_win = deck_state.count_wins(**count_wins_kwargs)
            expected_val = 0
            for win, cnt in ways_to_win.items():
                expected_val += self.payouts[win] * cnt / deck_state.exp_val_denom

            ways_to_win['expected_val'] = expected_val
            hand = ''.join([card if held else 'XX' for card, held in zip(self.hand, hold_l)])
            win_props[hand] = ways_to_win

        if return_full_analysis:
            return win_props
        else:
            return self.best_disc(win_props)


    @staticmethod
    def best_disc(results):
        """
        Helper function for .analyze(), sort results by expected value and return
        the discard string. The hand's discard strategy is represented as a 10
        character string, where the discarded cards are represented by 'XX'.
        """
        max_ev = 0
        best_ev_disc = 0
        for holddisc in results:
            cur_ev = results[holddisc]['expected_val']

            equal_bool = () and (cur_disc > best_ev_disc)
            if cur_ev > max_ev:
                besthold = holddisc
                max_ev = cur_ev
                best_ev_disc = holddisc.count('XX')
            elif cur_ev == max_ev:
                cur_ev_disc = holddisc.count('XX')
                if cur_ev_disc > best_ev_disc:
                    besthold = holddisc
                    best_ev_disc = cur_ev_disc
            else:
                continue

        bestholdstr = ''.join(besthold)

        return bestholdstr, results[besthold]['expected_val']


    def pay_current_hand(self):
        """
        Check to see if current hand is a winning hand. If so, return the
        associated payout, otherwise return 0.
        """
        pays = self.payouts.copy()
        groups = ['pair_jqka', 'two_pair', 'three_kind', 'full_house',
                  'four_kind', 'four_kind7', 'four_kindA8']
        straight_hands = ['straight', 'straight_flush', 'royal_flush']
        flushes = ['flush', 'straight_flush', 'royal_flush']

        held_r =[]
        suits = set()
        for r, s in self.__h:
            held_r.append(r)
            suits.add(s)

        held_r_cnts = Counter(held_r).most_common()
        num_suits = len(suits)

        if held_r_cnts[0][1] > 1:
            #at least a pair, so no straight_hands, no flushes
            for strtflu in straight_hands + flushes:
                pays[strtflu] = 0
            if held_r_cnts[0][1] == 2:
                for group in groups[2:]:
                    pays[group] = 0
                # check for two_pair
                if held_r_cnts[1][1] == 1:
                     pays['two_pair'] = 0
                # check JoB
                if held_r_cnts[0][0] not in 'JQKA':
                    pays['pair_jqka'] = 0
            #check full_house
            elif held_r_cnts[0][1] == 3:
                for group in groups[4:]:
                    pays[group] = 0
                if held_r_cnts[1][1] == 1:
                    pays['full_house'] = 0

            else:
                #check special fours of a kind
                if held_r_cnts[0][0] not in 'A8':
                    pays['four_kindA8'] = 0
                if held_r_cnts[0][0] != '7':
                    pays['four_kind7'] = 0
        else:
            #no pairs or higher
            for group in groups:
                pays[group] = 0

        # check for flush
        if num_suits > 1:
            for flush in flushes:
                pays[flush] = 0

        #check straights
        acelow_order_d = {r:i for i, r in enumerate(RANKS)}
        ordered_hand = ''.join(sorted(held_r, key= lambda x: acelow_order_d[x]))
        strt_set = set([''.join(x) for x in STRAIGHTS])
        #add royal straight to accommodate ace low ordering
        royals = 'ATJQK'
        strt_set.add(royals)
        if ordered_hand not in strt_set:
            for strt in straight_hands:
                pays[strt] = 0
        elif ordered_hand != royals:
            pays['royal_flush'] = 0


        return max(pays.values())


class DiscardValue(object):
    """
    Given a poker hand and specifying which cards to hold/discard count ways
    of building winning hands. If the payout table gives bonuses for particular
    hands, specify those with the specials keyword (currently only works for
    Aces and Eights variant).

    Methods named after poker hands (e.g. royal_flush, four_kind, full_house)
    return counts of ways to make the hand.

    All other methods, except count_wins, are helper functions for these poker
    hand methods.


    INPUT:
    held_d: (dict) Hold/Discard with keys 'h' and 'd' of the form output from
            HandAnalyzer.hold, e.g.:
            {'h': [('T', 's'), ('5', 'c'), ('2', 'h')],
            'd': [('9', 'c'), ('8', 'd')]}
    hand_str: (str) Ten characters specifying a poker hand (Case Insensitive),
              of the form for instantiating HandAnalyzer, e.g.: 'Ts9c8d5c2h'
    hold_str: (str) Same form as hand_str, except discarded cards represented
                 as 'XX', e.g.: 'TsXXXX5c2h'
        NOTE: DiscardValue object must be instantiated with held_d alone,
        or hold_str AND discard_str together. (held_d has priority
        if others are not None)
    specials: (list) Card ranks with bonuses for four of a kind, e.g.:
              ['A', '7', '8']

    OUTPUT: None
    """
    def __init__(self, held_d = None, hand_str = None, hold_str = None,
                 specials = None):
        if held_d is not None:
            #TODO: enforce rank uppercase, suit lowercase in card tuples
            self.held_d = held_d
        elif (hand_str is not None) and (hold_str is not None):
            ha_obj = HandAnalyzer(hand_str)
            hold_l = [hold_str[ind:ind+2].upper() != 'XX' for ind in range(0,10,2)]
            self.held_d = ha_obj.hold(hold_l)
        else:
            exp = 'If held_d is None, then specify hand_str AND hold_str. {} is None'
            kwzip = zip([hand_str, hold_str], ['hand_str', 'hold_str'])
            nones = ' '.join([kws if kw is None else '' for kw, kws in kwzip])
            raise Exception(exp.format(nones))

        self.__specials = specials

        self.held_r, self.held_s, self.disc_r, self.disc_s = self.pivot_held_d()
        #NOTE to self: regex find: (held_r[^\w_])  , replace: self.$1

        seen_ranks = Counter(list(self.held_r) + list(self.disc_r))
        self.__draws = Counter(RANKS*4) - seen_ranks
        self.held_r_cnts = Counter(self.held_r).most_common()
        self.draw_cnt = len(self.disc_r)

        self.nonheld_ranks = self.__draws.copy()
        for r in self.held_r:
            self.nonheld_ranks[r] = 0

        # counter of number of ranks with 0-4 available cards. For example,
        # discarding all 5 cards in a junk hand has:
        # nonheld_rank_grps == Counter({4: 8, 3: 5})
        # for 8 ranks have 4 cards each to draw, and 5 ranks have 3 cards to draw.
        self.nonheld_rank_grps = Counter(self.nonheld_ranks.values())

        # count of all possible draws, i.e. the denominator for calculating
        # probability of drawing a particular hand.
        self.exp_val_denom = comb(47, 5 - len(self.held_r))


    def draws(self):
        """Returns the count of each card rank available to be drawn."""
        return self.__draws


    def pivot_held_d(self):
        """Helper function to reorganize hold/discard info."""
        ranks_suits = []
        for key in ['h', 'd']:
            if self.held_d[key] != []:
                ranks_suits.extend(list(zip(*self.held_d[key])))
            else:
                ranks_suits.extend([(), ()])
        return ranks_suits

    def count_wins(self, wins = None, specials = None):
        """
        Wrapper func.
        Call each poker hand method specified as a string in wins and return
        the output from these in a dict.

        INPUT:
        wins: (list of str) Each elem corresponds to a poker hand method, e.g.:
                ['royal_flush', 'pair_jqka', 'four_kindA8']
                If wins is None: include all Jack or Better hands
        specials: (list of str) any ranks chars that get a bonus on 4 of a kind.
            e.g. 'A', '8', '7' for Aces and Eights payout table. Remove these
            from the nominal four_kind count and call a method for each bonus.

        OUTPUT: (dict) e.g.:
                {'royal_flush': 1, 'pair_jqka': 45456, 'four_kindA8': 0}
        """
        if wins is None:
            wins = ['royal_flush','straight_flush','four_kind','full_house',
                    'flush','straight','three_kind','two_pair','pair_jqka']
        #TODO: generate win_counters from wins
        win_counters = {'royal_flush': self.royal_flush,
                        'straight_flush': self.straight_flush,
                        'four_kind': self.four_kind,
                        'full_house': self.full_house,
                        'flush': self.flush,
                        'straight': self.straight,
                        'three_kind': self.three_kind,
                        'two_pair': self.two_pair,
                        'pair_jqka': self.pair_jqka,
                        'four_kindA8': self.four_kindA8,
                        'four_kind7': self.four_kind7,
                        'four_kindA': self.four_kindA,
                        'four_kind234': self.four_kind234}
        wins_d = {}
        for win in wins:
            if (specials is not None) and (win == 'four_kind'):
                wins_d[win] = win_counters[win](specials = specials)
            else:
                wins_d[win] = win_counters[win]()

        return wins_d


    def royal_flush(self):
        holding_2to9 = set(self.held_r).intersection(set('23456789')) != set()
        if holding_2to9 or (len(set(self.held_s)) > 1):
            return 0

        discarded_royal_suits = set()
        for card in self.held_d['d']:
            if (card[0] in 'AKQJT'):
                #check if held and discarded royal of same suit
                #already checked for multiple held suits, hence self.held_s[0]
                if (len(self.held_s) > 0) and (card[1] == self.held_s[0]):
                    return 0
                discarded_royal_suits.add(card[1])

        if len(set(self.held_s)) == 1:
            return 1
        else:
            return 4 - len(discarded_royal_suits)

    def straight_flush(self):
        ways_cnt = 0

        if len(set(self.held_s)) > 1:
            return 0

        #TODO: use defaultdict?, use global for ranks string
        undrawable_suits = {r: set() for r in RANKS}
        for hd in self.held_d:
            for r, s in self.held_d[hd]:
                if hd == 'd':
                    undrawable_suits[r].add(s)
                elif hd == 'h':
                    # 3 of 4 suits become undrawable when 1 is held
                    converse = {x for x in SUITS}.difference(s)
                    undrawable_suits[r].update(converse)
                else:
                    raise Exception('held_d has unexpected key: {}'.format(hd))
        po_strts, _ = self._potential_straights(include_royals = False)
        for strt in po_strts:
            if strt is not None:
                strt_miss_suits = set()
                for r in strt:
                    strt_miss_suits.update(undrawable_suits[r])
                ways_cnt += 4 - len(strt_miss_suits)

        return ways_cnt


    def flush(self):
        num_suits = len(set(self.held_s))
        if num_suits > 1:
            return 0

        ways_cnt = 0
        ways_cnt -= self.royal_flush()
        ways_cnt -= self.straight_flush()

        #use defaultdict
        undrawable_suit_cnt = {s:0 for s in SUITS}
        for suit in list(self.held_s) + list(self.disc_s):
            undrawable_suit_cnt[suit] += 1

        if num_suits == 1:
            ways_cnt += comb(13 - undrawable_suit_cnt[self.held_s[0]], len(self.disc_r))
        else: #no saved cards
            for suit, udc in undrawable_suit_cnt.items():
                ways_cnt += comb(13 - udc, len(self.disc_r))

        return ways_cnt



    def pair_jqka(self):
        # nothing held
        if self.held_r_cnts == []:
            draw5 = self._draw_for_ranks( gsize=2, cnt_held_only=False,
                                        pairing_jqka=True)
            return draw5
        # most common card is a singleton
        elif self.held_r_cnts[0][1] == 1:
            draws = self._draw_for_ranks(gsize=2, cnt_held_only=False,
                                        pairing_jqka=True)
            return draws
        elif self.held_r_cnts[0][1] == 2:
            #check for holding low pair
            lows = '23456789T'
            low_pair_bool = self.held_r_cnts[0][0] in lows
            #check for holding two pair
            two_pair_bool = (len(self.held_r_cnts) > 1) and (self.held_r_cnts[1][1] == 2)
            if low_pair_bool or two_pair_bool:
                return 0

            #holding pair of jkqa find everything that DOESN'T improve hand
            return self._count_ways2kick(num_kickers = self.draw_cnt)
        else:
            return 0


    def two_pair(self):
        held_r_avail = {}
        for r in self.held_r:
            held_r_avail[r] = self.__draws[r]

        held_r_avail_grps = Counter(held_r_avail.values())

        # nothing held
        if self.held_r_cnts == []:
            return self._draw_2pair(draw_cnt = 5)
        # most common card is a singleton
        elif self.held_r_cnts[0][1] == 1:
            ways_cnt = 0
            if self.draw_cnt == 4:
                #draw two pairs from the deck
                ways_cnt += self._draw_2pair(draw_cnt = 4)
                #pair up held singleton, draw a pair
                #TODO: possibly replace this block with a call to draw_for_ranks?
                held_draws = list(held_r_avail.values())[0] # ok since only holding 1
                for avail, rcnt in self.nonheld_rank_grps.items():
                    rways = rcnt * comb(avail, 2)
                    new_nhrg = self.nonheld_rank_grps.copy()
                    new_nhrg[avail] -= 1
                    kick_ways = self._count_ways2kick(nonheld_rank_grps = new_nhrg,
                                                     num_kickers = 1)
                    ways_cnt += held_draws * rways * kick_ways

                return ways_cnt
            elif self.draw_cnt == 3: # maybe change this block to draw_cnt in [3,2]

                for havail, hrcnt in held_r_avail_grps.items():
                    #pair up a held card
                    hrways = comb(hrcnt, 1) * comb(havail, 1)
                    #then draw a pair
                    drawways = self._draw_for_ranks(gsize=2, draw_cnt=2,
                                                   draw_only=True,
                                                   second_pair=False)
                    ways_cnt += hrways * drawways
                    #draw a match for both held singles
                    hrways2 = comb(havail, 1) ** hrcnt
                    kick_ways = self._count_ways2kick(num_kickers=1)
                    ways_cnt += hrways2 * kick_ways
                return ways_cnt
            elif self.draw_cnt == 2:
                #draw a match for 2 of the 3 held singles
                return self._draw_2pair(nonheld_rank_grps = held_r_avail_grps,
                                       draw_cnt = 2)

            else:
                return 0

        elif self.held_r_cnts[0][1] == 2:
            #check for holding two pair
            if (len(self.held_r_cnts) > 1) and (self.held_r_cnts[1][1] == 2):
                #find everything that DOESN't improve hand
                return self._count_ways2kick(num_kickers = self.draw_cnt)
            else:
                #holding a pair. take it out of consideration and look for another
                return self._draw_for_ranks(gsize=2, second_pair=True)
        else:
            return 0



    def _draw_2pair(self, nonheld_rank_grps = None, draw_cnt = 4):
        """
        helper for two_pair, originally designed for drawing 2 pairs when,
        drawing 4 or 5 cards.
        there's a mostly symmetrical case for drawing 2 cards and holding
        3 singletons and pairing up 2 of those. so if draw_cnt = 2 then
        choose 1 card from the number available within a rank. (in this case,
        nonheld_rank_grps != self.nonheld_rank_grps, so pass as keyword)
        """
        if nonheld_rank_grps is None:
            nonheld_rank_grps = self.nonheld_rank_grps

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
                    kick_ways = self._count_ways2kick(nonheld_rank_grps = new_nhrg,
                                                     num_kickers = 1)
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
                    kick_ways = self._count_ways2kick(nonheld_rank_grps = new_nhrg,
                                                     num_kickers = 1)
                else:
                    kick_ways = 1

                ways_cnt += mixpair * kick_ways

        return ways_cnt


    def three_kind(self):
        # nothing held or most common card is a singleton
        if self.held_r_cnts == [] or self.held_r_cnts[0][1] == 1:
            draw = self._draw_for_ranks(gsize=3, cnt_held_only=False)
            return draw

        elif self.held_r_cnts[0][1] == 2:
            #check for holding two pair, avoid counting FH
            if (len(self.held_r_cnts) > 1) and (self.held_r_cnts[1][1] == 2):
                return 0

            drawp = self._draw_for_ranks(gsize=3, cnt_held_only=True)
            #if holding a pair and a 3rd card, e.g. 'AA7', drawing '77' will be
            #counted by draw_for_ranks, but this is FH, so subtract this.
            if (len(self.held_r_cnts) == 2) and (self.held_r_cnts[1][1] == 1):
                rext_avail = self.__draws[self.held_r_cnts[1][0]]
                return drawp - comb(rext_avail, 2)
            else:
                return drawp

        elif self.held_r_cnts[0][1] == 3:
            #check for holding FH
            if (len(self.held_r_cnts) == 2) and (self.held_r_cnts[1][1] == 2):
                return 0
            else:
                #find everything that DOESN't improve hand
                return self._count_ways2kick(num_kickers = self.draw_cnt)
        else:
            return 0


    def full_house(self):
        held_r_avail = {}
        for r in self.held_r:
            held_r_avail[r] = self.__draws[r]

        held_r_avail_grps = Counter(held_r_avail.values())

        ways_cnt = 0
        # nothing held
        if self.held_r_cnts == []:
            for avail, rcnt in self.nonheld_rank_grps.items():

                rtrips = rcnt * comb(avail, 3)
                new_nhrg = self.nonheld_rank_grps.copy()
                new_nhrg[avail] -= 1

                pair_ways = 0
                for pavail, prcnt in new_nhrg.items():
                    pair_ways += prcnt * comb(pavail, 2)

                ways_cnt += rtrips * pair_ways
            return ways_cnt

        # most common card is a singleton
        elif self.held_r_cnts[0][1] == 1:

            if self.draw_cnt == 4:
                held_draws = list(held_r_avail.values())[0] # ok since only holding 1
                for heldneed, drawneed in [[1, 3], [2, 2]]:
                    up_held = comb(held_draws, heldneed)
                    draw_grp = self._draw_for_ranks(gsize=drawneed,
                                                   draw_cnt=drawneed,
                                                   draw_only=True)
                    ways_cnt += up_held * draw_grp

                return ways_cnt

            elif self.draw_cnt == 3:
                avail1, avail2 = list(held_r_avail.values())
                ways_cnt += comb(avail1, 2) * comb(avail2, 1)
                ways_cnt += comb(avail1, 1) * comb(avail2, 2)

                return ways_cnt

            else:
                return 0

        elif self.held_r_cnts[0][1] == 2:
            if self.draw_cnt in [3, 2]:
                #tripup held pair
                held_draws = self.__draws[self.held_r_cnts[0][0]]
                tripup_pair = comb(held_draws, 1)
                if self.draw_cnt == 3:
                    #draw trips to go with pair
                    ways_cnt += self._draw_for_ranks(gsize=3, draw_cnt=3,
                                                    draw_only=True)
                    #draw pair to go with tripup pair
                    draws = self._draw_for_ranks(gsize=2, draw_cnt=2,
                                                draw_only=True)
                elif self.draw_cnt == 2:
                    sing_avail = self.__draws[self.held_r_cnts[1][0]]
                    #trip up held singleton
                    ways_cnt += comb(sing_avail, 2)
                    #pair up held singleton
                    draws = comb(sing_avail, 1)

                ways_cnt += tripup_pair * draws

                return ways_cnt
            elif self.draw_cnt == 1:
                #check for holding two pair
                if self.held_r_cnts[1][1] == 2:
                    return sum(held_r_avail.values())
                else:
                    return 0
            else:
                return 0
        elif self.held_r_cnts[0][1] == 3:
            #draw pair with trips,
            if self.draw_cnt == 2:
                draw_pair = self._draw_for_ranks(gsize=2, draw_cnt=2,
                                                draw_only=True)
                return draw_pair
            #trips + pairup held singleton
            elif self.draw_cnt == 1:
                # count avail cards to pairup held singleton
                return self.__draws[self.held_r_cnts[1][0]]
            elif self.draw_cnt == 0 and self.held_r_cnts[1][1] == 2:
                #holding FH
                return 1
            else:
                return 0

        else:
            return 0


    def four_kind(self, specials = None):
        """
        specials: (list of str) any ranks chars that get a bonus on 4 of a kind.
            e.g. 'A', '8', '7' for Aces and Eights payout table. Remove these
            from the nominal four_kind count and call a method for each bonus.

            For example with Aces and Eights payouts, .analyze() will call:
            self.four_kind(specials = ['A', '7', '8'])
            self.four_kindA8()
            self.four_kind7()
        """

        draw = self._draw_for_ranks(gsize=4, cnt_held_only=False)
        if specials is None:
            return draw
        else:
            return draw - self._four_kind_special(specials)


    def four_kindA8(self):
        """Bonus for four of kind with Aces or Eights"""
        return self._four_kind_special('A8')


    def four_kind7(self):
        """Bonus for four of kind with Sevens"""
        return self._four_kind_special('7')

    def four_kindA(self):
        """Bonus for Aces (used in Triple Bonus Plus)"""
        return self._four_kind_special('A')

    def four_kind234(self):
        """Bonus for 2,3,4 (used in Triple Bonus Plus)"""
        return self._four_kind_special('234')


    def _four_kind_special(self, special_cards):
        """
        special_card: (str) rank character that gets a bonus on four of a kind.
            e.g. 'A', '8', '7' for Aces and Eights payout table.
        need to specify these special cards for the main four_kind method to
        avoid double counting them.
        """
        ways_cnt = 0
        for special_card in special_cards:
            kickers = len(self.disc_r) - self.__draws[special_card]
            if (kickers < 0) or (special_card in self.disc_r):
                continue
            elif kickers == 0:
                ways_cnt += 1
            else:
                #47 draw cards to start, drawing 5 draw the 4 specials and 1 kicker
                ways_cnt += 47 - self.__draws[special_card]
        return ways_cnt


    def straight(self):

        def prod_list(lst):
            accum = 1
            for el in lst:
                accum *= el
            return accum

        ways_cnt = 0
        #subtract royal and straight flush from the count
        ways_cnt -= self.royal_flush()
        ways_cnt -= self.straight_flush()
        if self.held_r_cnts == []:
            for s in STRAIGHTS:
                ways_cnt += prod_list([self.__draws[r] for r in s])
            return ways_cnt
        elif self.held_r_cnts[0][1] != 1:
            #holding a pair or more
            return 0
        else:
            strts_cop, draws_cop = self._potential_straights()
            for sc in strts_cop:
                if sc is not None:
                    ways_cnt += prod_list([draws_cop[r] for r in sc])

            return ways_cnt


    def _potential_straights(self, include_royals = True):
        """
        Helper func for hands with straights.
        Switches the strings in list of strings representing straights
        e.g. 'A2345', '789TJ' to None if holding a card that is not in
        the given straight. Also sets the draws for that rank to 1.
        Returns these.
        """
        if include_royals:
            strts_cop = STRAIGHTS[:]
            enum_strts = list(enumerate(STRAIGHTS))
        else:
            strts_cop = STRAIGHTS[:-1]
            enum_strts = list(enumerate(STRAIGHTS[:-1]))

        draws_cop = self.__draws.copy()
        for r in self.held_r:
            draws_cop[r] = 1
            for ind, strt in enum_strts:
                if r not in strt:
                    strts_cop[ind] = None
        return strts_cop, draws_cop


    def _draw_for_ranks(self, gsize = 3, cnt_held_only = False,
                       pairing_jqka = False, second_pair = False,
                       draw_cnt = None, draw_only = False):
        """
        Given held cards and discards count ways to draw for pairs/3kind/4_of_a_kind
        based on collecting them purely from draw pile or adding to the held cards

        INPUT:
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

        OUTPUT: (int)
        """
        #override the original draw count if necessary
        draw_cnt = self.draw_cnt if draw_cnt is None else draw_cnt

        #dealing with two_pair stuff
        if second_pair:
            rmv_held_pair = Counter({Counter(self.held_r).most_common(1)[0]: 2})
            nonheld_ranks_mod = self.__draws - rmv_held_pair
            for r in self.held_r:
                nonheld_ranks_mod[r] = 0
            nonheld_rank_grps_mod = Counter(nonheld_ranks_mod.values())
        else:
            nonheld_ranks_mod = self.nonheld_ranks
            nonheld_rank_grps_mod = self.nonheld_rank_grps
        #remove everything but JQKA if only considering those pairs
        if pairing_jqka:
            nonheld_jqka = self.nonheld_ranks - Counter('23456789T'*4)
            nonheld_jqka_grps = Counter(nonheld_jqka.values())
            draw_grp_iter = nonheld_jqka_grps.items()
        else:
            draw_grp_iter = nonheld_rank_grps_mod.items()

        ways_cnt = 0

        #add up ways of making group with all draw cards
        if not cnt_held_only:
            for avail, rcnt in draw_grp_iter:
                # count ranks that we can select 3 cards from.
                if gsize <= draw_cnt:
                    rways = rcnt * comb(avail, gsize)
                    kickers = draw_cnt - gsize
                    if kickers > 0:
                        new_nhrg = nonheld_rank_grps_mod.copy()
                        new_nhrg[avail] -= 1
                        kick_ways = self._count_ways2kick(nonheld_rank_grps = new_nhrg,
                                                         num_kickers = kickers)
                    else:
                        kick_ways = 1
                    #print(rcnt, avail, kick_ways, rways)
                    ways_cnt += rways * kick_ways
                else:
                    continue

        #add up ways of adding to the held cards
        if not draw_only:
            for r, hcnt in Counter(self.held_r).items():
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
                            kick_ways = self._count_ways2kick(num_kickers = kickers,
                                        nonheld_rank_grps = nonheld_rank_grps_mod)
                        else:
                            sp_nhrg = nonheld_rank_grps_mod - Counter({nonheld_ranks_mod[r]:1})
                            kick_ways = self._count_ways2kick(nonheld_rank_grps = sp_nhrg,
                                                             num_kickers = kickers)
                    else:
                        kick_ways = 1
                    #print(hcnt, kickers, kick_ways, hways)

                    ways_cnt += hways * kick_ways
                else:
                    continue

        return ways_cnt


    def _count_ways2kick(self, nonheld_rank_grps = None, num_kickers = 1):
        """
        Helper function for counting "kickers", that is cards that are drawn
        but are irrelevant to poker hand because other drawn cards already
        completed it.
        """
        # possible combinations, if num_kickers = 2 and there are 8 ranks with 4
        # cards to draw one elem will be (4, 4), so run counter on this to get things
        # to work properly. then comb(8, 2)*comb(4, 1)**2

        # some methods like full_house, two_pair need to use a modified version
        # of nonheld_rank_grps, so even though it is an instance attribute,
        # still take it as a keyword.
        if nonheld_rank_grps is None:
            nonheld_rank_grps = self.nonheld_rank_grps

        kick_cnt = 0
        for suit_cnt_tup in combinations_with_replacement(nonheld_rank_grps, num_kickers):
            multiplier = 1
            for suit_cnt_key, cnt in Counter(suit_cnt_tup).items():
                num_ranks = nonheld_rank_grps[suit_cnt_key]
                multiplier *= comb(num_ranks, cnt) * suit_cnt_key ** cnt
            kick_cnt += multiplier
        return kick_cnt

if __name__ == '__main__':
    print(HandAnalyzer('7c7h7d8s7s').analyze(return_full_analysis=True))
