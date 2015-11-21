import os
import random

from optparse import OptionParser

from core import (
    Vector,
    ROW,
    COL,
    PAWN_POS_MIN,
    PAWN_POS_MAX,
    WALL_POS_MIN,
    WALL_POS_MAX,
    HORIZONTAL,
    DIRECTIONS,
    YELLOW,
    GREEN,
    GOAL_ROW,
    InvalidMove,
    Quoridor2,
)

INNER_WIDTH = 72
INNER_HEIGHT = 36

PLAYER_LETTER_CONSOLE = {YELLOW: u'Y', GREEN: u'G'}
FIELD_WIDTH_CONSOLE = 8
FIELD_HEIGHT_CONSOLE = 4
COLOR_START_CONSOLE = {YELLOW: u'\x1b[1m\x1b[33m', GREEN: u'\x1b[1m\x1b[32m'}
COLOR_END_CONSOLE = u'\x1b[0m'


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
        color_start = COLOR_START_CONSOLE[pawn_color]
        color_end = COLOR_END_CONSOLE

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


def display_on_console(game, colors_on):
    base = make_base()
    for direction, walls in game.walls.items():
        for wall in walls:
            wall_to_base(direction, wall, base, colors_on=colors_on)
    for pawn, color in game.pawns.items():
        pawn_to_base(pawn, color, base, colors_on=colors_on)

    print_base(base)


def console_run(options):
    colors_on = options.colors_on
    if os.getenv('ANSI_COLORS_DISABLED') is not None:
        colors_on = False

    game = Quoridor2()
    if options.example:
        random_pawn_positions(game)
        random_walls(game)
        display_on_console(game, colors_on)
        return

    # TODO: ...
    while not game.game_ended():
        display_on_console(game, colors_on)
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
