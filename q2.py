# TODO: documentation

import os
import random

from optparse import OptionParser
from collections import namedtuple


Vector = namedtuple('Vector', ['row', 'col'])
ROW = 0
COL = 1

SIZE = 9
PAWN_POS_MIN = 0
PAWN_POS_MAX = SIZE - 1
WALL_POS_MIN = 0
WALL_POS_MAX = SIZE - 2

VERTICAL = Vector(row=1, col=0)
HORIZONTAL = Vector(row=0, col=1)
DIRECTIONS = (VERTICAL, HORIZONTAL)
OPPOSITE_DIRECTION = {VERTICAL: HORIZONTAL, HORIZONTAL: VERTICAL}

# It is possible to jump over single pawn
JUMP_DISTANCE_MAX = 2

YELLOW = 0
GREEN = 1

STARTING_POSITION_DEFAULT_YELLOW = Vector(row=PAWN_POS_MIN, col=4)
STARTING_POSITION_DEFAULT_GREEN = Vector(row=PAWN_POS_MAX, col=4)

GOAL_ROW = {
    YELLOW: PAWN_POS_MAX,
    GREEN: PAWN_POS_MIN,
}
FOLLOWING_PLAYER = {YELLOW: GREEN, GREEN: YELLOW}

PLAYER_LETTER_CONSOLE = {YELLOW: u'Y', GREEN: u'G'}
FIELD_WIDTH_CONSOLE = 8
FIELD_HEIGHT_CONSOLE = 4
COLOR_CONSOLE = {YELLOW: u'\x1b[1m\x1b[33m', GREEN: u'\x1b[1m\x1b[32m'}


def add_direction(position, direction):
    return Vector(
        row=position[ROW] + direction[ROW],
        col=position[COL] + direction[COL],
    )


def substract_direction(position, direction):
    return Vector(
        row=position[ROW] - direction[ROW],
        col=position[COL] - direction[COL],
    )


def adjacent_move_direction(from_, to):
    direction = Vector(
        row=abs(from_[ROW] - to[ROW]),
        col=abs(from_[COL] - to[COL]),
    )
    if direction not in DIRECTIONS:
        return None
    return direction


def pawn_move_distance_no_walls(from_, to):
    return abs(from_[COL] - to[COL]) + abs(from_[ROW] - to[ROW])


def pawn_within_board(position):
    return PAWN_POS_MIN <= position[COL] <= PAWN_POS_MAX and (
        PAWN_POS_MIN <= position[ROW] <= PAWN_POS_MAX
    )


def is_occupied(position, pawns):
    return position in pawns


def adjacent_pawn_spaces(position):
    if not pawn_within_board(position):
        return []
    spaces = []
    if position[ROW] > PAWN_POS_MIN:
        spaces.append(substract_direction(position, VERTICAL))
    if position[ROW] < PAWN_POS_MAX:
        spaces.append(add_direction(position, VERTICAL))

    if position[COL] > PAWN_POS_MIN:
        spaces.append(substract_direction(position, HORIZONTAL))
    if position[COL] < PAWN_POS_MAX:
        spaces.append(add_direction(position, HORIZONTAL))
    return spaces


def is_wall_between(from_, to, walls):
    direction = adjacent_move_direction(from_, to)
    if direction is None:
        return None     # TODO: think, whether exception here would be better
    else:
        direction = OPPOSITE_DIRECTION[direction]

    position = Vector(
        row=min(from_[ROW], to[ROW]),
        col=min(from_[COL], to[COL]),
    )

    if position in walls[direction]:
        return True
    elif substract_direction(position, direction) in walls[direction]:
        return True

    return False


def adjacent_pawn_spaces_not_blocked(position, walls):
    adjacent_positions = adjacent_pawn_spaces(position)
    for adjacent_position in adjacent_positions:
        if not is_wall_between(position, adjacent_position, walls):
            yield adjacent_position


def pawn_legal_moves(position, pawns, walls):
    for adjacent_position in adjacent_pawn_spaces_not_blocked(position, walls):
        if is_occupied(adjacent_position, pawns):
            jumps = adjacent_pawn_spaces_not_blocked(adjacent_position, walls)
            for jump in jumps:
                if jump != position:
                    yield jump
        else:
            yield adjacent_position


def is_correct_pawn_move(from_, to, pawns, walls):
    return to in pawn_legal_moves(from_, pawns, walls)


def wall_within_board(position):
    return WALL_POS_MIN <= position[COL] <= WALL_POS_MAX and (
        WALL_POS_MIN <= position[ROW] <= WALL_POS_MAX
    )


