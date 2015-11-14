VERTICAL = (0, 1)
HORIZONTAL = (1, 0)
DIRECTIONS = (VERTICAL, HORIZONTAL)


def _adjacent_move_direction(from_, to):
    direction = (abs(from_[0] - to[0]), abs(from_[1] - to[1]))
    assert direction in DIRECTIONS, (from_, to)
    return direction
