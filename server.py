#!/usr/bin/env python
import web
import re
import os
from BeautifulSoup import BeautifulSoup as BS
from scrabble import make_board,top_moves,read_dictionary,BOARD_SIZE,base_value

PATH = os.path.dirname(__file__)
board_render = web.template.frender(PATH+'/static/board.html')
tile_render = web.template.frender(PATH+'/static/tile.html')


def parse_letter(soup_letter):
  m = re.search('space_(\d+)_(\d+)',soup_letter['class'])
  if not m:
    return
  c,r = map(int,m.groups())
  letter,value = soup_letter.text[0],int(soup_letter.text[1:])
  if value >= 1:
    letter = letter.upper()
  return letter,r,c


def parse_html(html_blob):
  soup = BS(html_blob)
  letters = (parse_letter(x) for x in soup.findAll('div','space') if x.text)
  hand = (x.find('span','letter') for x in soup.findAll('div','tile'))
  hand = ''.join(x.text.upper() if x else '.' for x in hand)
  board = make_board(None)  # makes an empty board
  for x,r,c in letters:
    board[r][c] = x
  return board,hand


def board_as_html(board, play=()):
  trans = {'2':'dl','3':'tl','@':'dw','#':'tw','_':''}
  pd = dict(((r,c),x) for x,r,c in play)
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
        value = base_value(letter,r,c)
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


class WWF(object):
  def GET(self):
    args = web.input(board='',html='',hand='')
    if args.html:
      board,hand = parse_html(args.html)
    elif args.board and args.hand:
      board = make_board(open(args.board))
      hand = args.hand.upper()
    else:
      return render(args,None,[])
    moves = top_moves(board,words,hand)
    return render(args,board,moves)


if __name__ == '__main__':
  app = web.application(('/','WWF'),globals())
  app.run()
