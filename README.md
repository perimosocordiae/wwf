#WWF#
_A mostly-cheating way to get high scores playing Words With Friends_

##Setup##

    curl http://dotnetperls-controls.googlecode.com/files/enable1.txt >words.txt

##Usage##

    ./cli.py foo.board <letters_in_hand>

or 

    ./server.py

Using the Chrome inspector (or view-source, or equivalent) on the Words With Friends page, copy the html for the current active game
into the appropriate field in <http://localhost:8080/>. If you have an idea for an easier input technique, let me know!

