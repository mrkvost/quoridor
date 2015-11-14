from nose.tools import (
    assert_equal, raises,
)

from q2 import (
    VERTICAL,
    HORIZONTAL,
    _adjacent_move_direction,
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


def test_adjacent_move_direction_vertical():
    assert_equal(_adjacent_move_direction([0, 0], [0, 1]), VERTICAL)
    assert_equal(_adjacent_move_direction([5, 7], [5, 6]), VERTICAL)
    assert_equal(_adjacent_move_direction([3, 8], [2, 8]), HORIZONTAL)
    assert_equal(_adjacent_move_direction([7, 0], [8, 0]), HORIZONTAL)
