import os
import random

from optparse import OptionParser

from core import (
    Vector,
    ROW,
    COL,
    BOARD_SIZE,
    WALL_BOARD_SIZE,
    PAWN_POS_MIN,
    PAWN_POS_MAX,
    WALL_POS_MIN,
    WALL_POS_MAX,
    HORIZONTAL,
    DIRECTIONS,
    YELLOW,
    GREEN,
    PLAYER_COLOR_NAME,
    GOAL_ROW,
    InvalidMove,
    Quoridor2,
)

COLOR_START_CONSOLE = {YELLOW: u'\x1b[1m\x1b[33m', GREEN: u'\x1b[1m\x1b[32m'}
COLOR_END_CONSOLE = u'\x1b[0m'

FIELD_INNER_HEIGHT = 3
FIELD_INNER_WIDTH = 7

WALL_THICKNESS = 1

FIELD_WIDTH = FIELD_INNER_WIDTH + WALL_THICKNESS
FIELD_HEIGHT = FIELD_INNER_HEIGHT + WALL_THICKNESS

WALL_LENGTH_HORIZONTAL = 2 * FIELD_INNER_WIDTH + WALL_THICKNESS
WALL_LENGTH_VERTICAL = 2 * FIELD_INNER_HEIGHT + WALL_THICKNESS

BOARD_INNER_WIDTH = (
    WALL_BOARD_SIZE * WALL_THICKNESS + BOARD_SIZE * FIELD_INNER_WIDTH
)
BOARD_INNER_HEIGHT = (
    WALL_BOARD_SIZE * WALL_THICKNESS + BOARD_SIZE * FIELD_INNER_HEIGHT
)

BOARD_BORDER_THICKNESS = 1
BOARD_WIDTH = BOARD_INNER_WIDTH + 2 * BOARD_BORDER_THICKNESS
BOARD_HEIGHT = BOARD_INNER_HEIGHT + 2 * BOARD_BORDER_THICKNESS


def _base_border(base):
    # corners:
    base.update({
        Vector(row=0, col=0): u'\u2554',
        Vector(row=0, col=BOARD_WIDTH - 1): u'\u2557',
        Vector(row=BOARD_HEIGHT - 1, col=0): u'\u255a',
        Vector(row=BOARD_HEIGHT - 1, col=BOARD_WIDTH - 1): u'\u255d',
    })

    # top and bottom:
    for col in range(BOARD_BORDER_THICKNESS, BOARD_WIDTH - 1):
        base[Vector(row=0, col=col)] = u'\u2550'
        base[Vector(row=BOARD_HEIGHT - 1, col=col)] = u'\u2550'

    # left and right:
    for row in range(BOARD_BORDER_THICKNESS, BOARD_HEIGHT - 1):
        base[Vector(row=row, col=0)] = u'\u2551'
        base[Vector(row=row, col=BOARD_WIDTH - 1)] = u'\u2551'

    return base


def make_base():
    base = _base_border({})

    for row in range(BOARD_BORDER_THICKNESS, BOARD_HEIGHT - 1):
        for col in range(BOARD_BORDER_THICKNESS, BOARD_WIDTH - 1):
            col_mod = col % (FIELD_INNER_WIDTH + WALL_THICKNESS) == 0
            if row % (FIELD_INNER_HEIGHT + WALL_THICKNESS) == 0:
                if col % 2 == 0 and not col_mod:
                    base[Vector(row=row, col=col)] = '-'
                else:
                    base[Vector(row=row, col=col)] = ' '
            else:
                if row % 2 != 0 and col_mod:
                    base[Vector(row=row, col=col)] = '|'
                else:
                    base[Vector(row=row, col=col)] = ' '
    return base


def print_base(base):
    print '\n'.join([
        ''.join([
            base[Vector(row=row, col=col)] for col in range(BOARD_WIDTH + 100)
            if base.get(Vector(row=row, col=col)) is not None
        ]) for row in range(BOARD_HEIGHT)
    ])


