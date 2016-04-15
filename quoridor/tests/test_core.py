# TODO: make test names more descriptive and apparent

from nose.tools import assert_true, assert_false, assert_equal, assert_raises
from nose.plugins.attrib import attr

from quoridor.core import (
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
    is_horizontal_wall_crossing,
    is_vertical_wall_crossing,
    InvalidMove,
    Quoridor2,
)


@attr('core')
def test_make_initial_state():
    assert_equal(
        (YELLOW, 4, 76, 10, 10, frozenset(), frozenset()),
        _make_initial_state(9)
    )


@attr('core')
def test_make_blocker_positions_2():
    assert_equal(
        {
            0: {1: set([0]), 2: set([0])},
            1: {2: set([0]), 3: set([0])},
            2: {0: set([0]), 1: set([0])},
            3: {0: set([0]), 3: set([0])},
        },
        _make_blocker_positions(2),
    )


@attr('core')
def test_make_blocker_positions_3():
    assert_equal(
        {
            0: {1: set([0]), 2: set([0])},
            1: {1: set([1]), 2: set([0, 1]), 3: set([0])},
            2: {2: set([1]), 3: set([1])},

            3: {0: set([0]), 1: set([0, 2]), 2: set([2])},
            4: {0: set([0, 1]), 1: set([1, 3]), 2: set([2, 3]), 3: set([0, 2])},
            5: {0: set([1]), 2: set([3]), 3: set([1, 3])},

            6: {0: set([2]), 1: set([2])},
            7: {0: set([2, 3]), 1: set([3]), 3: set([2])},
            8: {0: set([3]), 3: set([3])},
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
def test_is_horizontal_wall_crossing_true():
    argss = (
        (9, frozenset([55]), frozenset(), 55),
        (9, frozenset(), frozenset([61]), 61),
        (9, frozenset([4]), frozenset(), 5),
        (9, frozenset([22]), frozenset(), 21),
        (9, frozenset([11, 13]), frozenset(), 12),
        (9, frozenset([0]), frozenset([1]), 1),
        (9, frozenset([59, 61]), frozenset([60]), 60),
    )
    def check_true(args):
        assert_true(is_horizontal_wall_crossing(*args))

    for args in argss:
        yield check_true, args


@attr('core')
def test_is_horizontal_wall_crossing_false():
    argss = (
        (9, frozenset(), frozenset(), 23),
        (9, frozenset(), frozenset([1, 3]), 2),
    )
    def check_false(args):
        assert_false(is_horizontal_wall_crossing(*args))

    for args in argss:
        yield check_false, args


@attr('core')
def test_is_vertical_wall_crossing_true():
    argss = (
        (9, frozenset(), frozenset([13]), 13),
        (9, frozenset([27]), frozenset(), 27),
        (9, frozenset(), frozenset([31]), 39),
        (9, frozenset(), frozenset([41]), 33),
        (9, frozenset(), frozenset([8, 24]), 16),
        (9, frozenset([14]), frozenset([22]), 14),
        (9, frozenset([44]), frozenset([36, 52]), 44),
    )
    def check_true(args):
        assert_true(is_vertical_wall_crossing(*args))

    for args in argss:
        yield check_true, args


@attr('core')
def test_is_vertical_wall_crossing_false():
    argss = (
        (9, frozenset([10, 12, 14]), frozenset([9, 27]), 45),
    )
    def check_false(args):
        assert_false(is_vertical_wall_crossing(*args))

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

    state = state[:5] + (frozenset([6, 13]), frozenset([5, 14]))
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

    state = (GREEN, 29, 30, 8, 9, frozenset([26]), frozenset([10, 16]))
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

    state = (YELLOW, 17, 8, 10, 9, frozenset(), frozenset([7]))
    for i in range(12):
        if i == DOWN:
            assert_true(game.is_valid_pawn_move(state, i))
        else:
            assert_false(game.is_valid_pawn_move(state, i))


@attr('core')
def test_game_player_can_reach_goal():
    game = Quoridor2(board_size=9)

    state = game.initial_state()
    assert_true(game.player_can_reach_goal(state, YELLOW))
    assert_true(game.player_can_reach_goal(state, GREEN))

    state = (
        YELLOW, 40, 31, 7, 7, frozenset([31, 32, 34, 36, 38]), frozenset([39])
    )
    assert_false(game.player_can_reach_goal(state, YELLOW))
    assert_true(game.player_can_reach_goal(state, GREEN))


@attr('core', 'now')
def test_game_players_can_reach_goal():
    game = Quoridor2(board_size=9)

    state = game.initial_state()
    assert_true(game.players_can_reach_goal(state))

    state = (YELLOW, 11, 20, 8, 8, frozenset([1, 18]), frozenset([9, 10]))
    assert_false(game.players_can_reach_goal(state))


@attr('core')
def test_game_is_terminal():
    game = Quoridor2(board_size=9)

    state = game.initial_state()
    assert_false(game.is_terminal(state))

    state = (GREEN, 77, 65, 9, 8, frozenset([26]), frozenset([19, 32]))
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
        YELLOW, 27, 62, 3, 3,
        frozenset((1, 3, 5, 7, 53, 55, 56, 58, 60, 62)),
        frozenset((0, 16, 32, 46))
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
