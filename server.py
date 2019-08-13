#!/usr/bin/env python
from __future__ import print_function, absolute_import, division
import os
import ast
from flask import Flask, render_template, request, make_response
from scrabble import make_board,top_moves,read_dictionary
from scorer import LETTER_VALUES
from cli import board_rows

app = Flask(__name__)
PATH = os.path.dirname(__file__)
words = read_dictionary(PATH)

# Hacky mutable global storage for the current board.
board_holder = [make_board()]


def board_as_html(board, play=()):
  trans = {'2':'dl','3':'tl','@':'dw','#':'tw','_':''}
  pd = dict(play)
  clickable = not play
  is_tile = lambda r,c: board[r][c] not in trans or (r,c) in pd
  board_size = len(board)
  tiles = []
  for r,row in enumerate(board):
    for c,space in enumerate(row):
      pos = (r,c)
      css_classes = ['space_%d_%d' % pos, 'space']
      letter, value = '', 0
      if pos in pd:
        css_classes.append('recent')
        letter = pd[pos]
      if space in trans:
        css_classes.append(trans[space])
      else:
        letter = space
      mergers = []
      if letter:
        value = LETTER_VALUES.get(letter, 0)
        if r > 0 and is_tile(r-1,c):
          mergers.append('mt')
        if r+1 < board_size and is_tile(r+1,c):
          mergers.append('mb')
        if c > 0 and is_tile(r,c-1):
          mergers.append('ml')
        if c+1 < board_size and is_tile(r,c+1):
          mergers.append('mr')
        if mergers == ['mt','mb','ml','mr']:
          mergers = ['mf']
        if r > 0 and c > 0 and is_tile(r-1,c-1):
          mergers.append('mtl')
        if r > 0 and c+1 < board_size and is_tile(r-1,c+1):
          mergers.append('mtr')
        if r+1 < board_size and c > 0 and is_tile(r+1,c-1):
          mergers.append('mbl')
        if r+1 < board_size and c+1 < board_size and is_tile(r+1,c+1):
          mergers.append('mbr')
      tclass = ' '.join(css_classes + mergers)
      tiles.append(render_template('tile.html', letter=letter,
                                   tile_class=tclass, r=r, c=c, value=value,
                                   clickable=clickable))
  return render_template('board.html', tiles=tiles, size=board_size)


@app.route('/', methods=['GET', 'POST'])
def main_page():
  def render(hand, board, moves):
    return render_template('index.html', hand=hand, board=board, moves=moves,
                           board_as_html=board_as_html)

  def GET():
    moves = None

    if 'play' in request.args:
      play = ast.literal_eval(request.args['play'])
      board = board_holder[0]
      for (r,c),x in play:
        board[r][c] = x.upper()

    if request.args.get('reset', False):
      board_holder[0] = make_board()

    if 'hand' in request.args:
      hand = request.args['hand'].upper()
      moves = top_moves(board_holder[0], words, hand)

    return render(request.args.get('hand', ''), board_holder[0], moves)

  def POST():
    try:
      board_holder[0] = make_board(request.files['board'])
    except ValueError as e:
      print('Failed to make the board:')
      print(e)
    return render('', board_holder[0], None)

  if request.method == 'POST':
    return POST()
  return GET()


@app.route('/tile_click')
def tile_clicker():
  board = board_holder[0]
  r = int(request.args['r'])
  c = int(request.args['c'])
  board[r][c] = request.args['letter'].upper()
  return 'OK'


@app.route('/active.board')
def board_downloader():
  resp = make_response('\n'.join(board_rows(board_holder[0], colors=False)))
  resp.headers['Content-type'] = 'test/ascii'
  return resp