def wall_intersects(direction, position, walls):
    if position in walls[direction]:
        return True
    elif position in walls[OPPOSITE_DIRECTION[direction]]:
        return True
    elif add_direction(position, direction) in walls[direction]:
        return True
    elif substract_direction(position, direction) in walls[direction]:
        return True
    return False


def pawn_can_reach_goal(color, current_position, walls):
    # TODO: optimize!, what if pawn already reached goal?
    to_visit = set([current_position])
    visited = set()
    while to_visit:
        position = to_visit.pop()
        if position[ROW] == GOAL_ROW[color]:
            return True
        visited.add(position)
        new_positions = adjacent_pawn_spaces_not_blocked(position, walls)
        for new_position in new_positions:
            if new_position not in visited:
                to_visit.add(new_position)
    return False


def is_correct_wall_move(direction, position, pawns, walls):
    if not wall_within_board(position):
        return False
    elif wall_intersects(direction, position, walls):
        return False

    walls[direction].add(position)
    for pawn_position, color in pawns.items():
        if not pawn_can_reach_goal(color, pawn_position, walls):
            walls[direction].remove(position)
            return False

    walls[direction].remove(position)
    return True


class InvalidMove(Exception):
    pass


class Quoridor2(object):

    def __init__(self):
        self._state = {
            'winner': None,
            'game_ended': False,
            'on_move': YELLOW,
            'players': {
                YELLOW: {
                    'pawn': STARTING_POSITION_DEFAULT_YELLOW,
                    'walls': 10,
                },
                GREEN: {
                    'pawn': STARTING_POSITION_DEFAULT_GREEN,
                    'walls': 10,
                },
            },
            'pawns': {
                STARTING_POSITION_DEFAULT_YELLOW: YELLOW,
                STARTING_POSITION_DEFAULT_GREEN: GREEN,
            },
            'walls': {
                VERTICAL: set(),
                HORIZONTAL: set(),
            },
        }

    def game_ended(self):
        return self._state['game_ended']

    @property
    def current_wall_count(self):
        return self._state['players'][self._state['on_move']]['walls']

    def place_wall(self, direction, position):
        if self.game_ended():
            raise InvalidMove('Game already ended.')

        if not self.current_wall_count > 0:
            raise InvalidMove('No walls to play with.')

        is_correct = is_correct_wall_move(
            direction,
            position,
            self._state['pawns'],
            self._state['walls']
        )

        if not is_correct:
            # TODO: reason the move is invalid would be nice, e.g. no path...
            raise InvalidMove()

        color = self._state['on_move']
        self._state['walls'][direction].add(position)
        self._state['players'][color]['walls'] -= 1
        self._state['on_move'] = FOLLOWING_PLAYER[color]

    @property
    def current_pawn_position(self):
        return self._state['players'][self._state['on_move']]['pawn']

    def move_pawn(self, new_position):
        if self.game_ended():
            raise InvalidMove('Game already ended.')

        pawn_position = self.current_pawn_position,
        is_correct = is_correct_pawn_move(
            pawn_position,
            new_position,
            self._state['pawns'],
            self._state['walls']
        )

        if not is_correct:
            raise InvalidMove()

        color = self._state['on_move']
        self._state['players'][color]['pawn'] = new_position
        del self._state['pawns'][pawn_position]
        self._state['pawns'][new_position] = color
        # Check end of the game...
        if new_positions[ROW] == GOAL_ROW[color]:
            self._state['game_ended'] = True
            self._state['winner'] = color

        self._state['on_move'] = FOLLOWING_PLAYER[color]

    @property
    def pawns(self):
        return self._state['pawns']

    @property
    def walls(self):
        return self._state['walls']


INNER_WIDTH = 72
INNER_HEIGHT = 36


def make_base():
    base = {
        (0, 0): u'\u2554',                      # TOP LEFT CORNER
        (INNER_WIDTH, 0): u'\u2557',            # TOP RIGHT CORNER
        (0, INNER_HEIGHT): u'\u255a',           # BOTTOM LEFT CORNER
        (INNER_WIDTH, INNER_HEIGHT): u'\u255d', # BOTTOM RIGHT CORNER
    }

    for i in range(1, INNER_WIDTH):
        base[(i, 0)] = u'\u2550'              # TOP SIDE
        base[(i, INNER_HEIGHT)] = u'\u2550'   # BOTTOM SIDE

    for row in range(1, INNER_HEIGHT):
        base[(0, row)] = u'\u2551'            # LEFT SIDE
        base[(INNER_WIDTH, row)] = u'\u2551'  # RIGHT SIDE
        for col in range(1, INNER_WIDTH):
            col_mod_8 = col % 8 == 0
            if row % 4 == 0:
                if col % 2 == 0 and not col_mod_8:
                    base[(col, row)] = '-'
                else:
                    base[(col, row)] = ' '
            else:
                if row % 2 != 0 and col_mod_8:
                    base[(col, row)] = '|'
                else:
                    base[(col, row)] = ' '
    return base


