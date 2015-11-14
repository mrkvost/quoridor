SIZE = 9
MIN_PAWN_POS = 0
MAX_PAWN_POS = SIZE - 1
MIN_WALL_POS = 0
MAX_WALL_POS = SIZE - 2

VERTICAL = (0, 1)
HORIZONTAL = (1, 0)
DIRECTIONS = (VERTICAL, HORIZONTAL)

COL = 0
ROW = 1


def _adjacent_move_direction(from_, to):
    direction = (abs(from_[COL] - to[COL]), abs(from_[ROW] - to[ROW]))
    assert direction in DIRECTIONS, (from_, to)
    return direction


def pawn_within_board(position):
    return MIN_PAWN_POS <= position[COL] <= MAX_PAWN_POS and (
        MIN_PAWN_POS <= position[ROW] <= MAX_PAWN_POS
    )


def adjacent_pawn_positions(position):
    assert pawn_within_board(position), position
    spaces = []
    if position[ROW] > MIN_PAWN_POS:
        spaces.append((position[COL], position[ROW] - 1))
    if position[ROW] < MAX_PAWN_POS:
        spaces.append((position[COL], position[ROW] + 1))

    if position[COL] > MIN_PAWN_POS:
        spaces.append((position[COL] - 1, position[ROW]))
    if position[COL] < MAX_PAWN_POS:
        spaces.append((position[COL] + 1, position[ROW]))
    return spaces


def wall_within_board(position):
    return MIN_WALL_POS <= position[COL] <= MAX_WALL_POS and (
        MIN_WALL_POS <= position[ROW] <= MAX_WALL_POS
    )
