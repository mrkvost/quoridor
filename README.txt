To run the game in console mode with linux terminal colors on:

    $ python quoridor.py -ce

To run tests, create virtual envirnonment and install test dependencies:

    $ cd /path/to/quoridor/
    $ virtualenv e
    $ . e/bin/activate
    (e) $ pip install -r test-requirements.txt
    (e) $ PYTHONPATH=. nosetests

TODOS:
 1. documentation strings for core module, core functions
 2. better/clearer/apposite test names
 3. different board sizes
 4. 4 players version
