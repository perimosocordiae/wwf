
#CFLAGS=-O2 -Wall -prof -fprof-auto -rtsopts
CFLAGS=-O2 -Wall

wwf: Main.hs Scrabble.hs
	ghc $(CFLAGS) $< -o $@

clean:
	rm -f *.hi *.o wwf
