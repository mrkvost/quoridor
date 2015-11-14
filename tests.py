from nose.tools import (
    assert_true, assert_false, assert_equal, raises,
)

from q2 import (
    VERTICAL,
    HORIZONTAL,
    _adjacent_move_direction,
    pawn_within_board,
    adjacent_pawn_positions,
    wall_within_board,
)


@raises(AssertionError)
def test_adjacent_move_direction_wrong_1():
    _adjacent_move_direction([0, 0], [0, 0])


@raises(AssertionError)
def test_adjacent_move_direction_wrong_2():
    _adjacent_move_direction([0, 0], [3, 3])


@raises(AssertionError)
def test_adjacent_move_direction_wrong_3():
    _adjacent_move_direction([5, 2], [0, 2])


def test_adjacent_move_direction_vertical_1():
    assert_equal(_adjacent_move_direction([0, 0], [0, 1]), VERTICAL)


def test_adjacent_move_direction_vertical_2():
    assert_equal(_adjacent_move_direction([5, 7], [5, 6]), VERTICAL)


def test_adjacent_move_direction_horizontal_1():
    assert_equal(_adjacent_move_direction([3, 8], [2, 8]), HORIZONTAL)


def test_adjacent_move_direction_horizontal_2():
    assert_equal(_adjacent_move_direction([7, 0], [8, 0]), HORIZONTAL)


def test_pawn_within_board_wrong_1():
    assert_false(pawn_within_board([-1, 0]))


def test_pawn_within_board_wrong_2():
    assert_false(pawn_within_board([1, 257]))


def test_pawn_within_board_wrong_3():
    assert_false(pawn_within_board([2147483649, -2147483649]))


def test_pawn_within_board_correct_1():
    assert_true(pawn_within_board([0, 0]))


def test_pawn_within_board_correct_2():
    assert_true(pawn_within_board([3, 7]))


def test_pawn_within_board_correct_3():
    assert_true(pawn_within_board([8, 8]))


def test_adjacent_pawn_positions_left_top_corner():
    expected = set([(0, 1), (1, 0)])
    assert_equal(set(adjacent_pawn_positions((0, 0))), expected)


def test_adjacent_pawn_positions_right_bottom_corner():
    expected = set([(8, 7), (7, 8)])
    assert_equal(set(adjacent_pawn_positions((8, 8))), expected)


def test_adjacent_pawn_positions_right_side():
    expected = set([(8, 2), (8, 4), (7, 3)])
    assert_equal(set(adjacent_pawn_positions((8, 3))), expected)


def test_adjacent_pawn_positions_middle():
    expected = set([(3, 4), (4, 3), (5, 4), (4, 5)])
    assert_equal(set(adjacent_pawn_positions((4, 4))), expected)


def test_wall_within_board_wrong_1():
    assert_false(wall_within_board([0, -1]))


def test_wall_within_board_wrong_2():
    assert_false(wall_within_board([65538, -1]))


def test_wall_within_board_wrong_3():
    assert_false(wall_within_board([-4294967296, 4294967296]))


def test_wall_within_board_correct_1():
    assert_true(pawn_within_board([0, 0]))


def test_wall_within_board_correct_2():
    assert_true(pawn_within_board([0, 7]))


def test_wall_within_board_correct_3():
    assert_true(pawn_within_board([5, 4]))


def test_wall_within_board_correct_4():
    assert_true(pawn_within_board([7, 7]))
