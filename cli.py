#!/usr/bin/env python
import os
from copy import deepcopy
from optparse import OptionParser
from scrabble import make_board,top_moves,read_dictionary


def show_board(board, play=None):
  if not play:
    for row in board:
      print ''.join(row)
  else:
    b = deepcopy(board)
    for x,r,c in play:
      b[r][c] = x.lower()
    show_board(b)


def main():
  op = OptionParser(usage='%prog [-n 20] boardfile hand')
  op.add_option('-n', '--num-plays', type=int, default=20,
                help='Number of possible plays to display')
  opts, args = op.parse_args()
  if len(args) != 2:
    op.error('Must provide boardfile and hand as arguments')
  board = make_board(open(args[0]))
  hand = args[1].upper()
  if (len(hand) < 1 or len(hand) > 7 or
      not all(x.isalpha() or x == '.' for x in hand)):
    op.error('Invalid hand: must be 1 to 7 letters or blanks (.)')
  word_list = read_dictionary(os.path.dirname(__file__))
  for score, words, play in top_moves(board, word_list, hand, opts.num_plays):
    print score, ', '.join(words)
    show_board(board, play)
    print ''

if __name__ == '__main__':
  main()
