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

    def test_analyze(self):
        #based on results from: https://www.videopokertrainer.org/calculator/
        junk_plays = self.junk.analyze()
        exp_val_discardjunk = junk_plays[('X','X','X','X','X')]['expected_val']
        self.assertEqual(round(exp_val_discardjunk, 5), round(0.35843407071, 5))

        exp_val_holdt = junk_plays[('TS', 'X', 'X', 'X', 'X')]['expected_val']
        self.assertEqual(round(exp_val_holdt, 5), round(0.32971715302, 5))

        h2_plays = self.h2.analyze()
        exp_val_holdq = h2_plays[('QD', 'X', 'X', 'X', 'X')]['expected_val']
        self.assertEqual(round(exp_val_holdq, 5), round(0.4741961707734, 5))

        exp_val_holdq8 = h2_plays[('QD', 'X', '8D', 'X', 'X')]['expected_val']
        self.assertEqual(round(exp_val_holdq8, 5), round(0.41036077705827, 5))

        h3_plays = self.h3.analyze()
        exp_val_holdaa = h3_plays[('X', 'X', 'X', 'AC', 'AD')]['expected_val']
        self.assertEqual(round(exp_val_holdaa, 5), round(1.536540240518, 5))

        exp_val_holdaa8 = h3_plays[('X', 'X', '8D', 'AC', 'AD')]['expected_val']
        self.assertEqual(round(exp_val_holdaa8, 5), round(1.4162812210915, 5))
