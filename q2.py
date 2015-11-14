SIZE = 9
MIN_POS = 0
MAX_POS = SIZE - 1

VERTICAL = (0, 1)
HORIZONTAL = (1, 0)
DIRECTIONS = (VERTICAL, HORIZONTAL)

COL = 0
ROW = 1


def _adjacent_move_direction(from_, to):
    direction = (abs(from_[COL] - to[COL]), abs(from_[ROW] - to[ROW]))
    assert direction in DIRECTIONS, (from_, to)
    return direction


def is_within_board(position):
    return (
        position[COL] >= MIN_POS and position[COL] <= MAX_POS
    ) and (
        position[ROW] >= MIN_POS and position[ROW] <= MAX_POS
    )


def adjacent_spaces(position):
    assert is_within_board(position), position
    spaces = []
    if position[ROW] > MIN_POS:
        spaces.append((position[COL], position[ROW] - 1))
    if position[ROW] < MAX_POS:
        spaces.append((position[COL], position[ROW] + 1))

    if position[COL] > MIN_POS:
        spaces.append((position[COL] - 1, position[ROW]))
    if position[COL] < MAX_POS:
        spaces.append((position[COL] + 1, position[ROW]))
    return spaces
