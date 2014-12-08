from itertools import chain
import string

__all__ = ['word_to_string', 'score_play', 'all_words']

cdef int BINGO_BONUS = 35
cdef int* LETTER_VALUES = [
    1, 4, 4, 2, 1, 4, 3, 3, 1, 10, 5, 2, 4,  # A - M
    2, 1, 4, 10, 1, 1, 1, 2, 5, 4, 8, 3, 10  # N - Z
]


def word_to_string(word):
  return ''.join(x for x,r,c in word).upper()


cdef int letter_value(bytes x):
  if x == '.':
    return 0
  cdef char* xx = x
  return LETTER_VALUES[xx[0] - 65]


cdef int score_word(board,word):
  cdef int base_val
  cdef char* space
  cdef int s = 0
  cdef int mult = 1
  for x,r,c in word:
    base_val = letter_value(x)
    space = board[r][c]
    s += base_val
    if space[0] == '2':
      s += base_val
    elif space[0] == '3':
      s += 2*base_val
    elif space[0] == '@':
      mult *= 2
    elif space[0] == '#':
      mult *= 3
  return s*mult


#TODO: DRY this up
def _find_horiz(board,playdict,r,c):
  cdef int ci = c
  cdef int board_size = len(board)
  while ci > 0 and board[r][ci-1].isalpha():
    ci -= 1
  if ci > 0 and (r,ci-1) in playdict:
    return
  word = []
  while ci < board_size:
    if board[r][ci].isalpha():
      word.append((board[r][ci],r,ci))
    elif (r,ci) in playdict:
      word.append((playdict[(r,ci)],r,ci))
    else:
      break
    ci += 1
  if len(word) >= 2:
    yield word


def _find_vert(board,playdict,r,c):
  cdef int ri = r
  cdef int board_size = len(board)
  while ri > 0 and board[ri-1][c].isalpha():
    ri -= 1
  if ri > 0 and (ri-1,c) in playdict:
    return
  word = []
  while ri < board_size:
    if board[ri][c].isalpha():
      word.append((board[ri][c],ri,c))
    elif (ri,c) in playdict:
      word.append((playdict[(ri,c)],ri,c))
    else:
      break
    ri += 1
  if len(word) >= 2:
    yield word


def find_words(board,playdict,r,c):
  return chain(_find_horiz(board,playdict,r,c),
               _find_vert(board,playdict,r,c))


def all_words(board,play):
  pd = dict(play)
  words = (find_words(board,pd,r,c) for (r,c),x in play)
  return chain.from_iterable(words)


def score_play(board,words,play):
  cdef int score = 0
  for w in all_words(board,play):
    if word_to_string(w) not in words:
      return 0
    score += score_word(board,w)
  if len(play) == 7:
    score += BINGO_BONUS
  return score