def wall_to_base(direction, position, base, colors_on=False):
    basic_col_offset = direction[COL] + direction[ROW] * FIELD_WIDTH
    basic_row_offset = direction[ROW] + direction[COL] * FIELD_HEIGHT

    col = position[COL] * FIELD_WIDTH
    row = position[ROW] * FIELD_HEIGHT

    if direction == HORIZONTAL:
        for col_delta in range(WALL_LENGTH_HORIZONTAL):
            base[Vector(
                row=basic_row_offset + row,
                col=basic_col_offset + col + col_delta,
            )] = u'\u2550'
    else:
        for row_delta in range(WALL_LENGTH_VERTICAL):
            base[Vector(
                row=basic_row_offset + row + row_delta,
                col=basic_col_offset + col,
            )] = u'\u2551'


def pawn_to_base(position, pawn_color, base, colors_on=False):
    color_start = u''
    color_end = u''
    if colors_on:
        color_start = COLOR_START_CONSOLE[pawn_color]
        color_end = COLOR_END_CONSOLE

    leftmost = position.col * FIELD_WIDTH + BOARD_BORDER_THICKNESS
    rightmost = leftmost + FIELD_INNER_WIDTH - 2
    top = position.row * FIELD_HEIGHT + BOARD_BORDER_THICKNESS
    bottom = top + FIELD_INNER_HEIGHT - 1

    # left and right sides:
    for column in range(leftmost, rightmost + 1):
        base[Vector(row=top, col=column)] = u'\u203e'
        base[Vector(row=bottom, col=column)] = u'_'

    # top and bottom sides:
    for row in range(top, bottom + 1):
        base[Vector(row=row, col=leftmost)] = color_start + u'\u23b8'
        base[Vector(row=row, col=rightmost)] = u'\u23b9' + color_end

    # corners:
    base.update({
        Vector(row=top, col=leftmost): color_start + u'\u27cb',
        Vector(row=top, col=rightmost): u'\u27cd' + color_end,
        Vector(row=bottom, col=leftmost): color_start + u'\u27cd',
        Vector(row=bottom, col=rightmost): u'\u27cb' + color_end,
    })

    # text:
    name = PLAYER_COLOR_NAME[pawn_color]

    for offset in range(1, rightmost - leftmost):
        row = int(round(0.25 + float(top + bottom) / 2))
        position = Vector(row=row, col=leftmost + offset)
        if offset <= len(name):
            base[position] = name[offset - 1]


def random_walls(game):
    for i in range(random.randint(10, 30)):
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


def status_line_to_base(row, line, base):
    for offset, char in enumerate(u' ' + line):
        base[Vector(row=row, col=BOARD_WIDTH + offset)] = char

def player_status_to_base(game, base):
    # TODO: WINNER info
    for n, color in enumerate(game.players):
        row = n * 4 + 2
        color_name = PLAYER_COLOR_NAME[color].upper()

        line = color_name + u' player'
        if color == game.on_move:
            line += ' - now playing'
        status_line_to_base(row, line, base)

        walls = unicode(game.player_wall_count(color))
        status_line_to_base(row + 1, u'Walls: ' + walls, base)

        line = u'Dist: ' + unicode(game.pawn_distance_from_goal(color))
        status_line_to_base(row + 2, line, base)


def status_to_base(game, base):
    line = u'Moves made: ' + unicode(game.moves_made)
    status_line_to_base(0, line, base)

    player_status_to_base(game, base)

    # info: Invalid move, etc...
    # menu possibilities
    # input


def display_on_console(game, colors_on):
    base = make_base()
    for direction, walls in game.walls.items():
        for wall in walls:
            wall_to_base(direction, wall, base, colors_on=colors_on)
    for pawn, color in game.pawns.items():
        pawn_to_base(pawn, color, base, colors_on=colors_on)

    status_to_base(game, base)

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
