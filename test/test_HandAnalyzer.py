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








