#WWF#
_A mostly-cheating way to get high scores playing Words With Friends_

##Setup##

    curl http://dotnetperls-controls.googlecode.com/files/enable1.txt >words.txt
    cat extra_words.txt >>words.txt

##Usage##

To test things out, try the simple CLI interface:

    $ ./cli.py boards/example.board abcdefg
    Using Cython (fast) scorer
    0.142285 secs, wordlist shrunk from 172822 to 168006
    0.016330 secs, valid play counts: {1: 23, 2: 61, 3: 74, 4: 85, 5: 94, 6: 99, 7: 96}
    0.014657 secs, letter combos: {1: 7, 2: 42, 3: 210, 4: 840, 5: 2520, 6: 5040, 7: 5040}
    3.417782 secs, scored 1309343 moves
    60 DECAF, OD, WE
    ...pairs of scores and boards....

For actual use, try the more convenient interactive mode.
Set up the boardfile to match your game, then run:

    $ ./interactive.py boards/mygame.board

This will prompt you for your hand, then suggest possible moves.
Once you've selected a move, the boardfile will be updated automatically,
and you'll be prompted for a new hand. Unless you're playing against yourself,
you'll need to enter the letters used by your opponent, then select the move
they made from the options.

If you like a more visual interface, run the `web.py`-based frontend:

    ./server.py

Using the Chrome inspector (or view-source, or equivalent) on the Words With Friends page, copy the html for the current active game
into the appropriate field in <http://localhost:8080/>. If you have an idea for an easier input technique, let me know!

##Performance##

If you try running the `cli.py` script and it prints out something about using
the slow Python scorer, you have two options to speed up the results:

  1) Install Cython, and try again. This will use the faster scoring code, which is compiled natively.
  2) Run `cli.py` with the `pypy` interpreter, which uses a JIT-compiler to speed up plain Python code.
