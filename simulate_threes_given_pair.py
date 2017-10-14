from itertools import product
from random import shuffle
from collections import Counter

def collect_n_pairs(n_samples):
    rank = 'A234567890JQK'
    suit = 'CDHS'
    deck = list(product(rank, suit))

    hands_w_pair = []
    n_hands = 0
    while len(hands_w_pair) < n_samples:
        shuffle(deck)
        hand = deck[:5]
        n_hands += 1
        if len(set([card[0] for card in hand])) < 5:
            hands_w_pair.append(hand)
    print("hands generated: {}".format(n_hands))
    return hands_w_pair

def count3s_4s(hands):
    pair, threek, fourk = 0, 0, 0
    for hand in hands:
        max_occurrence = Counter([card[0] for card in hand]).most_common(1)[0][1]
        if max_occurrence == 2:
            pair += 1
        elif max_occurrence == 3:
            threek += 1
        elif max_occurrence == 4:
            fourk += 1
        else:
            raise Exception('Unexpected count: {}'.format(hand))
    return pair, threek, fourk, (threek + fourk) / float(pair)
