from os.path import join as pjoin
from itertools import combinations,product,chain,permutations
from heapq import nlargest
from collections import defaultdict
import time

WORDS_FILE = 'words.txt'
BOARD_SIZE = 15
SPECIALS = {
  '2':[(2,1),(4,2),(6,4)], # double letter
  '3':[(6,0),(3,3),(5,5)], # triple letter
  '@':[(5,1),(7,3)],       # double word
  '#':[(3,0)],             # triple word
}
BINGO_BONUS = 35
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
LETTER_VALUES = dict((x,1) for x in ALPHABET)
for v,ltrs in ((0,'.'),(2,'DLNU'),(3,'GHY'),(4,'BCFMPW'),(5,'KV'),(8,'X'),(10,'JQZ')):
  for l in ltrs: LETTER_VALUES[l] = v
WILDS = set()

def make_board(fh):
  board = [ ['_' for _ in xrange(BOARD_SIZE)] for _ in xrange(BOARD_SIZE)]
  mid = BOARD_SIZE//2
  #board[mid][mid] = '*'
  for bonus,coords in SPECIALS.iteritems():
    for i,j in coords:
      i2 = mid-i+mid
      j2 = mid-j+mid
      board[i][j] = board[j][i] = board[i2][j] = board[j][i2] = \
      board[i][j2] = board[j2][i] = board[i2][j2] = board[j2][i2] = bonus
  if fh:
    data = [x.strip('\n') for x in fh]
    assert len(data) == BOARD_SIZE and len(data[0]) == BOARD_SIZE
    for r,row in enumerate(data):
      for c,letter in enumerate(row):
        l = letter.upper()
        if 'A' <= l <= 'Z':
          board[r][c] = l
  return board

def word_to_string(word):
  return ''.join(x for x,r,c in word).upper()

def base_value(x,r,c):
 return LETTER_VALUES[x] if x in LETTER_VALUES else 0

def score_word(board,word):
  s = 0
  mult = 1
  for x,r,c in word:
    base_val = base_value(x,r,c)
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
    if ci > 0 and (r,ci-1) in playdict: return
    word = []
    while ci < BOARD_SIZE:
      if is_letter(board[r][ci]):
        word.append((board[r][ci],r,ci))
      elif (r,ci) in playdict:
        word.append((playdict[(r,ci)],r,ci))
      else: break
      ci += 1
    if len(word) >= 2:
      yield word
  def find_vert():
    ri = r
    while ri > 0 and is_letter(board[ri-1][c]):
      ri -= 1
    if ri > 0 and (ri-1,c) in playdict: return
    word = []
    while ri < BOARD_SIZE:
      if is_letter(board[ri][c]):
        word.append((board[ri][c],ri,c))
      elif (ri,c) in playdict:
        word.append((playdict[(ri,c)],ri,c))
      else: break
      ri += 1
    if len(word) >= 2:
      yield word
  return chain(find_horiz(),find_vert())

def all_words(board,play):
  pd = dict(((r,c),x) for x,r,c in play)
  return chain.from_iterable(find_words(board,pd,r,c) for x,r,c in play)

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
    if r > 0 and is_letter(board[r-1][c]): return True
    if c > 0 and is_letter(board[r][c-1]): return True
    if r < BOARD_SIZE-1 and is_letter(board[r+1][c]): return True
    if c < BOARD_SIZE-1 and is_letter(board[r][c+1]): return True
    # also check if this is the first word
    if r == BOARD_SIZE//2 and c == BOARD_SIZE//2: return True
  return False

def powerset_nonempty(seq):
  s = list(seq)
  return chain.from_iterable(combinations(s, r) for r in xrange(1,len(s)+1))

def letter_combos(hand):
  lcs = defaultdict(set)
  if '.' not in hand:
    for combo_types in powerset_nonempty(hand):
      for combo in permutations(combo_types):
        lcs[len(combo)].add(combo)
  else:
    hands = (hand.replace('.',x,1) for x in ALPHABET.lower())
    for h in hands:
      for l,cs in letter_combos(h).iteritems():
        lcs[l].update(cs)
  return lcs

def valid_plays(board):
  # precompute possible play locations
  valid_plays = dict((n,[]) for n in xrange(1,8))
  for r,c in product(xrange(BOARD_SIZE),xrange(BOARD_SIZE)):
    if is_letter(board[r][c]): continue
    h_play,v_play = [],[]
    ri,ci = r,c
    for _ in xrange(7):
      h_play.append((r,ci))
      if next_to_existing(board,h_play):
        valid_plays[len(h_play)].append(h_play)
      ci += 1
      while ci < BOARD_SIZE and is_letter(board[r][ci]): ci += 1
      if ci == BOARD_SIZE: break
    for _ in xrange(7):
      v_play.append((ri,c))   # bug here, modifying v_play after appending it
      if next_to_existing(board,v_play):
        valid_plays[len(v_play)].append(v_play)
      ri += 1
      while ri < BOARD_SIZE and is_letter(board[ri][c]): ri += 1
      if ri == BOARD_SIZE: break
  return valid_plays

def valid_moves(valid_plays,hand):
  valid_moves = set()
  lcs = letter_combos(hand)
  print "got letter combos:", dict((n,len(lcs[n])) for n in lcs.iterkeys())
  for i in lcs.iterkeys():
    for letters,play in product(lcs[i],valid_plays[i]):
      move = tuple((l,r,c) for l,(r,c) in zip(letters,play))
      valid_moves.add(move)
  return valid_moves

def positive_scoring_moves(board,words,hand):
  t0 = time.time()
  plays = valid_plays(board)
  t1 = time.time()
  print "%f secs, valid play counts:" % (t1-t0), dict((n,len(plays[n])) for n in plays.iterkeys())
  moves = valid_moves(plays,hand)
  t2 = time.time()
  print "%f secs, valid move count:" % (t2-t1), len(moves)
  #TODO: reduce wordset size to only words containing at least one from the hand?
  for move in moves:
    score = score_play(board,words,move)
    if score > 0:
      yield score,move
  t3 = time.time()
  print "%f secs, done" % (t3-t2)

def read_dictionary(path=''):
  return set(x.strip().upper() for x in open(pjoin(path,WORDS_FILE)))

def top_moves(board,wordlist,hand,n=20):
  assert 1 <= len(hand) <= 7
  moves = positive_scoring_moves(board,wordlist,hand.upper())
  for score,play in nlargest(n,moves):
    yield score, map(word_to_string,all_words(board,play)), play

