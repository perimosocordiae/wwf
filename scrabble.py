from collections import defaultdict
from heapq import nlargest
from os.path import join as pjoin
import itertools
import time

WORDS_FILE = 'words.txt'
BOARD_SIZE = 15
BINGO_BONUS = 35
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTER_VALUES = dict((x,1) for x in ALPHABET)
for v,ltrs in ((0, '.'), (2, 'DLNU'), (3, 'GHY'), (4, 'BCFMPW'),
               (5, 'KV'), (8, 'X'), (10, 'JQZ')):
  for l in ltrs:
    LETTER_VALUES[l] = v
WILDS = set()


def make_board(fh):
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


def word_to_string(word):
  return ''.join(x for x,r,c in word).upper()


def score_word(board,word):
  s = 0
  mult = 1
  for x,r,c in word:
    base_val = LETTER_VALUES.get(x, 0)
    space = board[r][c]
    s += base_val
    if space == '2':
      s += base_val
    elif space == '3':
      s += 2*base_val
    elif space == '@':
      mult *= 2
    elif space == '#':
      mult *= 3
  return s*mult


def is_letter(x):
  return 'A' <= x <= 'Z' or 'a' <= x <= 'z'


def find_words(board,playdict,r,c):
  #TODO: DRY this up
  def find_horiz():
    ci = c
    while ci > 0 and is_letter(board[r][ci-1]):
      ci -= 1
    if ci > 0 and (r,ci-1) in playdict:
      return
    word = []
    while ci < BOARD_SIZE:
      if is_letter(board[r][ci]):
        word.append((board[r][ci],r,ci))
      elif (r,ci) in playdict:
        word.append((playdict[(r,ci)],r,ci))
      else:
        break
      ci += 1
    if len(word) >= 2:
      yield word

  def find_vert():
    ri = r
    while ri > 0 and is_letter(board[ri-1][c]):
      ri -= 1
    if ri > 0 and (ri-1,c) in playdict:
      return
    word = []
    while ri < BOARD_SIZE:
      if is_letter(board[ri][c]):
        word.append((board[ri][c],ri,c))
      elif (ri,c) in playdict:
        word.append((playdict[(ri,c)],ri,c))
      else:
        break
      ri += 1
    if len(word) >= 2:
      yield word
  return itertools.chain(find_horiz(),find_vert())


def all_words(board,play):
  pd = dict(play)
  words = (find_words(board,pd,r,c) for (r,c),x in play)
  return itertools.chain.from_iterable(words)


def score_play(board,words,play):
  score = 0
  for w in all_words(board,play):
    if word_to_string(w) not in words:
      return 0
    score += score_word(board,w)
  if len(play) == 7:
    score += BINGO_BONUS
  return score


def next_to_existing(board,play):
  for r,c in play:
    if r > 0 and is_letter(board[r-1][c]):
      return True
    if c > 0 and is_letter(board[r][c-1]):
      return True
    if r < BOARD_SIZE-1 and is_letter(board[r+1][c]):
      return True
    if c < BOARD_SIZE-1 and is_letter(board[r][c+1]):
      return True
    # also check if this is the first word
    if r == BOARD_SIZE//2 and c == BOARD_SIZE//2:
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
  for wilds in itertools.combinations_with_replacement(ALPHABET.lower(),
                                                       hand.count('.')):
    _letter_combos(h + ''.join(wilds), lcs)
  return lcs


def _letter_combos(hand, lcs):
  # Assumes no wildcards, updates lcs in place!
  for combo_types in powerset_nonempty(hand):
    lcs[len(combo_types)].update(itertools.permutations(combo_types))


def valid_plays(board):
  # precompute possible play locations
  valid_plays = dict((n,[]) for n in xrange(1,8))
  for r,c in itertools.product(xrange(BOARD_SIZE),xrange(BOARD_SIZE)):
    if is_letter(board[r][c]):
      continue
    h_play,v_play = [],[]
    ri,ci = r,c
    for _ in xrange(7):
      h_play.append((r,ci))
      if next_to_existing(board,h_play):
        valid_plays[len(h_play)].append(tuple(h_play))
      ci += 1
      while ci < BOARD_SIZE and is_letter(board[r][ci]):
        ci += 1
      if ci == BOARD_SIZE:
        break
    for _ in xrange(7):
      v_play.append((ri,c))
      # Avoid double-adding length-1 plays here.
      if len(v_play) > 1 and next_to_existing(board,v_play):
        valid_plays[len(v_play)].append(tuple(v_play))
      ri += 1
      while ri < BOARD_SIZE and is_letter(board[ri][c]):
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


def positive_scoring_moves(board,wordlist,hand):
  if '.' not in hand:
    pre_size = len(wordlist)
    tic = time.time()
    wordlist = shrink_wordlist(wordlist, hand)
    toc = time.time()
    print '%f secs, wordlist shrunk from %d to %d' % (
        toc-tic, pre_size, len(wordlist))

  tic = time.time()
  plays = valid_plays(board)
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
    score = score_play(board, wordlist, move)
    if score > 0:
      yield score,move
  toc = time.time()
  print "%f secs, scored %d moves" % (toc-tic, num_moves)


def read_dictionary(path=''):
  return set(x.strip().upper() for x in open(pjoin(path,WORDS_FILE)))


def top_moves(board,wordlist,hand,n=20):
  assert 1 <= len(hand) <= 7
  moves = positive_scoring_moves(board,wordlist,hand.upper())
  for score,play in nlargest(n,moves):
    yield score, map(word_to_string,all_words(board,play)), play
