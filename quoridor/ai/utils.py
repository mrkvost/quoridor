import itertools


def binarify(number, length):
    return [int(digit) for digit in bin(number)[2:].zfill(length)]
    # binary = []
    # for i in range(length):
    #     number, mod = divmod(number, 2)

def input_vector_from_game_state(context):
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
