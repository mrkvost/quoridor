import itertools
import copy


def binarify(number, length):
    return [int(digit) for digit in bin(number)[2:].zfill(length)]


def old_input_vector_from_game_state(context):
    """
    WARNING: works properly for maximum board size 11

    1: player on the move
    2...8: yellow player position in binary (0, 1, ..., 80)
    9...15: green player position in binary
    16...19: yellow player walls stock in binary (0, ..., 10)
    20...23: gren player walls stock in binary

    24...87: horizonal walls in binary
    88...151: vecrical walls in binary
    """

    state = context.state
    # TODO: add shortest path lengths for both players?
    return itertools.chain(
        (state[0], ),
        binarify(state[1], 7),
        binarify(state[2], 7),
        binarify(state[3], 4),
        binarify(state[4], 4),
        [int(i in state[5]) for i in range(context.game.wall_moves)],
    )


POSITIONS = [0] * 81


def input_vector_from_game_state_fast(context):
    state = context.state
    positions = copy.copy(POSITIONS)
    positions[state[1]] = 1
    positions[state[2]] = -1
    return itertools.chain(
        (state[0], ),
        positions,
        binarify(state[3], 4),
        binarify(state[4], 4),
        [int(i in state[5]) for i in range(context.game.wall_moves)],
    )


def input_vector_from_game_state(context, repeat=1):
    state = context.state
    positions = POSITIONS * repeat
    for i in range(repeat):
        positions[state[1] * repeat + i] = 1
        positions[state[2] * repeat + i] = -1

    return itertools.chain(
        (state[0], ),
        positions,
        binarify(state[3], 4),
        binarify(state[4], 4),
        [int(i in state[5]) for i in range(context.game.wall_moves)],
    )
