
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
| Thesis URL  | `thesis/thesis.pdf </thesis/thesis.pdf>`_                |
+-------------+----------------------------------------------------------+


INSTALLATION
============
program needs gcc to compile numpy upon installation::

    $ sudo apt-get install gcc

clone the quoridor repository::

    $ git clone https://github.com/mrkvost/quoridor

create virtualenvironment, activate it and install requirements::

    $ cd quoridor/
    $ virtualenv e
    $ . e/bin/activate
    (e) $ pip install -r requirements.txt

run install::

    (e) $ python setup.py install

or for developers::

    (e) $ python setup.py develop

Note, that for development, `tensorflow` package is required. Also,
to have other tools working following system packages are necessary too::

    $ sudo apt-get install gcc python-dev python-virtualenv sqlite3 libfreetype6-dev libxft-dev

RUN
===
To run the game in console mode::

    (e) $ qc

To run without colors::

    (e) $ qc -c

To display help::

    (e) $ qc -h


TESTS
=====
To run tests, run nosetests with setup.py::

    (e) $ python setup.py nosetests

THESIS
======
To create thesis document from source::

    (e) $ docmake

Note: It will also open default program for viewing pdf documents if run under
linux.


TODOS:
 - documentation strings for core module, core functions

 - save / load QLPlayer data

 - verify installation on clean system
 - better/clearer/apposite test names

 - create GUI or WEB interface
 - use curses for better user experience
 - different board sizes
 - 4 players version

NOTES:
 - curses - buildin library
 - urwid - console application framework
 - termcolor, colorama - colors

DEPLOY SHORTCUTS::
    $ sudo apt-get update
    $ sudo apt-get install gcc libfreetype6-dev libxft-dev git python-dev python-virtualenv sqlite3
    $ echo '.mode column\n.headers on' > ~/.sqliterc
