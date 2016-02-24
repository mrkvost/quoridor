import os
import re
import copy
import time
import random
import collections
import traceback

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
    VERTICAL,
    HORIZONTAL,
    current_pawn_position,
    adjacent_spaces_not_blocked,
    FOLLOWING_PLAYER,
)

from players import RandomPlayer, RandomPlayerWithPath, QLPlayer


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

PLAYER_GOAL_INFO = {
    YELLOW: u' (goes to the bottom \u21ca)',
    GREEN: u' (goes to the top \u21c8)',
}

CONSOLE_CLEAR = {'nt': 'cls', 'posix': 'clear'}

Pawn = collections.namedtuple('Pawn', ['row', 'col'])
HorizontalWall = collections.namedtuple('HorizontalWall', ['row', 'col'])
VerticalWall = collections.namedtuple('VerticalWall', ['row', 'col'])
ACTION_TYPE = {
    None: Pawn,
    HORIZONTAL: HorizontalWall,
    VERTICAL: VerticalWall,
}


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

    fw2 = (FIELD_WIDTH // 2)
    for col in range(BOARD_SIZE):
        base[Vector(row=0, col=col * FIELD_WIDTH + fw2)] = (
            (u'\x1b[47m\x1b[1m\x1b[30m') + u'ABCDEFGHI'[col] + COLOR_END_CONSOLE
        )

    fh2 = (FIELD_HEIGHT // 2)
    for row in range(BOARD_SIZE):
        base[Vector(row=row * FIELD_HEIGHT + fh2, col=0)] = (
            (u'\x1b[47m\x1b[1m\x1b[30m') + u'0123456789'[row] + COLOR_END_CONSOLE
        )

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


def clear_console():
    os.system(CONSOLE_CLEAR[os.name])


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


def random_walls(game, state):
    for i in range(random.randint(10, 30)):
        position = Vector(
            row=random.randint(WALL_POS_MIN, WALL_POS_MAX),
            col=random.randint(WALL_POS_MIN, WALL_POS_MAX),
        )
        direction = random.choice(DIRECTIONS)
        try:
            game.execute_action(state, (direction, position))
        except InvalidMove:
            pass


def random_pawn_positions(game, state):
    state['pawns'] = {}
    for color, goal_row in GOAL_ROW.items():
        position = Vector(
            row=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
            col=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
        )
        while position in state['pawns'] or position.row == goal_row:
            position = Vector(
                row=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
                col=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
            )

        state['pawns'][color] = position


def status_line_to_base(row, line, base):
    for offset, char in enumerate(u' ' + line):
        base[Vector(row=row, col=BOARD_WIDTH + offset)] = char


def pawn_distance_from_goal(state, color):
    starting_position = state['pawns'][color]
    goal_row = GOAL_ROW[color]
    walls = state['placed_walls']

    to_visit = collections.deque([(starting_position, 0)])
    visited = set()

    while to_visit:
        position, distance = to_visit.popleft()
        if position in visited:
            continue
        if position.row == goal_row:
            return distance
        visited.add(position)

        right_distance = distance % 2 == int(color == state['on_move'])
        for possible in adjacent_spaces_not_blocked(state, position):
            jumps = right_distance and possible in state['pawns'].values()
            if jumps:
                to_visit.append((possible, distance))
            else:
                to_visit.append((possible, distance + 1))

    error_msg_fmt = u'{color_name} player can not reach goal row!'
    color_name = PLAYER_COLOR_NAME[color].upper()
    raise Exception(error_msg_fmt.format(color_name=color_name))


def player_status_to_base(state, base):
    # TODO: WINNER info
    for n, color in enumerate(state['pawns']):
        row = n * 5 + 2
        color_name = PLAYER_COLOR_NAME[color].upper()

        line = color_name + u' player'
        if color == state['on_move']:
            line += ' - now playing'
        status_line_to_base(row, line, base)

        status_line_to_base(row + 1, PLAYER_GOAL_INFO[color], base)

        walls = unicode(state['walls'][color])
        status_line_to_base(row + 2, u' Walls: ' + walls, base)

        line = u' Dist: ' + unicode(pawn_distance_from_goal(state, color))
        status_line_to_base(row + 3, line, base)


def history_to_base(base, history):
    status_line_to_base(12, 'HISTORY:', base)
    for n, action in enumerate(history[-10:]):
        row = 13 + n
        action_type, position = action
        move = ACTION_TYPE[action_type](row=position.row, col=position.col)
        status_line_to_base(row, ' ' + repr(move), base)

def status_to_base(state, history, base):
    moves_made = len(history)
    line = u'Moves made: ' + unicode(moves_made)
    status_line_to_base(0, line, base)

    player_status_to_base(state, base)

    history_to_base(base, history)

    # info: Invalid move, etc...
    # menu possibilities
    # input


def display_on_console(state, colors_on, history=None, message=None,
                       with_clear=True):
    if history is None:
        history = []
    if with_clear:
        clear_console()
    base = make_base()
    for direction, walls in state['placed_walls'].items():
        for wall in walls:
            wall_to_base(direction, wall, base, colors_on=colors_on)
    for color, pawn in state['pawns'].items():
        pawn_to_base(pawn, color, base, colors_on=colors_on)

    status_to_base(state, history, base)

    print_base(base)

    if message is not None:
        print message


class InputError(Exception):
    pass


COLUMN_LETTERS = u'abcdefghi'
WALL_INPUT_PATTERN = (
    ur'(?:wall|w|)\s*'
    ur'(?P<direction>h|v)\s*'
    ur'(?P<row>\d+)\s*'
    ur'(?P<col>[{column_letters}])'
).format(column_letters=COLUMN_LETTERS)
WALL_INPUT_RE = re.compile(WALL_INPUT_PATTERN, re.I)
INPUT_DIRECTIONS = {'h': HORIZONTAL, 'v': VERTICAL}

MOVE_INPUT_PATTERN = (
    ur'(?:pawn|p|)\s*'
    ur'(?P<row>\d+)\s*'
    ur'(?P<col>[{column_letters}])'
).format(column_letters=COLUMN_LETTERS)
MOVE_INPUT_RE = re.compile(MOVE_INPUT_PATTERN, re.I)

QUIT_INPUT_PATTERN = u'quit|q|exit|end'
QUIT_INPUT_RE = re.compile(QUIT_INPUT_PATTERN, re.I)

UNDO_INPUT_PATTERN = u'u|undo|back'
UNDO_INPUT_RE = re.compile(UNDO_INPUT_PATTERN, re.I)

ACTION_UNKNOWN = 'unknown'
ACTION_END = 'end'
ACTION_MOVE = 'move'
ACTION_UNDO = 'undo'


def parse_input():
    try:
        user_input = raw_input('Enter choice:')
    except (EOFError, KeyboardInterrupt, SystemExit):
        return ACTION_END, None

    match = UNDO_INPUT_RE.match(user_input)
    if match is not None:
        return ACTION_UNDO, None

    match = WALL_INPUT_RE.match(user_input)
    if match is not None:
        direction, row, col = match.groups(0)
        return ACTION_MOVE, {
            'type': 'wall',
            'direction': INPUT_DIRECTIONS[direction],
            'position': Vector(
                row=int(row),
                col=COLUMN_LETTERS.find(col.lower())
            ),
        }

    match = MOVE_INPUT_RE.match(user_input)
    if match is not None:
        row, col = match.groups(0)
        return ACTION_MOVE, {
            'type': 'pawn',
            'position': Vector(
                row=int(row),
                col=COLUMN_LETTERS.find(col.lower())
            ),
        }

    match = QUIT_INPUT_RE.match(user_input)
    if match is not None:
        return ACTION_END, None

    return ACTION_UNKNOWN, None


def qlearn(with_clear=True):
    game = Quoridor2()
    rpwp = RandomPlayerWithPath(game)
    ql_player = QLPlayer(game)

    games_to_play = 5
    games_played = 0

    max_moves = 1000
    while games_to_play > games_played:
        current_state = game.initial_state()
        history = []
        moves = 0

        while max_moves > moves:
            if moves % 2 == 0:
                action = ql_player.play(current_state)
            else:
                action = rpwp.play(current_state)
            action_type, position = action
            previous_state = copy.deepcopy(current_state)
            game.execute_action(current_state, action)
            history.append(action)
            if (games_to_play - 1) == games_played:
                display_on_console(
                    current_state,
                    True,
                    history=history,
                    with_clear=with_clear,
                )
                time.sleep(0.1)
            ql_player.learn(previous_state, action, current_state)
            if game.is_terminal(current_state):
                break
            moves += 1

        games_played += 1
        print 'games_played:', games_played
    ql_player.save_Q()


def random_players(moves=None, with_clear=True):
    game = Quoridor2()
    state = game.initial_state()
    # rp = RandomPlayer(game)
    rpwp = RandomPlayerWithPath(game)
    if moves is None:
        moves = 1000
    history = []
    while moves > 0:
        action = rpwp.play(state)
        action_type, position = action
        game.execute_action(state, action)
        history.append(action)
        display_on_console(state, True, history=history, with_clear=with_clear)
        # print ACTION_TYPE[action_type](row=position.row, col=position.col)
        if game.is_terminal(state):
            break
        time.sleep(0.1)
        moves -= 1


def console_run(options):
    colors_on = options.colors_on
    if os.getenv('ANSI_COLORS_DISABLED') is not None:
        colors_on = False

    game = Quoridor2()
    state = game.initial_state()

    try:
        if options.random:
            random_players(with_clear=options.with_clear)
            return
        elif options.qlearn:
            qlearn(with_clear=options.with_clear)
            return
    except (EOFError, KeyboardInterrupt, SystemExit):
        pass
    finally:
        if traceback.format_exc() != 'None\n':
            traceback.print_exc()

    if options.example:
        random_pawn_positions(game, state)
        random_walls(game, state)
        display_on_console(state, colors_on, with_clear=options.with_clear)
        return

    message = None
    history = []
    while not game.is_terminal(state):
        display_on_console(
            state,
            colors_on,
            history=history,
            message=message,
            with_clear=options.with_clear,
        )
        message = None
        action_type, action_info = parse_input()
        if action_type == ACTION_END:
            break
        elif action_type == ACTION_UNDO:
            # print history
            if history:
                game.undo(state, history.pop())
            else:
                message = 'No history to undo.'
        elif action_type == ACTION_MOVE:
            try:
                action = (
                    action_info.get('direction'),
                    action_info['position']
                )
                if action_info['type'] == 'wall':
                    game.execute_action(state, action)
                    history.append(action)
                else:
                    history_position = current_pawn_position(state)
                    game.execute_action(state, action)
                    history.append((None, history_position))
            except InvalidMove as e:
                message = e.message
        else:
            # assert action_info['action'] == ACTION_UNKNOWN
            message = 'Wrong input. (Examples: wh1e, wv1e, p1e, 1e, quit, q)'

    if game.is_terminal(state):
        display_on_console(state, colors_on, with_clear=options.with_clear)
        print PLAYER_COLOR_NAME[FOLLOWING_PLAYER[state['on_move']]] + ' wins!'


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

    parser.add_option(
        '-r', '--random', dest='random', default=False, action='store_true',
        help=(
            'In console mode, play with random playes.'
        )
    )

    parser.add_option(
        '-w', '--withot-clear-console', dest='with_clear', default=True, action='store_false',
        help=(
            'Do not clear console on each move.'
        )
    )

    parser.add_option(
        '-q', '--qlearn', dest='qlearn', default=False, action='store_true',
        help=(
            'Train QPlayer.'
        )
    )

    options, args = parser.parse_args()
    console_run(options)


if __name__ == '__main__':
    main()
