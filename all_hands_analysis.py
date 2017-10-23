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

def analyze_hand(handstr):
    #handstr = hand2str(hand_tup)
    results = HandAnalyzer(handstr).analyze()
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
    line = '{}, {}, {}'.format(handstr, bestholdstr, str(results[besthold]['expected_val']))
    return line

def limit_hands_wrapper(hands_gen, n = 10000):
    for ind, hand in enumerate(hands_gen):
        if ind >= n:
            break
        else:
            yield hand

def save_chunks(hands_lst, filename_base, chunksize = 100000):
    procs = multiprocessing.cpu_count()
    for ind in range(0, len(hands_lst), chunksize):

        pool = multiprocessing.Pool(processes = procs)
        if ind+chunksize <= len(hands_lst):
            hands_analysis = pool.map(analyze_hand, hands_lst[ind:ind+chunksize])
        else:
            hands_analysis = pool.map(analyze_hand, hands_lst[ind:])

        fname = filename_base + str(ind) + '.txt'
        with open(fname, 'w') as fout:
            fout.write('\n'.join(hands_analysis))
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

    all_hands_str_l = list(map(hand2str, all_hands_gen()))
    indout = save_chunks(all_hands_str_l, 'poker_hand_evs_', chunksize = 100000)
    print(time.localtime())
