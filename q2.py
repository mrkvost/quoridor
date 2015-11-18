# TODO: documentation

SIZE = 9
PAWN_POS_MIN = 0
PAWN_POS_MAX = SIZE - 1
WALL_POS_MIN = 0
WALL_POS_MAX = SIZE - 2

VERTICAL = (0, 1)
HORIZONTAL = (1, 0)
DIRECTIONS = (VERTICAL, HORIZONTAL)
OPPOSITE_DIRECTION = {VERTICAL: HORIZONTAL, HORIZONTAL: VERTICAL}

# It is possible to jump over single pawn
JUMP_DISTANCE_MAX = 2

COL = 0
ROW = 1

RED = 0
GREEN = 1

GOAL_ROW = {
    RED: PAWN_POS_MAX,
    GREEN: PAWN_POS_MIN,
}
FOLLOWING_PLAYER = {RED: GREEN, GREEN: RED}


def add_direction(position, direction):
    return (position[COL] + direction[COL], position[ROW] + direction[ROW])


def substract_direction(position, direction):
    return (position[COL] - direction[COL], position[ROW] - direction[ROW])


def adjacent_move_direction(from_, to):
    direction = (abs(from_[COL] - to[COL]), abs(from_[ROW] - to[ROW]))
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

    position = (min(from_[COL], to[COL]), min(from_[ROW], to[ROW]))

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
    for color, pawn_position in pawns.items():
        if not pawn_can_reach_goal(color, pawn_position, walls):
            return False
    return True


class InvalidMove(Exception):
    pass


class Quoridor2(object):

    def __init__(self):
        self._state = {
            'winner': None,
            'game_ended': False,
            'on_move': RED,
            'players': {
                RED: {
                    'pawn': (4, PAWN_POS_MIN),
                    'walls': 10,
                },
                GREEN: {
                    'pawn': (4, PAWN_POS_MAX),
                    'walls': 10,
                },
            },
            'pawns': {
                (4, PAWN_POS_MIN): RED,
                (4, PAWN_POS_MAX): GREEN,
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
        return self._state['pawns'][self._state['on_move']]['walls']

    def place_wall(self, direction, position):
        if self.game_ended():
            raise InvalidMove('Game already ended.')

        if not self.current_wall_count > 0:
            raise InvalidMove('No walls to play with.')

        is_correct = is_correct_pawn_move(
            direction,
            position,
            self._state['pawns'],
            self._state['walls']
        )

        if not is_correct:
            # TODO: reason the move is invalid would be nice, e.g. no path...
            raise InvalidMove()

        color = self._state['on_move']
        self._state['wals'][direction].add(position)
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


def wall_to_base(direction, position, base):
    cm, rm = 8, 4
    boc = direction[1] * cm + direction[0]
    bor = direction[0] * rm + direction[1]
    col = position[COL] * cm
    row = position[ROW] * rm

    if direction == HORIZONTAL:
        for col_delta in range(15):
            base[(boc + col + col_delta, bor + row)] = u'\u2550'
    else:
        for row_delta in range(7):
            base[(boc + col, bor + row + row_delta)] = u'\u2551'


from termcolor import colored


def pawn_to_base(position, color, base):
    LETTER = {RED: u'Y', GREEN: u'G'}
    cm, rm = 8, 4
    col = position[COL] * cm + 1
    row = position[ROW] * rm + 1
    base.update({
        (col + 1, row): u'\u27cb',
        (col + 2, row): u'\u203e',
        (col + 3, row): u'\u203e',
        (col + 4, row): u'\u203e',
        (col + 5, row): u'\u27cd',

        (col + 1, row + 1): u'\u23b8',
        (col + 2, row + 1): LETTER[color],
        (col + 3, row + 1): LETTER[color],
        (col + 4, row + 1): LETTER[color],
        (col + 5, row + 1): u'\u23b9',

        (col + 1, row + 2): u'\u27cd',
        (col + 2, row + 2): u'_',
        (col + 3, row + 2): u'_',
        (col + 4, row + 2): u'_',
        (col + 5, row + 2): u'\u27cb',
    })


def main():
    game = Quoridor2()
    while not game.game_ended():
        base = make_base()
        for direction, walls in game.walls.items():
            for wall in walls:
                wall_to_base(direction, wall, base)
        for pawn, color in game.pawns.items():
            pawn_to_base(pawn, color, base)

        print_base(base)
        break   # TODO: TO BE REMOVED


if __name__ == '__main__':
    main()
