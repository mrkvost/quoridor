# TODO: make test names more descriptive and apparent

from nose.tools import assert_true, assert_false, assert_equal, assert_raises
from nose.plugins.attrib import attr

from quoridor.core.game import (
    YELLOW,
    GREEN,
    VERTICAL,
    HORIZONTAL,
    UP,
    RIGHT,
    DOWN,
    LEFT,
    _make_initial_state,
    _make_blocker_positions,
    _make_goal_positions,
    _make_move_deltas,
    InvalidMove,
    Quoridor2,
)


@attr('core')
def test_make_initial_state():
    assert_equal((YELLOW, 4, 76, 10, 10, frozenset()), _make_initial_state(9))


@attr('core')
def test_make_blocker_positions_2():
    assert_equal(
        {
            0: {1: set([1]), 2: set([0])},
            1: {2: set([0]), 3: set([1])},
            2: {0: set([0]), 1: set([1])},
            3: {0: set([0]), 3: set([1])},
        },
        _make_blocker_positions(2),
    )


@attr('core')
def test_make_blocker_positions_3():
    assert_equal(
        {
            0: {1: set([4]), 2: set([0])},
            1: {1: set([5]), 2: set([0, 1]), 3: set([4])},
            2: {2: set([1]), 3: set([5])},

            3: {0: set([0]), 1: set([4, 6]), 2: set([2])},
            4: {
                0: set([0, 1]),
                1: set([5, 7]),
                2: set([2, 3]),
                3: set([4, 6])
            },
            5: {0: set([1]), 2: set([3]), 3: set([5, 7])},

            6: {0: set([2]), 1: set([6])},
            7: {0: set([2, 3]), 1: set([7]), 3: set([6])},
            8: {0: set([3]), 3: set([7])},
        },
        _make_blocker_positions(3),
    )


@attr('core')
def test_make_goal_positions_3():
    assert_equal(
        {YELLOW: frozenset([6, 7, 8]), GREEN: frozenset([0, 1, 2])},
        _make_goal_positions(3)
    )


@attr('core')
def test_make_goal_positions_9():
    assert_equal(
        {
            YELLOW: frozenset([72, 73, 74, 75, 76, 77, 78, 79, 80]),
            GREEN: frozenset([0, 1, 2, 3, 4, 5, 6, 7, 8]),
        },
        _make_goal_positions(9)
    )


@attr('core')
def test_make_move_deltas_4():
    assert_equal(
        {UP: -4, RIGHT: +1, DOWN: +4, LEFT: -1},
        _make_move_deltas(4)
    )


@attr('core')
def test_make_move_deltas_9():
    assert_equal(
        {UP: -9, RIGHT: +1, DOWN: +9, LEFT: -1},
        _make_move_deltas(9)
    )


@attr('core')
def test_game_is_wall_crossing_9_true():
    game = Quoridor2(board_size=9)
    argss = (
        (frozenset([55]), 55),
        (frozenset([64 + 61]), 61),
        (frozenset([4]), 5),
        (frozenset([22]), 21),
        (frozenset([11, 13]), 12),
        (frozenset([0, 64 + 1]), 1),
        (frozenset([59, 61, 64 + 60]), 60),
        (frozenset([64 + 13]), 13),
        (frozenset([27]), 27),
        (frozenset([64 + 31]), 64 + 39),
        (frozenset([64 + 41]), 64 + 33),
        (frozenset([64 + 8, 64 + 24]), 64 + 16),
        (frozenset([14, 64 + 22]), 64 + 14),
        (frozenset([44, 64 + 36, 64 + 52]), 64 + 44),
    )
    def check_true(args):
        assert_true(game.is_wall_crossing(*args))

    for args in argss:
        yield check_true, args


@attr('core')
def test_game_is_wall_crossing_9_false():
    game = Quoridor2(board_size=9)
    argss = (
        (frozenset(), 23),
        (frozenset([64 + 1, 64 + 3]), 2),
        (frozenset([10, 12, 14, 64 + 9, 64 + 27]), 45),
    )
    def check_false(args):
        assert_false(game.is_wall_crossing(*args))

    for args in argss:
        yield check_false, args


@attr('core')
def test_game_is_move_impossible():
    game = Quoridor2(board_size=9)
    state = game.initial_state()

    assert_true(game.is_move_impossible(state, 0, UP))
    assert_true(game.is_move_impossible(state, 0, LEFT))
    assert_true(game.is_move_impossible(state, 80, DOWN))
    assert_true(game.is_move_impossible(state, 80, RIGHT))

    assert_false(game.is_move_impossible(state, 10, UP))
    assert_false(game.is_move_impossible(state, 10, LEFT))
    assert_false(game.is_move_impossible(state, 10, DOWN))
    assert_false(game.is_move_impossible(state, 10, RIGHT))

    state = state[:5] + (frozenset([6, 13, 64 + 5, 64 + 14]), )
    assert_true(game.is_move_impossible(state, 15, UP))
    assert_true(game.is_move_impossible(state, 15, LEFT))
    assert_true(game.is_move_impossible(state, 15, DOWN))
    assert_true(game.is_move_impossible(state, 15, RIGHT))

    assert_false(game.is_move_impossible(state, 32, UP))
    assert_false(game.is_move_impossible(state, 32, LEFT))
    assert_false(game.is_move_impossible(state, 32, DOWN))
    assert_false(game.is_move_impossible(state, 32, RIGHT))