def print_base(base):
    print '\n'.join([
        ''.join([base[(c, r)] for c in range(INNER_WIDTH + 1)])
        for r in range(INNER_HEIGHT + 1)
    ])


def wall_to_base(direction, position, base, colors_on=False):
    basic_col_offset = direction[COL] + direction[ROW] * FIELD_WIDTH_CONSOLE
    basic_row_offset = direction[ROW] + direction[COL] * FIELD_HEIGHT_CONSOLE

    col = position[COL] * FIELD_WIDTH_CONSOLE
    row = position[ROW] * FIELD_HEIGHT_CONSOLE

    if direction == HORIZONTAL:
        for col_delta in range(15):
            base[(
                basic_col_offset + col + col_delta,
                basic_row_offset + row,
            )] = u'\u2550'
    else:
        for row_delta in range(7):
            base[(
                basic_col_offset + col,
                basic_row_offset + row + row_delta,
            )] = u'\u2551'


def pawn_to_base(position, pawn_color, base, colors_on=False):
    color_start = u''
    color_end = u''
    if colors_on:
        color_start = COLOR_CONSOLE[pawn_color]
        color_end = u'\x1b[0m'

    col = position.col * FIELD_WIDTH_CONSOLE + 1
    row = position.row * FIELD_HEIGHT_CONSOLE + 1
    base.update({
        (col + 1, row): color_start + u'\u27cb',
        (col + 2, row): u'\u203e',
        (col + 3, row): u'\u203e',
        (col + 4, row): u'\u203e',
        (col + 5, row): u'\u27cd' + color_end,

        (col + 1, row + 1): color_start + u'\u23b8',
        (col + 2, row + 1): PLAYER_LETTER_CONSOLE[pawn_color],
        (col + 3, row + 1): PLAYER_LETTER_CONSOLE[pawn_color],
        (col + 4, row + 1): PLAYER_LETTER_CONSOLE[pawn_color],
        (col + 5, row + 1): u'\u23b9' + color_end,

        (col + 1, row + 2): color_start + u'\u27cd',
        (col + 2, row + 2): u'_',
        (col + 3, row + 2): u'_',
        (col + 4, row + 2): u'_',
        (col + 5, row + 2): u'\u27cb' + color_end,
    })


def random_walls(game):
    for i in range(random.randint(10, 20)):
        position = Vector(
            row=random.randint(WALL_POS_MIN, WALL_POS_MAX),
            col=random.randint(WALL_POS_MIN, WALL_POS_MAX),
        )
        direction = random.choice(DIRECTIONS)
        try:
            game.place_wall(direction, position)
        except InvalidMove:
            pass


def random_pawn_positions(game):
    game._state['pawns'] = {}
    for color, goal_row in GOAL_ROW.items():
        position = Vector(
            row=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
            col=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
        )
        while position in game._state['pawns'] or position.row == goal_row:
            position = Vector(
                row=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
                col=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
            )

        game._state['players'][color]['pawn'] = position
        game._state['pawns'][position] = color


def console_run(options):
    colors_on = options.colors_on
    if os.getenv('ANSI_COLORS_DISABLED') is not None:
        colors_on = False

    game = Quoridor2()
    if options.example:
        random_pawn_positions(game)
        random_walls(game)

    while not game.game_ended():
        base = make_base()
        for direction, walls in game.walls.items():
            for wall in walls:
                wall_to_base(direction, wall, base, colors_on=colors_on)
        for pawn, color in game.pawns.items():
            pawn_to_base(pawn, color, base, colors_on=colors_on)

        print_base(base)
        if options.example:
            return
        break   # TODO: TO BE REMOVED


def main():
    parser = OptionParser()
    parser.add_option(
        '-c', '--colors', dest='colors_on', default=False, action='store_true',
        help='Enable color output in console mode. Disabled by default.'
    )

    parser.add_option(
        '-e', '--example', dest='example', default=False, action='store_true',
        help=(
            'In console mode, create random board position display it and end.'
            ' Serves for debugging.'
        )
    )

    options, args = parser.parse_args()
    console_run(options)


if __name__ == '__main__':
    main()
