# TODO: documentation

SIZE = 9
PAWN_POS_MIN = 0
PAWN_POS_MAX = SIZE - 1
WALL_POS_MIN = 0
WALL_POS_MAX = SIZE - 2

VERTICAL = (0, 1)
HORIZONTAL = (1, 0)
DIRECTIONS = (VERTICAL, HORIZONTAL)

# It is possible to jump over single pawn
JUMP_DISTANCE_MAX = 2

COL = 0
ROW = 1

RED = 0
GREEN = 1


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
        spaces.append((position[COL], position[ROW] - 1))
    if position[ROW] < PAWN_POS_MAX:
        spaces.append((position[COL], position[ROW] + 1))

    if position[COL] > PAWN_POS_MIN:
        spaces.append((position[COL] - 1, position[ROW]))
    if position[COL] < PAWN_POS_MAX:
        spaces.append((position[COL] + 1, position[ROW]))
    return spaces


def is_wall_between(from_, to, walls):
    direction = adjacent_move_direction(from_, to)
    if direction is None:
        return None     # TODO: think, whether exception here would be better
    elif VERTICAL == direction:
        direction = HORIZONTAL
    else:
        direction = VERTICAL

    col = min(from_[COL], to[COL])
    row = min(from_[ROW], to[ROW])

    if (col, row) in walls[direction]:
        return True
    elif (col - direction[COL], row - direction[ROW]) in walls[direction]:
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
