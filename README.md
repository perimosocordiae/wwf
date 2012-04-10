#WWF#
_A mostly-cheating way to get high scores playing Words With Friends_

##Setup##

    curl http://dotnetperls-controls.googlecode.com/files/enable1.txt >words.txt
    cat extra_words.txt >>words.txt

##Usage##

    $ ./cli.py example.board abcdefg
    0.035848 secs, valid play counts: {1: 46, 2: 61, 3: 74, 4: 85, 5: 94, 6: 99, 7: 96}
    got letter combos: {1: 7, 2: 42, 3: 210, 4: 840, 5: 2520, 6: 5040, 7: 5040}
    16.309349 secs, valid move count: 1309343
    38.997948 secs, done
    60 DECAF, OD, WE
    ...pairs of scores and boards....

Use pypy if you have it, and you might get better performance.

Alternatively, run the web frontend:

    ./server.py

Using the Chrome inspector (or view-source, or equivalent) on the Words With Friends page, copy the html for the current active game
into the appropriate field in <http://localhost:8080/>. If you have an idea for an easier input technique, let me know!

