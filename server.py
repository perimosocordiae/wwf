#!/usr/bin/env python
import web
import os
import ast
from scrabble import make_board,top_moves,read_dictionary,BOARD_SIZE
from scorer import LETTER_VALUES
from cli import board_rows

PATH = os.path.dirname(__file__)
board_render = web.template.frender(PATH+'/static/board.html')
tile_render = web.template.frender(PATH+'/static/tile.html')


def board_as_html(board, play=()):
  trans = {'2':'dl','3':'tl','@':'dw','#':'tw','_':''}
  pd = dict(play)
  is_tile = lambda r,c: board[r][c] not in trans or (r,c) in pd
  tiles = []
  for r,row in enumerate(board):
    for c,space in enumerate(row):
      letter,recent,stype,value = '','','',0
      if (r,c) in pd:
        recent = 'recent'
        letter = pd[(r,c)]
      if space in trans:
        stype = trans[space]
      else:
        letter = space
      mergers = []
      if letter:
        value = LETTER_VALUES.get(letter, 0)
        if r>0 and is_tile(r-1,c):
          mergers.append('mt')
        if r+1<BOARD_SIZE and is_tile(r+1,c):
          mergers.append('mb')
        if c>0 and is_tile(r,c-1):
          mergers.append('ml')
        if c+1<BOARD_SIZE and is_tile(r,c+1):
          mergers.append('mr')
        if mergers == ['mt','mb','ml','mr']:
          mergers = ['mf']
        if r>0 and c>0 and is_tile(r-1,c-1):
          mergers.append('mtl')
        if r>0 and c+1<BOARD_SIZE and is_tile(r-1,c+1):
          mergers.append('mtr')
        if r+1<BOARD_SIZE and c>0 and is_tile(r+1,c-1):
          mergers.append('mbl')
        if r+1<BOARD_SIZE and c+1<BOARD_SIZE and is_tile(r+1,c+1):
          mergers.append('mbr')
      tiles.append(tile_render(letter,recent,stype,' '.join(mergers),r,c,value))
  return board_render(tiles)

words = read_dictionary(PATH)
render = web.template.frender(PATH+'/static/template.html',
                              globals={'board_as_html':board_as_html})
# Hacky mutable global storage for the current board.
board_holder = [make_board()]


class WWF(object):
  def GET(self):
    args = web.input(html='',hand='',reset=False, play='')
    moves = None

    if args.play:
      play = ast.literal_eval(args.play)
      board = board_holder[0]
      for (r,c),x in play:
        board[r][c] = x.upper()

    if args.reset:
      board_holder[0] = make_board()

    if args.hand:
      moves = top_moves(board_holder[0],words,args.hand.upper())

    return render(args.hand, board_holder[0], moves)

  def POST(self):
    data = web.input(board={})
    board_holder[0] = make_board(data['board'].file)
    return render('', board_holder[0], None)


class TileClicker(object):
  def GET(self):
    args = web.input(r='', c='', letter='')
    r,c = int(args.r), int(args.c)
    board = board_holder[0]
    board[r][c] = args.letter.encode('ascii').upper()


class BoardDownloader(object):
  def GET(self):
    web.header('Content-type', 'test/ascii')
    return '\n'.join(board_rows(board_holder[0], colors=False))


if __name__ == '__main__':
  urls = (
      '/', 'WWF',
      '/tile_click', 'TileClicker',
      '/active.board', 'BoardDownloader'
  )
  app = web.application(urls, globals())
  app.run()
