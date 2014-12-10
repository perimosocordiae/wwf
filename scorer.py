from itertools import chain
import string

__all__ = ['Scorer', 'all_words']
BINGO_BONUS = 35
LETTER_VALUES = dict((x,1) for x in string.uppercase)
for v,ltrs in ((0, '.'), (2, 'DLNU'), (3, 'GHY'), (4, 'BCFMPW'),
               (5, 'KV'), (8, 'X'), (10, 'JQZ')):
  for l in ltrs:
    LETTER_VALUES[l] = v


class Scorer(object):
  def __init__(self, board, wordlist):
    self.board = board
    self.wordlist = wordlist

  def score_play(self, play):
    score = 0
    for w in all_words_raw(self.board, play):
      if word_to_string(w) not in self.wordlist:
        return 0
      score += self._score_word(w)
    if len(play) == 7:
      score += BINGO_BONUS
    return score

  def _score_word(self, word):
    s = 0
    mult = 1
    for x,r,c in word:
      base_val = LETTER_VALUES.get(x, 0)
      space = self.board[r][c]
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


def all_words(board, play):
  return map(word_to_string, all_words_raw(board, play))


def all_words_raw(board, play):
  pd = dict(play)
  words = (find_words(board,pd,r,c) for (r,c),x in play)
  return chain.from_iterable(words)


def word_to_string(word):
  return ''.join(x for x,r,c in word).upper()


def find_words(board,playdict,r,c):
  board_size = len(board)

  #TODO: DRY this up
  def find_horiz():
    ci = c
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

  def find_vert():
    ri = r
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
  return chain(find_horiz(),find_vert())
