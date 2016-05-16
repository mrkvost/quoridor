import re
import os
import sys
import time
import math
import datetime
import operator
import functools
import itertools
import numpy as np

from quoridor.core.game import (
    YELLOW,
    GREEN,
    STARTING_WALL_COUNT,
    DOWN,
    DOWNDOWN,
    DOWNRIGHT,
    DOWNLEFT,
    UP,
    UPUP,
    UPRIGHT,
    UPLEFT,
    Quoridor2,
)
from quoridor.core.context import QuoridorContext
from quoridor.quoridor import ConsoleGame
from quoridor.ai.training import TRAINING_STATES


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
    game.display_on_console(context)


def lapse_training_states():
    for difficulty in range(len(TRAINING_STATES)):
        for state in TRAINING_STATES[difficulty]:
            print 'difficulty:', difficulty
            print 'state:', state
            show_state(state)
            yield


def is_state_valid_trivial(game, state):
    max_walls = STARTING_WALL_COUNT
    if state[3] + state[4] != 2 * max_walls - len(state[5]):
        return False        # number of walls in stocks and placed walls differ
    elif 0 > state[1] or game.board_positions - 1 < state[1]:
        return False        # yellow outside the board
    elif 0 > state[2] or game.board_positions - 1 < state[2]:
        return False        # green outside the board
    elif state[3] < 0 or state[3] > max_walls:
        return False        # wrong number of walls in yellow stock
    elif state[4] < 0 or state[4] > max_walls:
        return False        # wrong number of walls in green stock
    elif state[0] not in (YELLOW, GREEN):
        return False        # unknown player moving
    elif len(state) != 6:
        return False        # unrecognized state
    return True


def is_state_valid(game, state, check_trivial=False):
    if state[1] == state[2]:
        return False
    elif state[1] in game.goal_positions[YELLOW]:
        if state[0] == YELLOW:
            return False    # player, which is winning cannot be moving
        elif state[2] in game.goal_positions[GREEN]:
            return False    # both cannot be in the winning position

        for pawn_move in (UP, UPUP, UPLEFT, UPRIGHT):
            if game.is_valid_pawn_move((YELLOW, ) + state[1:], pawn_move):
                break
        else:
            return False    # pawn could not get to this winning position

        if not game.shortest_path(state, GREEN):
            return False    # GREEN cannot reach goal
    elif state[2] in game.goal_positions[GREEN]:
        if state[0] == GREEN:
            return False    # player, which is winning cannot be moving

        for pawn_move in (DOWN, DOWNDOWN, DOWNLEFT, DOWNRIGHT):
            if game.is_valid_pawn_move((GREEN, ) + state[1:], pawn_move):
                break
        else:
            return False    # pawn could not get to this winning position

        if not game.shortest_path(state, YELLOW):
            return False    # YELLOW cannot reach goal
    elif not game.players_can_reach_goal(state):
        return False        # at least one player cannot reach goal

    temp_walls = set(state[5])
    while temp_walls:
        wall = temp_walls.pop()
        if temp_walls & game.wall_crossers(wall):
            return False    # there are crossing walls on the board

    return (not check_trivial) or is_state_valid_trivial(game, state)


_VALID_STATE_STATUS_FMT = '''\
sec.:{s:>5}s |count:{c:>8} |c/s.:{cs:>5} |pl:{p:>2} |verified:{v:>8} \
|valid: {val:>7}\
'''


def _print_valid_states_status(start_time, counter, placed, verified, valid):
    delta_time = datetime.datetime.now() - start_time
    seconds = int(delta_time.total_seconds())
    print _VALID_STATE_STATUS_FMT.format(
        s=seconds, c=counter, v=verified, p=placed, val=valid,
        cs=counter//seconds,
    )


def count_valid_states(placed, yrange=None, grange=None, show_each=1048576):
    game = Quoridor2()
    wall_moves = range(game.wall_moves)
    yrange = yrange or range(game.board_positions)
    grange = grange or range(game.board_positions)
    valid = counter = verified = 0
    stock_distributions = 11 - abs(placed - 10)

    start_time = datetime.datetime.now()
    try:
        for comb in itertools.combinations(wall_moves, placed):
            combination = frozenset(comb)
            for ypawn in yrange:
                for gpawn in grange:
                    for color in (YELLOW, GREEN):
                        counter += 1
                        verified += stock_distributions
                        # no need to validate number of walls in stock
                        state = (color, ypawn, gpawn, 10, 10, combination)
                        if is_state_valid(game, state):
                            valid += stock_distributions
                        if counter % 16384 == 0:
                            _print_valid_states_status(
                                start_time,
                                counter,
                                placed,
                                verified,
                                valid,
                            )
    except KeyboardInterrupt, EOFError:
        return
    _print_valid_states_status(start_time, counter, placed, verified, valid)
    return valid


def comb(N,k): # from scipy.comb(), but MODIFIED!
    if (k > N) or (N < 0) or (k < 0):
        return 0L
    N,k = map(long,(N,k))
    top = N
    val = 1L
    while (top > (N-k)):
        val *= top
        top -= 1
    n = 1L
    while (n < k+1L):
        val /= n
        n += 1
    return val


mertens_Sf = sum([
    reduce(operator.mul, [j for j in range(128, 124 - 4 * i, -4)], 1)
    for i in range(20)
])

# print [i+1 - (i>10)*(2*(i-10)) for i in range(21)]
my_S = 2*6399*sum([(i+1 - (i>10)*2*(i-10))*comb(128, i) for i in range(21)])
