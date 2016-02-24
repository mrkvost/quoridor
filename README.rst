
+-------------+----------------------------------------------------------+
| Bachelor Thesis information                                            |
+=============+==========================================================+
| Thesis name | Artifictial neural network as an opponent in Quoridor    |
+-------------+----------------------------------------------------------+
| Author      | Michal Hoľa                                              |
+-------------+----------------------------------------------------------+
| Adviser     | Mgr. Peter Gergeľ                                        |
+-------------+----------------------------------------------------------+
|             | 1. Brief overview of existing approaches to the          |
|             |    production of agents playing board games              |
| Aim         | 2. Program intelligent agent built based on neural       |
|             |    networks, which will learn to play Quoridor           |
|             | 3. Test end evaluate the behaviour of the agent          |
+-------------+----------------------------------------------------------+
| Sources     | `thesis/sources.rst </thesis/sources.rst>`_              |
+-------------+----------------------------------------------------------+
| Diary       | `thesis/diary.rst </thesis/diary.rst>`_                  |
+-------------+----------------------------------------------------------+
| Project URL | `<https://github.com/mrkvost/quoridor>`_                 |
+-------------+----------------------------------------------------------+


INSTALLATION
============

clone the quoridor repository::

    $ git clone https://github.com/mrkvost/quoridor

create virtualenvironment and activate it::

    $ cd quoridor/
    $ virtualenv e
    $ . e/bin/activate

run install::

    (e) $ python setup.py install

or for developers::

    (e) $ python setup.py develop

RUN
===

To run the game in console mode with linux terminal colors on::

    (e) $ qc -c

To run without clearing the console output::

    (e) $ qc -w

To display help::

    (e) $ qc -h


TESTS
=====

To run tests, run nosetests with setup.py::

    (e) $ python setup.py nosetests


TODOS:
 - save / load game
 - documentation strings for core module, core functions

 - Neural Network player
 - save / load NN player weights

 - save / load QLPlayer data

 - better/clearer/apposite test names
 - different board sizes
 - 4 players version

 - use curses for better user experience
 - create GUI or WEB interface

NOTES:
 - curses - buildin library
 - urwid - console application framework
 - termcolor, colorama - colors