@attr('core')
def test_game_is_valid_pawn_move():
    game = Quoridor2(board_size=9)
    state = game.initial_state()

    assert_false(game.is_valid_pawn_move(state, 100))
    assert_false(game.is_valid_pawn_move(state, -2))
    assert_false(game.is_valid_pawn_move(state, UP))
    assert_true(game.is_valid_pawn_move(state, RIGHT))
    assert_true(game.is_valid_pawn_move(state, DOWN))
    assert_true(game.is_valid_pawn_move(state, LEFT))

    for i in range(4, 12):  # in the begenning, no jump should be possible
        assert_false(game.is_valid_pawn_move(state, i))

    state = (GREEN, 29, 30, 8, 9, frozenset([26, 64 + 10, 64 + 16]))
    assert_true(game.is_valid_pawn_move(state, UP))
    assert_true(game.is_valid_pawn_move(state, RIGHT))
    assert_false(game.is_valid_pawn_move(state, DOWN))
    assert_false(game.is_valid_pawn_move(state, LEFT))
    assert_false(game.is_valid_pawn_move(state, 4))
    assert_false(game.is_valid_pawn_move(state, 5))
    assert_false(game.is_valid_pawn_move(state, 6))
    assert_true(game.is_valid_pawn_move(state, 7))
    assert_false(game.is_valid_pawn_move(state, 8))
    assert_true(game.is_valid_pawn_move(state, 9))
    assert_false(game.is_valid_pawn_move(state, 10))
    assert_false(game.is_valid_pawn_move(state, 11))

    state = (YELLOW, 17, 8, 10, 9, frozenset([64 + 7]))
    for i in range(12):
        if i == DOWN:
            assert_true(game.is_valid_pawn_move(state, i))
        else:
            assert_false(game.is_valid_pawn_move(state, i))


@attr('core')
def test_game_shortest_path():
    game = Quoridor2(board_size=9)

    state = game.initial_state()
    path = game.shortest_path(state, YELLOW)
    assert_true(path is not None)
    assert_equal(len(path), 9)
    path = game.shortest_path(state, GREEN)
    assert_true(path is not None)
    assert_equal(len(path), 9)

    state = (YELLOW, 40, 31, 7, 7, frozenset([31, 32, 34, 36, 38, 64 + 39]))
    assert_true(game.shortest_path(state, YELLOW) is None)

    path = game.shortest_path(state, GREEN)
    assert_true(path is not None)
    assert_equal(len(path), 4)


@attr('core')
def test_game_players_can_reach_goal():
    game = Quoridor2(board_size=9)

    state = game.initial_state()
    assert_true(game.players_can_reach_goal(state))

    state = (YELLOW, 11, 20, 8, 8, frozenset([1, 18, 64 + 9, 64 + 10]))
    assert_false(game.players_can_reach_goal(state))


@attr('core')
def test_game_is_terminal():
    game = Quoridor2(board_size=9)

    state = game.initial_state()
    assert_false(game.is_terminal(state))

    state = (GREEN, 77, 65, 9, 8, frozenset([26, 64 + 19, 64 + 32]))
    assert_true(game.is_terminal(state))


@attr('core')
def test_game_execute_action_exceptions():
    game = Quoridor2(board_size=9)

    def check_exception(state, actions, message):
        for action in actions:
            with assert_raises(InvalidMove) as e:
                # print '\n\naction:', action
                # print 'state:', state
                new_state = game.execute_action(state, action)
                # print '\nnew_state:', new_state
            assert_equal(str(e.exception), message.format(action=action))

    state = game.initial_state()
    check_exception(state, (23442, -13), 'Unknown action {action}!')
    check_exception(state, range(132, 140), 'Pawn cannot move there!')

    state = (GREEN, 33, 61, 10, 0, frozenset(), frozenset())
    check_exception(state, range(128), 'Not enough walls!')

    state = (
        YELLOW, 27, 62, 3, 3, frozenset((1, 3, 5, 7, 53, 55, 56, 58, 60, 62,
                                         64, 80, 96, 110))
    )

    horizontal = tuple(range(8)) + (16, 32, 46) + tuple(range(52, 64))
    vertical = (
        64, 65, 67, 69, 71, 72, 80, 88, 96, 102, 104, 110, 117, 118, 119, 120,
        122, 124, 126
    )

    check_exception(
        state,
        horizontal + vertical,
        'Wall crosses already placed walls!'
    )

    check_exception(
        state,
         #                    48,  52,  61,  63
         (8, 24, 39, 40, 47, 112, 116, 125, 127),
        'Pawn can not reach the goal!'
    )
    check_exception(state, (129, 131), 'Pawn cannot move there!')
    check_exception(
        (GREEN, ) + state[1:],
        (129, 130),
        'Pawn cannot move there!'
    )
