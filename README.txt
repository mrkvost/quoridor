To run the game in console mode with linux terminal colors on:

    $ python quoridor.py -ce

To run tests, create virtual envirnonment and run nosetests with setup.py:

    $ cd /path/to/quoridor/
    $ virtualenv e
    $ . e/bin/activate
    (e) $ python setup.py nosetests

TODOS:
 1. documentation strings for core module, core functions
 2. better/clearer/apposite test names
 3. different board sizes
 4. 4 players version
 5. use curses for better user experience

NOTES:
 - curses - buildin library
 - urwid - console application framework
 - termcolor, colorama - colors
