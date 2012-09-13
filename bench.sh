#!/bin/sh

board=example.board
letters=abcdefg

#time ./cli.py $board $letters 10 | sed '1,4d' >/tmp/$letters-py 2>/dev/null

pushd haskell
time ./wwf ../$board $letters 10 >/tmp/$letters-hs 2>/dev/null
popd

diff -si /tmp/$letters-py /tmp/$letters-hs

