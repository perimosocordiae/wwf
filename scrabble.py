from collections import defaultdict
from heapq import nlargest
from os.path import join as pjoin
import itertools
import os
import string
import time

try:
  import pyximport
  pyximport.install()
  from _scorer import Scorer, all_words
  print('Using Cython (fast) scorer')
except ImportError as e:
  from scorer import Scorer, all_words
  print('Using Python (slow) scorer')

WORDS_FILE = 'words.txt'
BOARD_TPLS = {
  # 2 = double letter, 3 = triple letter
  # @ = double word, # = triple word
  11: ["3_#_____#_3",
       "_@___@___@_",
       "#_2_2_2_2_#",
       "___3___3___",
       "__2_____2__",
       "_@_______@_",
       "__2_____2__",
       "___3___3___",
       "#_2_2_2_2_#",
       "_@___@___@_",
       "3_#_____#_3"],
  15: ["___#__3_3__#___",
       "__2__@___@__2__",
       "_2__2_____2__2_",
       "#__3___@___3__#",
       "__2___2_2___2__",
       "_@___3___3___@_",
       "3___2_____2___3",
       "___@_______@___",
       "3___2_____2___3",
       "_@___3___3___@_",
       "__2___2_2___2__",
       "#__3___@___3__#",
       "_2__2_____2__2_",
       "__2__@___@__2__",
       "___#__3_3__#___"],
}


def make_board(fh=None):
  if fh is None:
    data = []
    board_size = 15
  else:
    data = [x.rstrip(os.linesep).upper() for x in fh]
    board_size = len(data)
    if len(data) != len(data[0]) or len(data) not in BOARD_TPLS:
      raise ValueError('Invalid board dimensions: (%d,%d)' % (len(data),
                                                            len(data[0])))
  board = [[bytes(x, 'ascii') for x in row] for row in BOARD_TPLS[board_size]]
  for r,row in enumerate(data):
    for c,letter in enumerate(row):
      if 'A' <= letter <= 'Z':
        board[r][c] = letter.encode('ascii')
  return board


def next_to_existing(board,play):
  board_size = len(board)
  mid = board_size // 2
  for r,c in play:
    if r > 0 and board[r-1][c].isalpha():
      return True
    if c > 0 and board[r][c-1].isalpha():
      return True
    if r < board_size-1 and board[r+1][c].isalpha():
      return True
    if c < board_size-1 and board[r][c+1].isalpha():
      return True
    # also check if this is the first word
    if r == mid and c == mid:
      return True
  return False


def powerset_nonempty(seq):
  s = list(seq)
  return itertools.chain.from_iterable(itertools.combinations(s, r)
                                       for r in range(1,len(s)+1))


def letter_combos(hand):
  lcs = defaultdict(set)
  num_wild = hand.count(b'.')
  if num_wild == 0:
    _letter_combos(hand, lcs)
    return lcs
  h = hand.replace(b'.', b'')
  # Make all possible hands by replacing wilds with *lowercase* letters.
  # The lowercase is what lets downstream scorers know that the letter is wild.
  for wilds in itertools.combinations_with_replacement(string.lowercase,
                                                       num_wild):
    _letter_combos(h + b''.join(wilds), lcs)
  return lcs


def _letter_combos(hand, lcs):
  hand = [bytes([c]) for c in hand]
  # Assumes no wildcards, updates lcs in place!
  for combo_types in powerset_nonempty(hand):
    lcs[len(combo_types)].update(itertools.permutations(combo_types))


def valid_plays(board, hand_length):
  board_size = len(board)
  # precompute possible play locations
  valid_plays = dict((n,[]) for n in range(1,hand_length+1))
  for r,c in itertools.product(range(board_size), range(board_size)):
    if board[r][c].isalpha():
      continue
    h_play,v_play = [],[]
    ri,ci = r,c
    for _ in range(hand_length):
      h_play.append((r,ci))
      if next_to_existing(board,h_play):
        valid_plays[len(h_play)].append(tuple(h_play))
      ci += 1
      while ci < board_size and board[r][ci].isalpha():
        ci += 1
      if ci == board_size:
        break
    for _ in range(hand_length):
      v_play.append((ri,c))
      # Avoid double-adding length-1 plays here.
      if len(v_play) > 1 and next_to_existing(board,v_play):
        valid_plays[len(v_play)].append(tuple(v_play))
      ri += 1
      while ri < board_size and board[ri][c].isalpha():
        ri += 1
      if ri == board_size:
        break
  return valid_plays


def valid_moves(valid_plays, lcs):
  for i,combos in lcs.items():
    for letters,play in itertools.product(combos, valid_plays[i]):
      yield list(zip(play, letters))


def shrink_wordlist(wordlist, hand):
  # reduce wordlist size to only words containing at least one from the hand
  return set(w for w in wordlist if any(h in w for h in hand))


def positive_scoring_moves(board,wordlist,hand,prune_words):
  if prune_words and b'.' not in hand:
    pre_size = len(wordlist)
    tic = time.time()
    wordlist = shrink_wordlist(wordlist, hand)
    toc = time.time()
    print('%f secs, wordlist shrunk from %d to %d' % (
          toc-tic, pre_size, len(wordlist)))

  tic = time.time()
  plays = valid_plays(board, len(hand))
  toc = time.time()
  play_counts = dict((n,len(p)) for n,p in plays.items())
  print('%f secs, valid play counts: %s' % (toc-tic, play_counts))

  scorer = Scorer(board, wordlist, hand)

  tic = time.time()
  for i,pp in plays.items():
    pp[:] = filter(scorer.is_playable, pp)
  toc = time.time()
  play_counts = dict((n,len(p)) for n,p in plays.items())
  print('%f secs, valid play counts: %s' % (toc-tic, play_counts))

  tic = time.time()
  lcs = letter_combos(hand)
  toc = time.time()
  lc_counts = dict((n,len(lc)) for n,lc in lcs.items())
  print('%f secs, letter combos: %s' % (toc-tic, lc_counts))

  tic = time.time()
  num_moves = 0
  for move in valid_moves(plays, lcs):
    num_moves += 1
    score = scorer.score_play(move)
    if score > 0:
      yield score, move
  toc = time.time()
  print('%f secs, scored %d moves' % (toc-tic, num_moves))


def read_dictionary(path=''):
  return set(x.strip().upper() for x in open(pjoin(path,WORDS_FILE), 'rb'))


def top_moves(board, wordlist, hand, n=20, prune_words=True):
  assert 1 <= len(hand) <= 7
  hand = hand.encode('ascii').upper()
  moves = positive_scoring_moves(board,wordlist,hand,prune_words)
  for score,play in nlargest(n,moves):
    yield score, all_words(board, play), play
