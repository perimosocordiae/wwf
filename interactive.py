#!/usr/bin/env python
import os
from optparse import OptionParser
from scrabble import make_board,top_moves,read_dictionary
from cli import board_rows, print_blocks


def main():
  op = OptionParser(usage='%prog boardfile')
  opts, args = op.parse_args()
  if len(args) != 1:
    op.error('Must provide boardfile argument')
  word_list = read_dictionary(os.path.dirname(__file__))
  # Keep reading the boardfile, asking for a hand, then suggesting plays.
  while True:
    board = make_board(open(args[0]))
    try:
      hand = ask_for_hand()
      interactive_play(board, word_list, hand, args[0])
    except KeyboardInterrupt:
      print ''
      break


def ask_for_hand():
  while True:
    hand = raw_input('Enter your hand: ').upper()
    if (len(hand) < 1 or len(hand) > 7 or
        not all(x.isalpha() or x == '.' for x in hand)):
      print 'Invalid hand: must be 1 to 7 letters or blanks (.)'
      continue
    return hand


def gen_blocks(board, word_list, hand):
  # Generates an almost-infinite sequences of (block, play) pairs.
  for score, words, play in top_moves(board, word_list, hand, 999,
                                      prune_words=False):
    header = ('%d %s' % (score, ', '.join(words))).center(15)
    block = [header] + board_rows(board, play)
    yield block, play


def interactive_play(board, word_list, hand, board_filename):
  genny = gen_blocks(board, word_list, hand)
  while True:
    # Grab and show four plays.
    chunk, plays = zip(*[next(genny) for _ in xrange(4)])
    print_blocks(chunk, num_cols=4)
    # Ask for which play the user wants.
    print 'Choose a move (1-%d) or leave blank for more choices' % len(chunk)
    resp = raw_input().strip()
    try:
      idx = int(resp) - 1
      assert 0 <= idx < len(chunk)
    except:
      continue
    # User made a valid choice, so write the boardfile and exit.
    choice = plays[idx]
    new_boardfile = '\n'.join(board_rows(board, choice, colors=False))
    with open(board_filename, 'w') as fh:
      print >>fh, new_boardfile
    return
  # TODO: handle this case better. It's unlikely, but it shouldn't error out.
  assert False, 'You looked at all the moves and chose none of them!'


if __name__ == '__main__':
  main()