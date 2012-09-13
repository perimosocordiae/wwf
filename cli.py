#!/usr/bin/env python
import sys,os
from copy import deepcopy
from scrabble import make_board,top_moves,read_dictionary

def show_board(board,play=None):
  if not play:
    for row in board:
      print ''.join(row)
  else:
    b = deepcopy(board)
    for x,r,c in play:
      b[r][c] = x.lower()
    show_board(b)

if __name__ == '__main__':
  assert len(sys.argv) >= 3, 'Usage: ./scrabble.py boardfile hand [num_moves]'
  board = make_board(open(sys.argv[1]))
  hand = sys.argv[2].upper()
  path = os.path.dirname(sys.argv[0])
  num_moves = int(sys.argv[3]) if len(sys.argv) > 3 else 20
  for score,words,play in top_moves(board,read_dictionary(path),hand,num_moves):
    print score, ', '.join(words)
    show_board(board,play)
    print ''
