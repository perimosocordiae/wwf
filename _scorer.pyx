# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
from cython.view cimport array as cvarray

__all__ = ['Scorer', 'all_words']

cdef:
  int BINGO_BONUS = 35
  int* LETTER_VALUES = [
      1, 4, 4, 2, 1, 4, 3, 3, 1, 10, 5, 2, 4,  # A - M
      2, 1, 4, 10, 1, 1, 1, 2, 5, 4, 8, 3, 10  # N - Z
  ]

cdef class Scorer:
  cdef char[:,::1] board
  cdef dict wordlist
  cdef int[27] hand_ct  # holds counts for each letter + wild in the hand

  def __init__(self, list board, set wordlist, bytes hand):
    cdef int i, j
    cdef list row
    cdef bytes space, w
    cdef char* hand_ptr
    cdef int board_size = len(board)
    self.board = cvarray(shape=(board_size, board_size), itemsize=sizeof(char),
                         format='c')
    # parse the board
    for i in range(board_size):
      row = board[i]
      for j in range(board_size):
        space = row[j]
        self.board[i,j] = (<char*>space)[0]
    # group into subsets, by word length
    self.wordlist = dict()
    for w in wordlist:
      i = len(w)
      if i in self.wordlist:
        self.wordlist[i].add(w)
      else:
        self.wordlist[i] = set([w])
    # count occurrences of each letter
    hand_ptr = hand
    for i in range(27):
      self.hand_ct[i] = 0
    for i in range(len(hand)):
      if hand_ptr[i] == '.':
        self.hand_ct[26] += 1
      else:
        self.hand_ct[hand_ptr[i]-65] += 1


  cpdef int score_play(self, play):
    cdef int score = 0, r, c
    cdef HorizWord hword
    cdef VertWord vword
    cdef dict playdict = dict(play)
    for (r,c),_ in play:
      hword = _find_horiz(self.board,playdict,r,c)
      if hword is not None:
        if hword.letters.upper() not in self.wordlist[hword.length]:
          return 0
        score += hword.score(self.board)
      vword = _find_vert(self.board,playdict,r,c)
      if vword is not None:
        if vword.letters.upper() not in self.wordlist[vword.length]:
          return 0
        score += vword.score(self.board)
    if len(play) == 7:
      score += BINGO_BONUS
    return score

  cpdef char is_playable(self, play_loc):
    cdef int r, c
    cdef HorizWord hword
    cdef VertWord vword
    cdef dict playdict = dict(zip(play_loc, '.......'))
    for (r,c) in play_loc:
      hword = _find_horiz(self.board,playdict,r,c)
      if (hword is not None and not _word_playable(hword.letters, hword.length,
                                                   self.wordlist[hword.length],
                                                   self.hand_ct)):
        return False
      vword = _find_vert(self.board,playdict,r,c)
      if (vword is not None and not _word_playable(vword.letters, vword.length,
                                                   self.wordlist[vword.length],
                                                   self.hand_ct)):
        return False
    return True


cdef char _word_playable(char* word_tpl, int word_len, set wordlist, int* hand_ct):
  cdef bytes word
  cdef char* x_ptr
  cdef int i, j
  cdef char w, x
  for word in wordlist:
    x_ptr = word
    for i in range(word_len):
      w = word_tpl[i]
      x = x_ptr[i]
      if w == x:
        continue
      if w == '.':
        # Just check if the hand includes this letter (or any wilds)
        if hand_ct[x - 65] == 0 and hand_ct[26] == 0:
          break
      else:
        break
    else:
      return True
  return False


cdef class HorizWord:
  cdef char[16] letters
  cdef int r_idx
  cdef int[15] c_idxs
  cdef int length

  cdef int score(self, char[:,::1] board):
    cdef char space
    cdef char* letters = self.letters
    cdef int base_val, i, r = self.r_idx, s = 0, mult = 1
    cdef int* c_idxs = self.c_idxs
    for i in range(self.length):
      base_val = letter_value(letters[i])
      space = board[r, c_idxs[i]]
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

cdef class VertWord:
  cdef char[16] letters
  cdef int[15] r_idxs
  cdef int c_idx
  cdef int length

  cdef int score(self, char[:,::1] board):
    cdef char space
    cdef char* letters = self.letters
    cdef int base_val, i, c = self.c_idx, s = 0, mult = 1
    cdef int* r_idxs = self.r_idxs
    for i in range(self.length):
      base_val = letter_value(letters[i])
      space = board[r_idxs[i], c]
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


cdef inline int letter_value(char x):
  if x >= 97:
    # Wilds are represented as lowercase letters
    return 0
  return LETTER_VALUES[x - 65]


cdef HorizWord _find_horiz(char[:,::1] board, dict playdict, int r, int c):
  cdef int ci = c
  cdef int board_size = board.shape[0]
  cdef char space
  while ci > 0:
    space = board[r, ci-1]
    if space >= 'A' and space <= 'Z':
      ci -= 1
    else:
      break
  if ci > 0 and (r,ci-1) in playdict:
    return
  cdef HorizWord w = HorizWord()
  cdef int i = 0
  cdef bytes tmp
  while ci < board_size:
    space = board[r, ci]
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


cdef VertWord _find_vert(char[:,::1] board, dict playdict, int r, int c):
  cdef int ri = r
  cdef int board_size = board.shape[0]
  cdef char space
  while ri > 0:
    space = board[ri-1, c]
    if space >= 'A' and space <= 'Z':
      ri -= 1
    else:
      break
  if ri > 0 and (ri-1,c) in playdict:
    return
  cdef VertWord w = VertWord()
  cdef int i = 0
  cdef bytes tmp
  while ri < board_size:
    space = board[ri, c]
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


cpdef list all_words(list board, play):
  cdef int board_size = len(board)
  cdef char[:,::1] _board = cvarray(shape=(board_size, board_size),
                                    itemsize=sizeof(char), format='c')
  cdef int i, j
  cdef list row
  cdef bytes space
  for i in range(board_size):
    row = board[i]
    for j in range(board_size):
      space = row[j]
      _board[i, j] = (<char*>space)[0]

  cdef HorizWord hword
  cdef VertWord vword
  cdef dict playdict = dict(play)
  cdef int r, c
  cdef list ret = []
  for (r,c),_ in play:
    hword = _find_horiz(_board,playdict,r,c)
    if hword is not None:
      ret.append(hword.letters)
    vword = _find_vert(_board,playdict,r,c)
    if vword is not None:
      ret.append(vword.letters)
  return ret
