import re
import os
import sys
import time
import datetime
import numpy as np

from quoridor.core.game import (
    YELLOW,
    GREEN,
    Quoridor2,
)
from quoridor.core.context import QuoridorContext
from quoridor.quoridor import (
    ConsoleGame,
    BOARD_BORDER_THICKNESS,
    Vector,
    TRAINING_STATES,
)


COMBINED_TABLE_9 = """\
---------------------------------------------------------------
|  0  |   1  |   2  |   3  |   4  |   5  |   6  |   7  |   8  |
|-----0------1------2------3------4------5------6------7------|
|  9  |  10  |  11  |  12  |  13  |  14  |  15  |  16  |  17  |
|-----8------9-----10-----11-----12-----13-----14-----15------|
| 18  |  19  |  20  |  21  |  22  |  23  |  24  |  25  |  26  |
|----16-----17-----18-----19-----20-----21-----22-----23------|
| 27  |  28  |  29  |  30  |  31  |  32  |  33  |  34  |  35  |
|----24-----25-----26-----27-----28-----29-----30-----31------|
| 36  |  37  |  38  |  39  |  40  |  41  |  42  |  43  |  44  |
|----32-----33-----34-----35-----36-----37-----38-----39------|
| 45  |  46  |  47  |  48  |  49  |  50  |  51  |  52  |  53  |
|----40-----41-----42-----43-----44-----45-----46-----47------|
| 54  |  55  |  56  |  57  |  58  |  59  |  60  |  61  |  62  |
|----48-----49-----50-----51-----52-----53-----54-----55------|
| 63  |  64  |  65  |  66  |  67  |  68  |  69  |  70  |  71  |
|----56-----57-----58-----59-----60-----61-----62-----63------|
| 72  |  73  |  74  |  75  |  76  |  77  |  78  |  79  |  80  |
---------------------------------------------------------------
"""


def print_number_table(size):
    count = size ** 2
    fmt = '{{:{}}}'.format(len(str(count-1)))
    for i in range(count):
        print fmt.format(i),
        if (i + 1) % size == 0:
            print


def print_installed_distributions():
    import pip
    for p in pip.get_installed_distributions():
        print 'project_name:', repr(p.project_name)
        print '    version:', repr(p.version)
        print '    platform:', repr(p.platform)
        print '    location:', repr(p.location)
        print '    key:', repr(p.key)
        print '    parsed_version:', repr(p.parsed_version)
        print '    py_version:', repr(p.py_version)
        print '    requires():', repr(p.requires())
        print '    precedence:', repr(p.precedence)
        print '    extras:', repr(p.extras)
        print '    get_entry_map():', repr(p.get_entry_map())
        print ' -'*40


def print_console_colors():
    for i in range(10):
        color = i + 30
        print str(color),
        print u'  \x1b[1m\x1b[{color}m CONSOLE COLOR \x1b[0m'.format(
            color=str(color)
        )


def show_state(state):
    game = ConsoleGame()
    context = QuoridorContext(game, console_colors=True)
    players = {YELLOW: {'name': '??'}, GREEN: {'name': '??'}}
    context.reset(state=state, players=players)
    for number in range(game.board_positions):
        row, col = divmod(number, game.board_size)
        top = row * game.field_height + BOARD_BORDER_THICKNESS
        bottom = top + game.field_inner_height - 1
        row = int(round(0.25 + float(top + bottom) / 2))
        leftmost = col * game.field_width + BOARD_BORDER_THICKNESS
        rightmost = leftmost + game.field_inner_width - 2
        name = str(number)
        for offset in range(1, min(len(name) + 1, rightmost - leftmost)):
            position = Vector(row=row, col=leftmost + offset + 1)
            game.output_base[position] = name[offset - 1]
    game.display_on_console(context)
