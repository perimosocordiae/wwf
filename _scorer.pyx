# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
__all__ = ['word_to_string', 'score_play', 'all_words']

cdef:
  int BINGO_BONUS = 35
  int BOARD_SIZE = 15
  int* LETTER_VALUES = [
      1, 4, 4, 2, 1, 4, 3, 3, 1, 10, 5, 2, 4,  # A - M
      2, 1, 4, 10, 1, 1, 1, 2, 5, 4, 8, 3, 10  # N - Z
  ]

cdef class HorizWord:
  cdef char[16] letters
  cdef int r_idx
  cdef int[15] c_idxs
  cdef int length

  cdef int score(self, list board):
    cdef char* space
    cdef char* letters = self.letters
    cdef int base_val, i, r = self.r_idx, s = 0, mult = 1
    cdef list board_row = board[r]
    cdef int* c_idxs = self.c_idxs
    for i in range(self.length):
      base_val = letter_value(letters[i])
      space = board_row[c_idxs[i]]
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

cdef class VertWord:
  cdef char[16] letters
  cdef int[15] r_idxs
  cdef int c_idx
  cdef int length

  cdef int score(self, list board):
    cdef char* space
    cdef char* letters = self.letters
    cdef int base_val, i, c = self.c_idx, s = 0, mult = 1
    cdef int* r_idxs = self.r_idxs
    for i in range(self.length):
      base_val = letter_value(letters[i])
      space = board[r_idxs[i]][c]
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

ctypedef fused Word:
  HorizWord
  VertWord

cpdef bytes word_to_string(Word word):
  return word.letters

cdef int letter_value(char x):
  if x == '.':
    return 0
  return LETTER_VALUES[x - 65]


cdef HorizWord _find_horiz(list board, dict playdict, int r, int c):
  cdef int ci = c
  cdef bytes tmp
  cdef char space
  while ci > 0:
    tmp = board[r][ci-1]
    space = (<char*>tmp)[0]
    if space >= 'A' and space <= 'Z':
      ci -= 1
    else:
      break
  if ci > 0 and (r,ci-1) in playdict:
    return
  cdef HorizWord w = HorizWord()
  cdef int i = 0
  while ci < BOARD_SIZE:
    tmp = board[r][ci]
    space = (<char*>tmp)[0]
    if space >= 'A' and space <= 'Z':
      w.letters[i] = space
      w.c_idxs[i] = ci
    elif (r,ci) in playdict:
      tmp = playdict[(r,ci)]
      space = (<char*>tmp)[0]
      w.letters[i] = space
      w.c_idxs[i] = ci
    else:
      break
    ci += 1
    i += 1
  if i >= 2:
    w.r_idx = r
    w.length = i
    return w


cdef VertWord _find_vert(list board, dict playdict, int r, int c):
  cdef int ri = r
  cdef bytes tmp
  cdef char space
  while ri > 0:
    tmp = board[ri-1][c]
    space = (<char*>tmp)[0]
    if space >= 'A' and space <= 'Z':
      ri -= 1
    else:
      break
  if ri > 0 and (ri-1,c) in playdict:
    return
  cdef VertWord w = VertWord()
  cdef int i = 0
  while ri < BOARD_SIZE:
    tmp = board[ri][c]
    space = (<char*>tmp)[0]
    if space >= 'A' and space <= 'Z':
      w.letters[i] = space
      w.r_idxs[i] = ri
    elif (ri,c) in playdict:
      tmp = playdict[(ri,c)]
      space = (<char*>tmp)[0]
      w.letters[i] = space
      w.r_idxs[i] = ri
    else:
      break
    ri += 1
    i += 1
  if i >= 2:
    w.c_idx = c
    w.length = i
    return w


def all_words(list board, play):
  cdef HorizWord hword
  cdef VertWord vword
  cdef dict playdict = dict(play)
  cdef int r, c
  for (r,c),_ in play:
    hword = _find_horiz(board,playdict,r,c)
    if hword is not None:
      yield hword
    vword = _find_vert(board,playdict,r,c)
    if vword is not None:
      yield vword


cpdef int score_play(list board, set words, play):
  cdef int score = 0, r, c
  cdef HorizWord hword
  cdef VertWord vword
  cdef dict playdict = dict(play)
  for (r,c),_ in play:
    hword = _find_horiz(board,playdict,r,c)
    if hword is not None:
      if word_to_string(hword) not in words:
        return 0
      score += hword.score(board)
    vword = _find_vert(board,playdict,r,c)
    if vword is not None:
      if word_to_string(vword) not in words:
        return 0
      score += vword.score(board)
  if len(play) == 7:
    score += BINGO_BONUS
  return score
