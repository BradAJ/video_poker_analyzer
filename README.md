## Video Poker Analyzer

Python code to calculate the optimal discard strategy for a given video poker hand and payout table (currently works for "Jacks or Better" and "Aces and Eights" tables). See: `vp_analyzer.HandAnalyzer`.

all_hands_analysis: Script that calls `HandAnalyzer` and saves strategy and expected value of the play for all ~2.6M possible hands (assuming a 52 card deck).

tl;dr:

The game of poker is played with a great number of variations, and it is often said that the game is as much about your opponent as the cards. While that is true of the version commonly seen on TV, there are other variations of poker where this is not true. Specifically, in "video poker" a player does not have an opponent per se, just a machine that includes a random number generator.

In the simplest version of video poker each poker hand between a pair and a royal flush return some multiple of the input bet. Most video poker machines and software use [Five-Card Draw](https://en.wikipedia.org/wiki/Five-card_draw) as the base poker game. After receiving an initial deal of five cards the player may hold or discard any combination of these cards, in order to maximize the poker hand value. Each discard is replaced with a card from the remaining deck. After drawing replacement cards for each discard, the round ends and any winning hands are paid according to a payout table displayed on the video poker machine (or software GUI).

The version of poker described here is a solved game, in the sense that there is an optimal play (i.e. choice of which cards to hold/discard) that maximizes the expected payout for any given hand. Calculating the expected value of a particular discard strategy is a problem of combinatorics. That is, you need to count up all the ways to make a particular hand. The total expected value of a particular discard strategy for a given hand is just the weighted sum of the ways to make all the winning hands (where the weights are the multipliers from the payout table) divided by the total number of resulting hands.

`vp_analyzer.HandAnalyzer` is a Python class that takes a poker hand as a string as input. Calling `.analyze()` on the `HandAnalyzer` object returns a nested dictionary containing each discard strategy and the count of the ways of obtaining winning hands with that strategy, along with its total expected value.

**Note on card representation:** Hands are represented as 10-character long strings, with a card rank character followed by a suit character. The expected rank characters are: A, 2, 3, 4, 5, 6, 7, 8, 9, T, J, Q, K. The expected suit characters are: c, d, h, s. (Though the input to `HandAnalyzer` is Case-Insensitive). When dealing with discards, cards to be replaced are represented by 'XX'. For example, a hand containing: Three of Clubs, Ace of Hearts, Three of Diamonds, Ten of Hearts, Jack of Spades; is '3cAh3dThJs' and one discard strategy would be to hold the pair of threes: '3cXX3dXXXX'. (When playing with a payout table for "9-6 Jacks or Better", described below, this is the optimal strategy for this hand, with an expected value of: 0.824 times your bet.)

There are nearly 2.6 million unique poker hands (assuming 5 cards from a 52 card deck). To calculate the long-term expected value of playing a particular video poker payout table (when playing optimally), find the mean expected value of each of these hands. `all_hands_analysis.py` is a wrapper script for saving these expected values for each possible hand.

The table for "9-6 Jacks or Better", which is the original standard for video poker is as follows:

```
 Hand | Multiplier
------+-------
Royal Flush | 800
Straight Flush | 50
Four of a Kind | 25
Full House | 9
Flush | 6
Straight | 4
Three of a Kind | 3
Two Pair | 2
Pair J, Q, K, or A | 1
```
Note: This table includes a bonus for a Royal Flush that is typically available when your bet size is set to "Max coins" (usually 5x the minimum bet). Also, video poker machines typically pay nothing for pairs of twos through tens.

Running `all_hands_analysis.py` with the above payout table and taking the mean of the expected values results in: 0.99544. This is consistent with published expectations, such as those available at [Wizard of Odds](https://wizardofodds.com/games/video-poker/).

Another variant where I have calculated strategies and expected values is known as "Aces and Eights". For the payout table below, optimal long-term play has an expected value of: 0.99782, again consistent with published expectations.

```
 Hand | Multiplier
------+-------
Royal Flush | 800
Straight Flush | 50
Four As, or 8s | 80
Four 7s | 50
Other Four of a Kind | 25
Full House | 8
Flush | 5
Straight | 4
Three of a Kind | 3
Two Pair | 2
Pair J, Q, K, or A | 1
```
