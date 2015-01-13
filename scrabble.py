from collections import defaultdict
from heapq import nlargest
from os.path import join as pjoin
import itertools
import string
import time

try:
  import pyximport
  pyximport.install()
  from _scorer import Scorer, all_words
  print 'Using Cython (fast) scorer'
except ImportError:
  from scorer import Scorer, all_words
  print 'Using Python (slow) scorer'

WORDS_FILE = 'words.txt'
BOARD_SIZE = 15


def make_board(fh=None):
  # 2 = double letter, 3 = triple letter
  # @ = double word, # = triple word
  board = map(list, [
      "___#__3_3__#___",
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
      "___#__3_3__#___"])
  if fh:
    data = [x.strip('\n').upper() for x in fh]
    assert len(data) == BOARD_SIZE and len(data[0]) == BOARD_SIZE
    for r,row in enumerate(data):
      for c,letter in enumerate(row):
        if 'A' <= letter <= 'Z':
          board[r][c] = letter
  return board


def next_to_existing(board,play):
  mid = BOARD_SIZE//2
  for r,c in play:
    if r > 0 and board[r-1][c].isalpha():
      return True
    if c > 0 and board[r][c-1].isalpha():
      return True
    if r < BOARD_SIZE-1 and board[r+1][c].isalpha():
      return True
    if c < BOARD_SIZE-1 and board[r][c+1].isalpha():
      return True
    # also check if this is the first word
    if r == mid and c == mid:
      return True
  return False


def powerset_nonempty(seq):
  s = list(seq)
  return itertools.chain.from_iterable(itertools.combinations(s, r)
                                       for r in xrange(1,len(s)+1))


def letter_combos(hand):
  lcs = defaultdict(set)
  if '.' not in hand:
    _letter_combos(hand, lcs)
    return lcs
  h = hand.replace('.', '')
  # Make all possible hands by replacing wilds with *lowercase* letters.
  # The lowercase is what lets downstream scorers know that the letter is wild.
  for wilds in itertools.combinations_with_replacement(string.lowercase,
                                                       hand.count('.')):
    _letter_combos(h + ''.join(wilds), lcs)
  return lcs


def _letter_combos(hand, lcs):
  # Assumes no wildcards, updates lcs in place!
  for combo_types in powerset_nonempty(hand):
    lcs[len(combo_types)].update(itertools.permutations(combo_types))


def valid_plays(board, hand_length):
  # precompute possible play locations
  valid_plays = dict((n,[]) for n in xrange(1,hand_length+1))
  for r,c in itertools.product(xrange(BOARD_SIZE),xrange(BOARD_SIZE)):
    if board[r][c].isalpha():
      continue
    h_play,v_play = [],[]
    ri,ci = r,c
    for _ in xrange(hand_length):
      h_play.append((r,ci))
      if next_to_existing(board,h_play):
        valid_plays[len(h_play)].append(tuple(h_play))
      ci += 1
      while ci < BOARD_SIZE and board[r][ci].isalpha():
        ci += 1
      if ci == BOARD_SIZE:
        break
    for _ in xrange(hand_length):
      v_play.append((ri,c))
      # Avoid double-adding length-1 plays here.
      if len(v_play) > 1 and next_to_existing(board,v_play):
        valid_plays[len(v_play)].append(tuple(v_play))
      ri += 1
      while ri < BOARD_SIZE and board[ri][c].isalpha():
        ri += 1
      if ri == BOARD_SIZE:
        break
  return valid_plays


def valid_moves(valid_plays, lcs):
  for i,combos in lcs.iteritems():
    for letters,play in itertools.product(combos, valid_plays[i]):
      yield zip(play,letters)


def shrink_wordlist(wordlist, hand):
  # reduce wordlist size to only words containing at least one from the hand
  return set(w for w in wordlist if any(h in w for h in hand))


def positive_scoring_moves(board,wordlist,hand,prune_words):
  if prune_words and '.' not in hand:
    pre_size = len(wordlist)
    tic = time.time()
    wordlist = shrink_wordlist(wordlist, hand)
    toc = time.time()
    print '%f secs, wordlist shrunk from %d to %d' % (
        toc-tic, pre_size, len(wordlist))

  tic = time.time()
  plays = valid_plays(board, len(hand))
  toc = time.time()
  play_counts = dict((n,len(p)) for n,p in plays.iteritems())
  print "%f secs, valid play counts: %s" % (toc-tic, play_counts)

  scorer = Scorer(board, wordlist, hand)

  tic = time.time()
  for i,pp in plays.iteritems():
    pp[:] = filter(scorer.is_playable, pp)
  toc = time.time()
  play_counts = dict((n,len(p)) for n,p in plays.iteritems())
  print "%f secs, valid play counts: %s" % (toc-tic, play_counts)

  tic = time.time()
  lcs = letter_combos(hand)
  toc = time.time()
  lc_counts = dict((n,len(lc)) for n,lc in lcs.iteritems())
  print "%f secs, letter combos: %s" % (toc-tic, lc_counts)

  tic = time.time()
  num_moves = 0
  for move in valid_moves(plays, lcs):
    num_moves += 1
    score = scorer.score_play(move)
    if score > 0:
      yield score,move
  toc = time.time()
  print "%f secs, scored %d moves" % (toc-tic, num_moves)


def read_dictionary(path=''):
  return set(x.strip().upper() for x in open(pjoin(path,WORDS_FILE)))


def top_moves(board, wordlist, hand, n=20, prune_words=True):
  assert 1 <= len(hand) <= 7
  hand = hand.encode('ascii').upper()
  moves = positive_scoring_moves(board,wordlist,hand,prune_words)
  for score,play in nlargest(n,moves):
    yield score, all_words(board, play), play
