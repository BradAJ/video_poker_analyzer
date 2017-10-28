from collections import Counter
from scipy.misc import comb
import unittest
from vp_analyzer import HandAnalyzer

# Run reminder:
# python -m unittest test.test_HandAnalyzer

class TestHandAnalyzer(unittest.TestCase):
    def setUp(self):
        self.h1 = HandAnalyzer('ahjcts7s4h')
        self.hold_d_h1AJ = {'d': [('T', 'S'), ('7', 'S'), ('4', 'H')],
                               'h': [('A', 'H'), ('J', 'C')]}
        self.hold_bool_h1AJ = [True]*2 + [False]*3

        self.h2 = HandAnalyzer('qd9c8d5c2c')
        self.h3 = HandAnalyzer('qd9c8dacad')
        self.junk = HandAnalyzer('ts9c8d5c2h')

        self.aces8s_d = {'pair_jqka': 1, 'two_pair': 2, 'three_kind': 3,
                        'straight': 4, 'flush': 5, 'full_house': 8,
                        'four_kind': 25, 'four_kind7':50, 'four_kindA8':80,
                        'straight_flush': 50, 'royal_flush': 800}

    def test_draws(self):
        full_ranks = '235689QK'
        h1_ranks = 'AJT74'
        test_h1_deck = Counter(full_ranks*4) + Counter(h1_ranks*3)
        h1_deck = self.h1.draws()
        self.assertEqual(h1_deck, test_h1_deck)

    def test_hold(self):
        hold_d = self.h1.hold(self.hold_bool_h1AJ)
        self.assertEqual(hold_d, self.hold_d_h1AJ)

    def test_pivot_held_d(self):
        test_pivot = [('A', 'J'), ('H', 'C'), ('T', '7', '4'), ('S', 'S', 'H')]
        pivot = self.h1.pivot_held_d(self.hold_d_h1AJ)
        self.assertEqual(pivot, test_pivot)

    def test_royal_flush(self):
        self.assertEqual(self.h1.royal_flush(self.hold_d_h1AJ), (0, 1))

        holda = self.h1.hold([True] + [False]*4)
        self.assertEqual(self.h1.royal_flush(holda), (1, comb(47, 4)))

        discard_all = self.h1.hold([False]*5)
        self.assertEqual(self.h1.royal_flush(discard_all), (1, comb(47, 5)))

        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.royal_flush(discard_h2), (3, comb(47, 5)))

    def test_three_kind(self):
        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.three_kind(discard_h2), (31502, comb(47, 5)))

        h3holdaa = self.h3.hold([False]*3 + [True]*2)
        self.assertEqual(self.h3.three_kind(h3holdaa), (1854, comb(47, 3)))

        h3hold8aa = self.h3.hold([False]*2 + [True]*3)
        self.assertEqual(self.h3.three_kind(h3hold8aa), (84, comb(47, 2)))

        fh = HandAnalyzer('qdqcqh2s2d')
        self.assertEqual(fh.three_kind(fh.hold([True]*5)), (0, 1))
        self.assertEqual(fh.three_kind(fh.hold([True]*3+[False]*2)), (968, comb(47, 2)))


    def test_draw_for_ranks(self):
        holdq = self.h2.hold([True] + [False]*4)
        h2d4r = self.h2.draw_for_ranks(holdq, gsize = 3,
                                     cnt_held_only = False)
        self.assertEqual(h2d4r, 4102)


        h3d4r = self.h3.draw_for_ranks(self.h3.hold([False]*3 + [True]*2), gsize = 3)
        self.assertEqual(h3d4r, 1893)

    def test_pair_jqka(self):
        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.pair_jqka(holdq), (45456, comb(47, 4)))

        holdaa = self.h3.hold([False]*3 + [True]*2)
        self.assertEqual(self.h3.pair_jqka(holdaa), (11559, comb(47, 3)))

        twop = HandAnalyzer('acad8h8s2c')
        self.assertEqual(twop.pair_jqka(twop.hold([True]*2 + [False]*3)), (11520, comb(47, 3)))

        nohi = HandAnalyzer('td9c8d5c2c')
        self.assertEqual(nohi.pair_jqka(nohi.hold([False]*5)), (241680, comb(47, 5)))

        lowp = HandAnalyzer('qcjckdtdth')
        self.assertEqual(lowp.pair_jqka(lowp.hold([True]*4+[False])), (9, comb(47, 1)))

        threek = HandAnalyzer('4h4c5h3h4s')
        self.assertEqual(threek.pair_jqka(threek.hold([True]*5)), (0, 1))


    def test_four_kind(self):
        holdaa = self.h3.hold([False]*3 + [True]*2)
        self.assertEqual(self.h3.four_kind(holdaa), (45, comb(47, 3)))

        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.four_kind(holdq), (52, comb(47, 4)))

        h3hold8aa = self.h3.hold([False]*2 + [True]*3)
        self.assertEqual(self.h3.four_kind(h3hold8aa), (1, comb(47, 2)))

        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.four_kind(discard_h2), (344, comb(47, 5)))

        fh = HandAnalyzer('qdqcqh2s2d')
        self.assertEqual(fh.four_kind(fh.hold([True]*3 + [False]*2)), (46, comb(47, 2)))

        fourk = HandAnalyzer('qcqdqhqs2c')
        self.assertEqual(fourk.four_kind(fourk.hold([True]*4 + [False])), (47, comb(47, 1)))

        h2A8 = HandAnalyzer(''.join(self.h2.hand), payouts = self.aces8s_d)
        h2A8holdq = h2A8.hold([True]+[False]*4)
        h2A8holdq8 = h2A8.hold([True,False,True]+[False]*2)
        spec = ['A', '7', '8']
        self.assertEqual(h2A8.four_kind(h2A8holdq, specials=spec), (50, comb(47, 4)))
        self.assertEqual(h2A8.four_kind(h2A8holdq8, specials=spec), (1, comb(47, 3)))

        junk6 = HandAnalyzer('tc9d6h5s2c', payouts = self.aces8s_d)
        j6disc = junk6.hold([False]*5)
        self.assertEqual(junk6.four_kind(j6disc, specials=spec), (215, comb(47, 5)))

    def test_two_pair(self):
        twop = HandAnalyzer('acad8h8s2c')
        self.assertEqual(twop.two_pair(twop.hold([True]*4 + [False])), (43, comb(47, 1)))
        self.assertEqual(twop.two_pair(twop.hold([True]*5)), (1, 1))
        self.assertEqual(twop.two_pair(twop.hold([True]*3 + [False]*2)), (149, comb(47, 2)))

        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.two_pair(discard_h2), (71802, comb(47, 5)))

        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.two_pair(holdq), (8874, comb(47, 4)))

        holdq9 = self.h2.hold([True]*2 + [False]*3)
        self.assertEqual(self.h2.two_pair(holdq9), (711, comb(47, 3)))

        holdq98 = self.h2.hold([True]*3 + [False]*2)
        self.assertEqual(self.h2.two_pair(holdq98), (27, comb(47, 2)))

        hold98a = self.h3.hold([False, True, True, True, False])
        self.assertEqual(self.h3.two_pair(hold98a), (21, comb(47, 2)))

        holdq985 = self.h2.hold([True]*4 + [False]*1)
        self.assertEqual(self.h2.two_pair(holdq985), (0, 1))

        h3hold8aa = self.h3.hold([False]*2 + [True]*3)
        self.assertEqual(self.h3.two_pair(h3hold8aa), (186, comb(47, 2)))

        holdaa = self.h3.hold([False]*3 + [True]*2)
        self.assertEqual(self.h3.two_pair(holdaa), (2592, comb(47, 3)))

        discaa = self.h3.hold([True]*3 + [False]*2)
        self.assertEqual(self.h3.two_pair(discaa), (27, comb(47, 2)))

        fourk = HandAnalyzer('qcqdqhqs2c')
        self.assertEqual(fourk.two_pair(fourk.hold([True]*4 + [False])), (0, 1))

        fh = HandAnalyzer('qdqcqh2s2d')
        self.assertEqual(fh.two_pair(fh.hold([True]*5)), (0, 1))

    def test_full_house(self):
        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.full_house(discard_h2), (2124, comb(47, 5)))

        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.full_house(holdq), (288, comb(47, 4)))

        holdq9 = self.h2.hold([True]*2 + [False]*3)
        self.assertEqual(self.h2.full_house(holdq9), (18, comb(47, 3)))

        holdq98 = self.h2.hold([True]*3 + [False]*2)
        self.assertEqual(self.h2.full_house(holdq98), (0, 1))

        holdaa = self.h3.hold([False]*3 + [True]*2)
        self.assertEqual(self.h3.full_house(holdaa), (165, comb(47, 3)))

        h3hold8aa = self.h3.hold([False]*2 + [True]*3)
        self.assertEqual(self.h3.full_house(h3hold8aa), (9, comb(47, 2)))

        trips = HandAnalyzer('qcqdqh7c2d')
        tripsonly = trips.hold([True]*3+[False]*2)
        self.assertEqual(trips.full_house(tripsonly), (66, comb(47, 2)))
        tripsp1 = trips.hold([True]*4+[False])
        self.assertEqual(trips.full_house(tripsp1), (3, comb(47, 1)))

        twop = HandAnalyzer('acad8h8s2c')
        self.assertEqual(twop.full_house(twop.hold([True]*4 + [False])), (4, comb(47, 1)))

        fh = HandAnalyzer('qdqcqh2s2d')
        self.assertEqual(fh.full_house(fh.hold([True]*5)), (1, 1))
        self.assertEqual(fh.full_house(fh.hold([True]*4 + [False])), (2, comb(47, 1)))


    def test_straight(self):
        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.straight(discard_h2), (5832, comb(47, 5)))

        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.straight(holdq), (590, comb(47, 4)))

        holdq9 = self.h2.hold([True]*2 + [False]*3)
        self.assertEqual(self.h2.straight(holdq9), (112, comb(47, 3)))

        holdq98 = self.h2.hold([True]*3 + [False]*2)
        self.assertEqual(self.h2.straight(holdq98), (16, comb(47, 2)))

    def test_straight_flush(self):
        discard_h2 = self.h2.hold([False]*5)
        self.assertEqual(self.h2.straight_flush(discard_h2), (21, comb(47, 5)))

        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.straight_flush(holdq), (1, comb(47, 4)))

        h1aj = self.h1.hold([True]*2+[False]*3)
        self.assertEqual(self.h1.straight_flush(h1aj), (0, 1))

        #junk = HandAnalyzer('ts9c8d5c2h')
        junkd = self.junk.hold([False]*5)
        self.assertEqual(self.junk.straight_flush(junkd), (16, comb(47, 5)))
        junkt = self.junk.hold([True]+[False]*4)
        self.assertEqual(self.junk.straight_flush(junkt), (4, comb(47, 4)))
        junk8 = self.junk.hold([False, False, True, False, False])
        self.assertEqual(self.junk.straight_flush(junk8), (5, comb(47, 4)))

    def test_flush(self):
        holdq = self.h2.hold([True] + [False]*4)
        self.assertEqual(self.h2.flush(holdq), (328, comb(47, 4)))

        holdq9 = self.h2.hold([True]*2 + [False]*3)
        self.assertEqual(self.h2.flush(holdq9), (0, 1))

        holdq8 = self.h2.hold([True, False, True, False, False])
        self.assertEqual(self.h2.flush(holdq8), (164, comb(47, 3)))

        #junk = HandAnalyzer('ts9c8d5c2h')
        junkd = self.junk.hold([False]*5)
        self.assertEqual(self.junk.flush(junkd), (2819, comb(47, 5)))
        junkt = self.junk.hold([True]+[False]*4)
        self.assertEqual(self.junk.flush(junkt), (490, comb(47, 4)))

    def test_four_kindA8(self):

        h2A8 = HandAnalyzer(''.join(self.h2.hand), payouts = self.aces8s_d)
        self.assertEqual(h2A8.four_kindA8(h2A8.hold([True]+[False]*4)), (1, comb(47, 4)))

        junk6 = HandAnalyzer('tc9d6h5s2c', payouts = self.aces8s_d)
        self.assertEqual(junk6.four_kindA8(junk6.hold([False]*5)), (86, comb(47, 5)))

        aaa = HandAnalyzer('ACADAH9CQH',payouts = self.aces8s_d)
        self.assertEqual(aaa.four_kindA8(aaa.hold([True]*3+[False]*2)), (46, comb(47, 2)))

    def test_four_kind7(self):
        h2A8 = HandAnalyzer(''.join(self.h2.hand), payouts = self.aces8s_d)
        self.assertEqual(h2A8.four_kind7(h2A8.hold([True]+[False]*4)), (1, comb(47, 4)))
        self.assertEqual(h2A8.four_kind7(h2A8.hold([True,False,True]+[False]*2)), (0, comb(47, 3)))

        junk6 = HandAnalyzer('tc9d6h5s2c', payouts = self.aces8s_d)
        self.assertEqual(junk6.four_kind7(junk6.hold([False]*5)), (43, comb(47, 5)))


    def test_analyze(self):
        #based on results from: https://www.videopokertrainer.org/calculator/
        junk_plays = self.junk.analyze()
        disc_all = ('XX','XX','XX','XX','XX')
        exp_val_discardjunk = junk_plays[disc_all]['expected_val']
        self.assertEqual(round(exp_val_discardjunk, 5), round(0.35843407071, 5))

        exp_val_holdt = junk_plays[('TS', 'XX', 'XX', 'XX', 'XX')]['expected_val']
        self.assertEqual(round(exp_val_holdt, 5), round(0.32971715302, 5))

        h2_plays = self.h2.analyze()
        exp_val_holdq = h2_plays[('QD', 'XX', 'XX', 'XX', 'XX')]['expected_val']
        self.assertEqual(round(exp_val_holdq, 5), round(0.4741961707734, 5))

        exp_val_holdq8 = h2_plays[('QD', 'XX', '8D', 'XX', 'XX')]['expected_val']
        self.assertEqual(round(exp_val_holdq8, 5), round(0.41036077705827, 5))

        h3_plays = self.h3.analyze()
        exp_val_holdaa = h3_plays[('XX', 'XX', 'XX', 'AC', 'AD')]['expected_val']
        self.assertEqual(round(exp_val_holdaa, 5), round(1.536540240518, 5))

        exp_val_holdaa8 = h3_plays[('XX', 'XX', '8D', 'AC', 'AD')]['expected_val']
        self.assertEqual(round(exp_val_holdaa8, 5), round(1.4162812210915, 5))

        lowp = HandAnalyzer('qcjckdtdth').analyze()
        exp_val_qjkt = lowp[('QC', 'JC', 'KD', 'TD', 'XX')]['expected_val']
        self.assertEqual(round(exp_val_qjkt, 5), round(0.8723404255319, 5))

        h2A8 = HandAnalyzer(''.join(self.h2.hand), payouts = self.aces8s_d)
        h2A8_plays = h2A8.analyze()
        exp_val_h2A8 = h2A8_plays[('QD', 'XX', 'XX', 'XX', 'XX')]['expected_val']
        self.assertEqual(round(exp_val_h2A8, 5), round(0.47119109690802569, 5))

        junk6 = HandAnalyzer('tc9d6h5s2c', payouts = self.aces8s_d)
        j6_plays = junk6.analyze()
        exp_val_j6 = j6_plays[disc_all]['expected_val']
        j6_disc_ev = 0.3588441261353939
        self.assertEqual(round(exp_val_j6, 5), round(j6_disc_ev, 5))
        j6_best = junk6.analyze(return_full_analysis = False)
        self.assertEqual(j6_best[0], ''.join(disc_all))
        self.assertEqual(round(j6_best[1], 5), round(j6_disc_ev, 5))

        aaa = HandAnalyzer('ACADAH9CQH',payouts = self.aces8s_d)
        aaa_best = aaa.analyze(return_full_analysis = False)
        self.assertEqual(aaa_best[0], ''.join(('AC', 'AD', 'AH', 'XX', 'XX')))
        self.assertEqual(round(aaa_best[1], 5), round(6.5818686401480111, 5))
