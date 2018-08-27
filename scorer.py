from __future__ import print_function, absolute_import, division
from itertools import chain
from collections import defaultdict
import string
import re

__all__ = ['Scorer', 'all_words']
BINGO_BONUS = 35
LETTER_VALUES = dict((x,1) for x in string.uppercase)
for v,ltrs in ((2, 'DLNU'), (3, 'GHY'), (4, 'BCFMPW'),
               (5, 'KV'), (8, 'X'), (10, 'JQZ')):
  for l in ltrs:
    LETTER_VALUES[l] = v


class Scorer(object):
  def __init__(self, board, wordlist, hand):
    self.board = board
    # group into subsets, by word length
    self.wordlist = defaultdict(set)
    for w in wordlist:
      self.wordlist[len(w)].add(w)
    self._playable_cache = set()
    # prep the hand regexp
    if '.' in hand:
      self.hand_patt = '[A-Z]'
    else:
      self.hand_patt = '[%s]' % hand

  def score_play(self, play):
    score = 0
    for w in all_words_raw(self.board, play):
      if word_to_string(w) not in self.wordlist[len(w)]:
        return 0
      score += self._score_word(w)
    if len(play) == 7:
      score += BINGO_BONUS
    return score

  def _score_word(self, word):
    s = 0
    mult = 1
    for x,r,c in word:
      # lowercase letters aren't in the dict, so they get a score of zero.
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

  def is_playable(self, play_loc):
    play_tpl = [(loc, b'.') for loc in play_loc]
    for w in all_words_raw(self.board, play_tpl):
      word_tpl = word_to_string(w)
      if word_tpl in self._playable_cache:
        continue
      patt = re.compile(word_tpl.replace('.', self.hand_patt) + '$', re.I)
      for x in self.wordlist[len(w)]:
        if patt.match(x):
          self._playable_cache.add(word_tpl)
          break
      else:  # no valid words were playable
          return False
    return True


def all_words(board, play):
  return map(word_to_string, all_words_raw(board, play))


def all_words_raw(board, play):
  pd = dict(play)
  for (r, c), x in play:
    for word in find_words(board, pd, r, c):
      yield word


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
