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
