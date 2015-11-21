# TODO: documentation

from collections import namedtuple


Vector = namedtuple('Vector', ['row', 'col'])
ROW = 0
COL = 1

BOARD_SIZE = 9
PAWN_POS_MIN = 0
PAWN_POS_MAX = BOARD_SIZE - 1

WALL_BOARD_SIZE = BOARD_SIZE - 1
WALL_POS_MIN = 0
WALL_POS_MAX = WALL_BOARD_SIZE - 1

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
