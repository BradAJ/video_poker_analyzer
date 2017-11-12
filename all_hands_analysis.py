from functools import partial
from itertools import combinations, product
import json
from vp_analyzer import HandAnalyzer
import time
import multiprocessing

"""
Script to generate a series of files that together contain all ~2.6M five-card
poker hands and the optimal discard for a given video poker payout table, along
with the expected value of that play.

Written to be run in parallel across multiple cores via multiprocessing.
"""

def all_hands_gen():
    ranks = 'A23456789TJQK'
    suits = 'cdhs'

    deck = product(ranks, suits)
    return combinations(deck, 5)

def hand2str(hand_tup):
    hstr = ''
    for r, s in hand_tup:
        hstr += r + s
    return hstr

def analyze_hand(handstr, payouts = None, return_bestdisc_cnts = True):
    hand = HandAnalyzer(handstr, payouts=payouts)
    results = hand.analyze(return_full_analysis=False,
                           return_bestdisc_cnts = return_bestdisc_cnts)
    if return_bestdisc_cnts:
        return {handstr: results}
    else:
        return '{},{},{}'.format(handstr, *results)


def save_chunks(hands_lst, filename_base, payouts = None, chunksize = 100000,
                return_bestdisc_cnts = False):
    """
    Wrapper func for spreading analysis work across available cores, and saving
    intermediate results rather than waiting to write out the results of all
    hands in a single file.
    Why?:
    Analysis of a given hand's 32 possible discards takes between 0.01 and 0.1s
    with a single core on my machine, so depending on setup, analysis of all
    possible hands will likely take several hours.

    INPUT:
    hands_lst: (list of str) List of 10-char strings of poker hands.
    filename_base: (str) base name of text files to be written. these will be
        appended with the lowest count of chunksize and '.txt' or '.json'. e.g.
        filename_base = "poker_hands_" writes out poker_hands_0.txt,
        poker_hands_100000.txt, etc. (if chunksize = default)
    payouts: (dict) Payout value of each winning hand.
        If None, see: vp_analyzer.HandAnalyzer, default is for "9-6 Jacks or
        Better"
    chunksize: (int) Number of hands to collect in each output file. Usually set
        to be some sizeable fraction of len(hands_lst).
    return_bestdisc_cnts: (bool) Return win counts for best discard strategy.
        This returns a nested dict of {hand:{bestdiscstr:{win counts, exp val}}}
        for each hand, saved as a json. See vp_analyzer.HandAnalyzer.analyze
        for more info.

    OUTPUT:
    Files to disk: (text)

    """
    procs = multiprocessing.cpu_count()
    if payouts is None:
        mapfunc = analyze_hand
    else:
        kwargs = {'payouts': payouts, 'return_bestdisc_cnts': return_bestdisc_cnts}
        mapfunc = partial(analyze_hand, **kwargs)

    for ind in range(0, len(hands_lst), chunksize):

        pool = multiprocessing.Pool(processes = procs)
        if ind+chunksize <= len(hands_lst):
            hands_analysis = pool.map(mapfunc, hands_lst[ind:ind+chunksize])
        else:
            hands_analysis = pool.map(mapfunc, hands_lst[ind:])

        fname = filename_base + str(ind)
        if return_bestdisc_cnts:
            with open(fname + '.json', 'w') as fout:
                json.dump(hands_analysis, fout)
        else:
            with open(fname + '.txt', 'w') as fout:
                # write results on separate lines, include \n on last line
                fout.write('\n'.join(hands_analysis)+'\n')
        print('Saved: {}'.format(fname))


def flatten_bestdisc_json_chunks2df(json_chunks):
    """Helper to convert a list of nested dicts (from save_chunks with
    return_bestdisc_cnts == True) to a flattened list of dicts, suitable as
    input to a Pandas DataFrame."""
    unnest = []
    for chunk in json_chunks:
        for hand_d in chunk:
            hand = hand_d.keys()[0]
            flat_d = {'hand': hand}
            holds = hand_d[hand].keys()[0]
            flat_d['holds'] = holds
            flat_d.update(hand_d[hand][holds])
            unnest.append(flat_d)

    return unnest



if __name__ == '__main__':
    print(time.localtime())

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
    # indout = save_chunks(all_hands_str_l, 'poker_hand_evs_aces8s_',
    #                      payouts = aces8s_d, chunksize = 200000)


    tripbonusplus_d = {'pair_jqka': 1, 'two_pair': 1, 'three_kind': 3,
                    'straight': 4, 'flush': 5, 'full_house': 9,
                    'four_kind': 50, 'four_kind234':120, 'four_kindA':240,
                    'straight_flush': 100, 'royal_flush': 800}

    indout = save_chunks(all_hands_str_l, 'poker_hands_win_cnts_triplebonusplus_',
                         payouts = tripbonusplus_d, chunksize = 200000,
                         return_bestdisc_cnts = True)
    print(time.localtime())
