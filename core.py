# TODO: documentation

import collections


Vector = collections.namedtuple('Vector', ['row', 'col'])
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
ORTOGONAL_DIRECTION = {VERTICAL: HORIZONTAL, HORIZONTAL: VERTICAL}

# It is possible to jump over single pawn
JUMP_DISTANCE_MAX = 2

STARTING_POSITION_DEFAULT_YELLOW = Vector(row=PAWN_POS_MIN, col=4)
STARTING_POSITION_DEFAULT_GREEN = Vector(row=PAWN_POS_MAX, col=4)
STARTING_WALL_COUNT_2_PLAYERS = 10

YELLOW = 0
GREEN = 1
PLAYER_COLOR_NAME = {YELLOW: 'Yellow', GREEN: 'Green'}

GOAL_ROW = {
    YELLOW: PAWN_POS_MAX,
    GREEN: PAWN_POS_MIN,
}
FOLLOWING_PLAYER = {YELLOW: GREEN, GREEN: YELLOW}

PAWN_POSITIONS_COUNT = BOARD_SIZE ** 2
WALL_POSITIONS_COUNT = WALL_BOARD_SIZE ** 2
ALL_PAWN_POSITIONS = frozenset([
    Vector(row=i // BOARD_SIZE, col=i % BOARD_SIZE)
    for i in range(PAWN_POSITIONS_COUNT)
])
ALL_WALL_POSITIONS = frozenset([
    Vector(row=i // WALL_BOARD_SIZE, col=i % WALL_BOARD_SIZE)
    for i in range(WALL_POSITIONS_COUNT)
])


def add_direction(position, direction):
    return Vector(
        row=position.row + direction.row,
        col=position.col + direction.col,
    )


def substract_direction(position, direction):
    return Vector(
        row=position.row - direction.row,
        col=position.col - direction.col,
    )


def adjacent_move_direction(from_, to):
    direction = Vector(
        row=abs(from_.row - to.row),
        col=abs(from_.col - to.col),
    )
    if direction not in DIRECTIONS:
        return None
    return direction


def pawn_move_distance_no_walls(from_, to):
    return abs(from_.col - to.col) + abs(from_.row - to.row)


def pawn_within_board(position):
    return PAWN_POS_MIN <= position.col <= PAWN_POS_MAX and (
        PAWN_POS_MIN <= position.row <= PAWN_POS_MAX
    )


def is_occupied(state, position):
    return position in state['pawns'].values()


def adjacent_spaces(position):
    if not pawn_within_board(position):
        return
    if position.row > PAWN_POS_MIN:
        yield substract_direction(position, VERTICAL)
    if position.row < PAWN_POS_MAX:
        yield add_direction(position, VERTICAL)

    if position.col > PAWN_POS_MIN:
        yield substract_direction(position, HORIZONTAL)
    if position.col < PAWN_POS_MAX:
        yield add_direction(position, HORIZONTAL)


def is_wall_between(state, from_, to):
    direction = adjacent_move_direction(from_, to)
    if direction is None:
        return None     # TODO: think, whether exception here would be better
    else:
        direction = ORTOGONAL_DIRECTION[direction]

    position = Vector(
        row=min(from_.row, to.row),
        col=min(from_.col, to.col),
    )

    if position in state['placed_walls'][direction]:
        return True
    elif substract_direction(position, direction) in state['placed_walls'][direction]:
        return True

    return False


def adjacent_spaces_not_blocked(state, pawn_position):
    for adjacent_space in adjacent_spaces(pawn_position):
        if not is_wall_between(state, pawn_position, adjacent_space):
            yield adjacent_space


def pawn_legal_moves(state, pawn_position):
    for adjacent_position in adjacent_spaces_not_blocked(state, pawn_position):
        if is_occupied(state, adjacent_position):
            jumps = adjacent_spaces_not_blocked(state, adjacent_position)
            for jump in jumps:
                if jump != pawn_position:
                    yield jump
        else:
            yield adjacent_position


def is_correct_pawn_move(state, from_, to):
    return to in pawn_legal_moves(state, from_)


def wall_within_board(position):
    return WALL_POS_MIN <= position.col <= WALL_POS_MAX and (
        WALL_POS_MIN <= position.row <= WALL_POS_MAX
    )


def wall_intersects(state, direction, position):
    return (
        (position in state['placed_walls'][direction]) or
        (position in state['placed_walls'][ORTOGONAL_DIRECTION[direction]]) or
        (add_direction(position, direction) in state['placed_walls'][direction]) or
        (substract_direction(position, direction) in state['placed_walls'][direction])
    )


def player_can_reach_goal(state, player):
    to_visit = set([state['pawns'][player]])
    visited = set()
    while to_visit:
        position = to_visit.pop()
        if position.row == GOAL_ROW[player]:
            return True
        visited.add(position)
        for new_position in adjacent_spaces_not_blocked(state, position):
            if new_position not in visited:
                to_visit.add(new_position)
    return False


def is_correct_wall_move(state, direction, wall_position, raise_errors=False):
    if not wall_within_board(wall_position):
        if raise_errors:
            raise InvalidMove('Position is not within board.')
        return False
    elif wall_intersects(state, direction, wall_position):
        if raise_errors:
            raise InvalidMove('Wall would intersect already placed walls.')
        return False

    # wall intersects ensures that the position is not used
    state['placed_walls'][direction].add(wall_position)

    for player, pawn_position in state['pawns'].items():
        if not player_can_reach_goal(state, player):
            state['placed_walls'][direction].remove(wall_position)
            if raise_errors:
                raise InvalidMove(
                    'Player {player} would not be able to reach goal.'.format(
                        player=PLAYER_COLOR_NAME[player],
                    )
                )
            return False

    state['placed_walls'][direction].remove(wall_position)
    return True


def current_pawn_position(state):
    return state['pawns'][state['on_move']]


def following_pawn_position(state):
    return state['pawns'][FOLLOWING_PLAYER[state['on_move']]]


def wall_affects(state, direction, wall_position):
    yield direction, wall_position
    yield direction, add_direction(wall_position, direction)
    yield direction, substract_direction(wall_position, direction)
    yield ORTOGONAL_DIRECTION[direction], wall_position


def wall_legal_moves(state):
    if not state['walls'][state['on_move']]:
        return
    # TODO: what to do with leaving the paths to goals?
    result_walls = {
        HORIZONTAL: set(ALL_WALL_POSITIONS),
        VERTICAL: set(ALL_WALL_POSITIONS),
    }
    for dimension, walls in state['placed_walls'].items():
        for position in walls:
            affected = wall_affects(state, dimension, position)
            for direction, position in affected:
                result_walls[direction].discard(position)

    for direction, walls in result_walls.items():
        for wall in walls:
            yield (direction, wall)


class Quoridor2(object):

    def initial_state(self):
        return {
            'on_move': YELLOW,
            'pawns': {
                YELLOW: STARTING_POSITION_DEFAULT_YELLOW,
                GREEN: STARTING_POSITION_DEFAULT_GREEN,
            },
            'walls': {
                YELLOW: STARTING_WALL_COUNT_2_PLAYERS,
                GREEN: STARTING_WALL_COUNT_2_PLAYERS,
            },
            'placed_walls': {
                HORIZONTAL: set(),
                VERTICAL: set(),
            },
            'utility': 0,
        }

    def players(self, state):
        pass  # TODO: what here? is this necessary?

    def actions(self, state):
        for position in pawn_legal_moves(state, current_pawn_position(state)):
            yield (None, position)

        for action in wall_legal_moves(state):
            yield action

    def is_terminal(self, state):
        for player, pawn_position in state['pawns'].items():
            if pawn_position.row == GOAL_ROW[player]:
                return True
        return False

    def utility(self, state, player):
        return PLAYER_UTILITIES[player] * state['utility']

    def execute_action(self, state, action):
        direction, new_position = action
        if direction is None:
            current_position = current_pawn_position(state)
            if not is_correct_pawn_move(state, current_position, new_position):
                msg_fmt = (
                    '{color} pawn cannot move here. (row={row}, col={col})'
                )
                raise InvalidMove(msg_fmt.format(
                    color=PLAYER_COLOR_NAME[state['on_move']],
                    row=new_position.row,
                    col=new_position.col,
                ))
            state['pawns'][state['on_move']] = new_position
            if self.is_terminal(state):
                state['utility'] = 1
        else:
            if state['walls'][state['on_move']] < 1:
                raise InvalidMove('Not enough walls to play.')
            is_correct_wall_move(state, direction, new_position, True)
            state['placed_walls'][direction].add(new_position)
            state['walls'][state['on_move']] -= 1
        state['on_move'] = FOLLOWING_PLAYER[state['on_move']]

    def undo(self, state, action):
        direction, position = action
        last_player = FOLLOWING_PLAYER[state['on_move']]
        if direction is None:
            pawn_position = state['pawns'][last_player]
            if not is_correct_pawn_move(state, pawn_position, position):
                raise InvalidMove('Incorrect undo move.')
            state['pawns'][last_player] = position
        else:
            if position not in state['placed_walls'][direction]:
                raise InvalidMove('Incorrect undo move.')
            state['placed_walls'][direction].remove(position)
            state['walls'][last_player] += 1
        state['on_move'] = last_player


class InvalidMove(Exception):
    pass
