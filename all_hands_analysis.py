from functools import partial
from itertools import combinations, product
from vp_analyzer import HandAnalyzer
import time
import multiprocessing

def all_hands_gen():
    ranks = 'A23456789TJQK'
    suits = 'CDHS'

    deck = product(ranks, suits)
    return combinations(deck, 5)

def hand2str(hand_tup):
    hstr = ''
    for r, s in hand_tup:
        hstr += r + s
    return hstr

def analyze_some_hands(hands_gen, n = 10000):
    analysis = []
    for ind, hand in enumerate(hands_gen):
        if ind >= n:
            break
        handstr = hand2str(hand)
        analysis.append(HandAnalyzer(handstr).analyze())

    return analysis

def analyze_hand(handstr, payouts = None):
    ## moved to vp_analyzer
    # #handstr = hand2str(hand_tup)
    # results = HandAnalyzer(handstr).analyze()
    # max_ev = 0
    # best_ev_disc = 0
    # for holddisc in results:
    #     cur_ev = results[holddisc]['expected_val']
    #
    #     equal_bool = () and (cur_disc > best_ev_disc)
    #     if cur_ev > max_ev:
    #         besthold = holddisc
    #         max_ev = cur_ev
    #         best_ev_disc = holddisc.count('XX')
    #     elif cur_ev == max_ev:
    #         cur_ev_disc = holddisc.count('XX')
    #         if cur_ev_disc > best_ev_disc:
    #             besthold = holddisc
    #             best_ev_disc = cur_ev_disc
    #     else:
    #         continue
    #
    hand = HandAnalyzer(handstr, payouts=payouts)
    results = hand.analyze(return_full_analysis=False)
    return '{},{},{}'.format(handstr, *results)


def limit_hands_wrapper(hands_gen, n = 10000):
    for ind, hand in enumerate(hands_gen):
        if ind >= n:
            break
        else:
            yield hand

def save_chunks(hands_lst, filename_base, payouts = None, chunksize = 100000):
    procs = multiprocessing.cpu_count()
    if payouts is None:
        mapfunc = analyze_hand
    else:
        kwargs = {'payouts': payouts}
        mapfunc = partial(analyze_hand, **kwargs)

    for ind in range(0, len(hands_lst), chunksize):

        pool = multiprocessing.Pool(processes = procs)
        if ind+chunksize <= len(hands_lst):
            hands_analysis = pool.map(mapfunc, hands_lst[ind:ind+chunksize])
        else:
            hands_analysis = pool.map(mapfunc, hands_lst[ind:])

        fname = filename_base + str(ind) + '.txt'
        with open(fname, 'w') as fout:
            # write results on separate lines, include \n on last line
            fout.write('\n'.join(hands_analysis)+'\n')
        print('Saved: {}'.format(fname))
    return str(ind)


if __name__ == '__main__':
    print(time.localtime())

    #all_hands = all_hands_gen()
    #print(len(analyze_some_hands(all_hands)))
    #print([x for x in limit_hands_wrapper(all_hands_gen(), n = 10)])


    #pool = multiprocessing.Pool(processes = procs)
    #analysis = pool.map(analyze_hand, limit_hands_wrapper(all_hands_gen(), n = 10))
    #print(analysis)
    #print([ha[('X','X','X','X','X')]['expected_val'] for ha in analysis])
    aces8s_d = {'flush': 5,
                  'four_kind': 25,
                  'four_kind7': 50,
                  'four_kindA8': 80,
                  'full_house': 8,
                  'pair_jqka': 1,
                  'royal_flush': 800,
                  'straight': 4,
                  'straight_flush': 50,
                  'three_kind': 3,
                  'two_pair': 2}
    all_hands_str_l = list(map(hand2str, all_hands_gen()))
    indout = save_chunks(all_hands_str_l, 'poker_hand_evs_aces8s_',
                         payouts = aces8s_d, chunksize = 200000)
    print(time.localtime())
