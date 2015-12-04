# TODO: documentation

from collections import namedtuple, deque


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
PLAYER_COLOR_NAME = {YELLOW: 'Yellow', GREEN: 'Green'}

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
            'moves_made': 0,
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

    @property
    def moves_made(self):
        return self._state['moves_made']

    @property
    def on_move(self):
        return self._state['on_move']

    def player_wall_count(self, color):
        return self._state['players'][color]['walls']

    @property
    def players(self):
        return [color for color in self._state['players']]

    @property
    def game_ended(self):
        return self._state['game_ended']

    @property
    def winner(self):
        return self._state['winner']

    @property
    def current_wall_count(self):
        return self.player_wall_count(self.on_move)

    def pawn_distance_from_goal(self, color):
        starting_position = self.pawn_position(color)
        goal_row = GOAL_ROW[color]
        walls = self._state['walls']

        to_visit = deque([(starting_position, 0)])
        visited = set()

        while to_visit:
            position, distance = to_visit.popleft()
            if position in visited:
                continue
            if position.row == goal_row:
                return distance
            visited.add(position)

            right_distance = distance % 2 == int(color == self.on_move)
            for possible in adjacent_pawn_spaces_not_blocked(position, walls):
                jumps = right_distance and possible in self._state['pawns']
                if jumps:
                    to_visit.append((possible, distance))
                else:
                    to_visit.append((possible, distance + 1))

        error_msg_fmt = u'{color_name} player can not reach goal row!'
        color_name = PLAYER_COLOR_NAME[color].upper()
        raise Exception(error_msg_fmt.format(color_name=color_name))


    def place_wall(self, direction, position):
        if self.game_ended:
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

        color = self.on_move
        self._state['walls'][direction].add(position)
        self._state['players'][color]['walls'] -= 1
        self._state['on_move'] = FOLLOWING_PLAYER[color]
        self._state['moves_made'] += 1

    def pawn_position(self, color):
        return self._state['players'][color]['pawn']

    @property
    def current_pawn_position(self):
        return self.pawn_position(self.on_move)

    def move_pawn(self, new_position):
        if self.game_ended:
            raise InvalidMove('Game already ended.')

        pawn_position = self.current_pawn_position
        is_correct = is_correct_pawn_move(
            pawn_position,
            new_position,
            self._state['pawns'],
            self._state['walls']
        )

        if not is_correct:
            raise InvalidMove()

        color = self.on_move
        self._state['players'][color]['pawn'] = new_position
        del self._state['pawns'][pawn_position]
        self._state['pawns'][new_position] = color
        # Check end of the game...
        if new_position[ROW] == GOAL_ROW[color]:
            self._state['game_ended'] = True
            self._state['winner'] = color

        self._state['on_move'] = FOLLOWING_PLAYER[color]
        self._state['moves_made'] += 1

    @property
    def pawns(self):
        return self._state['pawns']

    @property
    def walls(self):
        return self._state['walls']
