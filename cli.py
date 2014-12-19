#!/usr/bin/env python
import os
from copy import deepcopy
from itertools import izip_longest
from optparse import OptionParser
from scrabble import make_board,top_moves,read_dictionary


def board_rows(board, play=None):
  if play:
    b = deepcopy(board)
    for (r,c),x in play:
      b[r][c] = x.lower()
    return board_rows(b)
  return [''.join(row) for row in board]


def print_blocks(blocks, num_cols=4):
  slices = [blocks[start::num_cols] for start in xrange(num_cols)]
  for bs in izip_longest(*slices):
    for rs in zip(*filter(None, bs)):
      print ' | '.join(rs)
    print ''


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
  blocks = []
  for score, words, play in top_moves(board, word_list, hand, opts.num_plays):
    header = ('%d %s' % (score, ', '.join(words))).center(15)
    # TODO: add padding when len(header) > 15
    blocks.append([header] + board_rows(board, play))
  print_blocks(blocks)

if __name__ == '__main__':
  main()
