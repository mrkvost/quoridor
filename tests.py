# TODO: make test names more descriptive and apparent

from nose.tools import (
    assert_true, assert_false, assert_equal,
)

from q2 import (
    YELLOW,
    GREEN,
    VERTICAL,
    HORIZONTAL,
    add_direction,
    substract_direction,
    adjacent_move_direction,
    pawn_within_board,
    adjacent_pawn_spaces,
    wall_within_board,
    pawn_move_distance_no_walls,
    is_occupied,
    is_wall_between,
    adjacent_pawn_spaces_not_blocked,
    pawn_legal_moves,
    is_correct_pawn_move,
    wall_intersects,
    pawn_can_reach_goal,
    is_correct_wall_move,
)


def test_add_direction_1():
    assert_equal(add_direction((0, 0), VERTICAL), (0, 1))


def test_add_direction_2():
    assert_equal(add_direction((6, 2), VERTICAL), (6, 3))


def test_add_direction_3():
    assert_equal(add_direction((4, 8), VERTICAL), (4, 9))


def test_add_direction_4():
    assert_equal(add_direction((1, 5), HORIZONTAL), (2, 5))


def test_add_direction_5():
    assert_equal(add_direction((0, 3), HORIZONTAL), (1, 3))


def test_add_direction_6():
    assert_equal(add_direction((8, 7), HORIZONTAL), (9, 7))


def test_substract_direction_1():
    assert_equal(substract_direction((7, 0), VERTICAL), (7, -1))


def test_substract_direction_2():
    assert_equal(substract_direction((8, 8), VERTICAL), (8, 7))


def test_substract_direction_3():
    assert_equal(substract_direction((4, 3), HORIZONTAL), (3, 3))


def test_substract_direction_4():
    assert_equal(substract_direction((0, 6), HORIZONTAL), (-1, 6))


def test_adjacent_move_direction_wrong_1():
    assert_equal(adjacent_move_direction([0, 0], [0, 0]), None)


def test_adjacent_move_direction_wrong_2():
    assert_equal(adjacent_move_direction([0, 0], [3, 3]), None)


def test_adjacent_move_direction_wrong_3():
    assert_equal(adjacent_move_direction([5, 2], [0, 2]), None)


def test_adjacent_move_direction_vertical_1():
    assert_equal(adjacent_move_direction([0, 0], [0, 1]), VERTICAL)


def test_adjacent_move_direction_vertical_2():
    assert_equal(adjacent_move_direction([5, 7], [5, 6]), VERTICAL)


def test_adjacent_move_direction_horizontal_1():
    assert_equal(adjacent_move_direction([3, 8], [2, 8]), HORIZONTAL)


def test_adjacent_move_direction_horizontal_2():
    assert_equal(adjacent_move_direction([7, 0], [8, 0]), HORIZONTAL)


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


def test_adjacent_pawn_spaces_left_top_corner():
    expected = set([(0, 1), (1, 0)])
    assert_equal(set(adjacent_pawn_spaces((0, 0))), expected)


def test_adjacent_pawn_spaces_right_bottom_corner():
    expected = set([(8, 7), (7, 8)])
    assert_equal(set(adjacent_pawn_spaces((8, 8))), expected)


def test_adjacent_pawn_spaces_right_side():
    expected = set([(8, 2), (8, 4), (7, 3)])
    assert_equal(set(adjacent_pawn_spaces((8, 3))), expected)


def test_adjacent_pawn_spaces_middle():
    expected = set([(3, 4), (4, 3), (5, 4), (4, 5)])
    assert_equal(set(adjacent_pawn_spaces((4, 4))), expected)


def test_wall_within_board_correct_1():
    assert_true(pawn_within_board([0, 0]))


def test_wall_within_board_correct_2():
    assert_true(pawn_within_board([0, 7]))


def test_wall_within_board_correct_3():
    assert_true(pawn_within_board([5, 4]))


def test_wall_within_board_correct_4():
    assert_true(pawn_within_board([7, 7]))


def test_wall_within_board_correct_5():
    assert_true(wall_within_board((0, 4)))


def test_wall_within_board_wrong_1():
    assert_false(wall_within_board((-1, 2)))


def test_wall_within_board_wrong_2():
    assert_false(wall_within_board((8, -3)))


def test_wall_within_board_wrong_3():
    assert_false(wall_within_board((8, 2)))


def test_wall_within_board_wrong_4():
    assert_false(wall_within_board((5, 2147483651)))


def test_wall_within_board_wrong_5():
    assert_false(wall_within_board([0, -1]))


def test_wall_within_board_wrong_6():
    assert_false(wall_within_board([65538, -1]))


def test_wall_within_board_wrong_7():
    assert_false(wall_within_board([-4294967296, 4294967296]))


def test_pawn_move_distance_no_walls_1():
    assert_equal(pawn_move_distance_no_walls((0, 0), (5, 5)), 10)


def test_pawn_move_distance_no_walls_2():
    assert_equal(pawn_move_distance_no_walls((7, 7), (2, 6)), 6)


def test_pawn_move_distance_no_walls_3():
    assert_equal(pawn_move_distance_no_walls((4, 1), (3, 7)), 7)


def test_pawn_move_distance_no_walls_4():
    assert_equal(pawn_move_distance_no_walls((5, 2), (5, 2)), 0)


def test_is_occupied_1():
    assert_true(is_occupied((4, 4), {(3, 4): 0, (4, 4): 1}))


def test_is_occupied_2():
    assert_false(is_occupied((0, 0), {(7, 1): 0, (1, 0): 1}))


def test_is_wall_between_1():
    assert_true(
        is_wall_between(
            (2, 4),
            (2, 5),
            {HORIZONTAL: set([(1, 4)]), VERTICAL: set()}
        )
    )


def test_is_wall_between_2():
    assert_true(
        is_wall_between(
            (6, 6),
            (6, 5),
            {HORIZONTAL: set([(6, 5)]), VERTICAL: set()}
        )
    )


def test_is_wall_between_3():
    assert_true(
        is_wall_between(
            (1, 3),
            (2, 3),
            {HORIZONTAL: set(), VERTICAL: set([(1, 3)])}
        )
    )


def test_is_wall_between_4():
    assert_true(
        is_wall_between(
            (4, 1),
            (3, 1),
            {HORIZONTAL: set(), VERTICAL: set([(3, 0)])}
        )
    )


def test_is_wall_between_5():
    assert_true(
        is_wall_between(
            (7, 2),
            (6, 2),
            {HORIZONTAL: set(), VERTICAL: set([(6, 2)])}
        )
    )


def test_is_wall_between_6():
    assert_false(
        is_wall_between((0, 0), (0, 1), {HORIZONTAL: set(), VERTICAL: set()})
    )


def test_is_wall_between_7():
    assert_false(
        is_wall_between(
            (0, 7),
            (1, 7),
            {HORIZONTAL: set([(7, 1)]), VERTICAL: set([(6, 2)])}
        )
    )


def test_is_wall_between_8():
    assert_false(
        is_wall_between(
            (3, 3),
            (3, 2),
            {
                HORIZONTAL: set([(1, 2), (4, 2)]),
                VERTICAL: set([(2, 2)])
            }
        )
    )


def test_is_wall_between_wrong_1():
    assert_equal(
        is_wall_between((0, 0), (5, 5), {HORIZONTAL: set(), VERTICAL: set()}),
        None,
    )


def test_is_wall_between_wrong_2():
    assert_equal(
        is_wall_between((6, 3), (6, 0), {HORIZONTAL: set(), VERTICAL: set()}),
        None
    )


def test_is_wall_between_wrong_3():
    assert_equal(
        is_wall_between((7, 6), (2, 6), {HORIZONTAL: set(), VERTICAL: set()}),
        None
    )


def test_is_wall_between_wrong_4():
    assert_equal(
        is_wall_between((0, 7), (0, 7), {HORIZONTAL: set(), VERTICAL: set()}),
        None
    )


def test_adjacent_pawn_spaces_not_blocked_corner_1():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (0, 8),
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(0, 7), (1, 8)])
    )


def test_adjacent_pawn_spaces_not_blocked_corner_2():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (8, 8),
            {
                HORIZONTAL: set(),
                VERTICAL: set([(7, 7)]),
            }
        )),
        set([(8, 7)])
    )


def test_adjacent_pawn_spaces_not_blocked_side_1():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (4, 8),
            {
                HORIZONTAL: set([(3, 7)]),
                VERTICAL: set([(4, 7)]),
            }
        )),
        set([(3, 8)])
    )


def test_adjacent_pawn_spaces_not_blocked_side_2():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (0, 7),
            {
                HORIZONTAL: set([(0, 6)]),
                VERTICAL: set(),
            }
        )),
        set([(0, 8), (1, 7)])
    )


def test_adjacent_pawn_spaces_not_blocked_side_3():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (8, 5),
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(8, 6), (8, 4), (7, 5)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_1():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (4, 4),
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(3, 4), (4, 3), (4, 5), (5, 4)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_2():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (2, 7),
            {
                HORIZONTAL: set(),
                VERTICAL: set([(1, 6)]),
            }
        )),
        set([(3, 7), (2, 6), (2, 8)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_3():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (5, 3),
            {
                HORIZONTAL: set([(4, 3)]),
                VERTICAL: set([(5, 2)]),
            }
        )),
        set([(4, 3), (5, 2)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_4():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            (2, 1),
            {
                HORIZONTAL: set([(2, 0), (1, 1)]),
                VERTICAL: set([(1, 0)]),
            }
        )),
        set([(3, 1)])
    )


def test_pawn_legal_moves_corner_1():
    assert_equal(
        set(pawn_legal_moves(
            (0, 0),
            {
                (0, 0): YELLOW,
                (5, 5): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(0, 1), (1, 0)])
    )


def test_pawn_legal_moves_corner_2():
    assert_equal(
        set(pawn_legal_moves(
            (8, 8),
            {
                (8, 7): YELLOW,
                (8, 8): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(7, 8), (7, 7), (8, 6)])
    )


def test_pawn_legal_moves_corner_3():
    assert_equal(
        set(pawn_legal_moves(
            (0, 8),
            {
                (0, 7): YELLOW,
                (0, 8): GREEN,
            },
            {
                HORIZONTAL: set([(0, 7)]),
                VERTICAL: set(),
            }
        )),
        set([(1, 8)])
    )


def test_pawn_legal_moves_corner_4():
    assert_equal(
        set(pawn_legal_moves(
            (8, 0),
            {
                (8, 0): YELLOW,
                (8, 1): GREEN,
            },
            {
                HORIZONTAL: set([(7, 1)]),
                VERTICAL: set(),
            }
        )),
        set([(7, 0), (7, 1)])
    )


def test_pawn_legal_moves_corner_5():
    assert_equal(
        set(pawn_legal_moves(
            (0, 0),
            {
                (0, 0): YELLOW,
                (0, 1): GREEN,
            },
            {
                HORIZONTAL: set([(0, 1)]),
                VERTICAL: set([(0, 0)]),
            }
        )),
        set()
    )


def test_pawn_legal_moves_side_1():
    assert_equal(
        set(pawn_legal_moves(
            (3, 0),
            {
                (3, 0): YELLOW,
                (3, 1): GREEN,
            },
            {
                HORIZONTAL: set([(3, 1)]),
                VERTICAL: set([(2, 0)]),
            }
        )),
        set([(4, 0), (4, 1)])
    )


def test_pawn_legal_moves_side_2():
    assert_equal(
        set(pawn_legal_moves(
            (8, 1),
            {
                (8, 1): YELLOW,
                (8, 2): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set([(7, 1)]),
            }
        )),
        set([(8, 0), (8, 3)])
    )


def test_pawn_legal_moves_side_3():
    assert_equal(
        set(pawn_legal_moves(
            (7, 8),
            {
                (7, 7): YELLOW,
                (7, 8): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(6, 8), (7, 6), (8, 8), (6, 7), (8, 7)])
    )


def test_pawn_legal_moves_side_4():
    assert_equal(
        set(pawn_legal_moves(
            (0, 2),
            {
                (1, 2): YELLOW,
                (0, 2): GREEN,
            },
            {
                HORIZONTAL: set([(0, 1)]),
                VERTICAL: set([(0, 2)]),
            }
        )),
        set([(0, 3)])
    )


def test_pawn_legal_moves_middle_1():
    assert_equal(
        set(pawn_legal_moves(
            (4, 2),
            {
                (4, 2): YELLOW,
                (4, 3): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([(3, 2), (5, 2), (4, 1), (5, 3), (3, 3), (4, 4)])
    )


def test_pawn_legal_moves_middle_2():
    assert_equal(
        set(pawn_legal_moves(
            (5, 5),
            {
                (4, 5): YELLOW,
                (5, 5): GREEN,
            },
            {
                HORIZONTAL: set([(4, 5), (5, 4)]),
                VERTICAL: set([(3, 5), (5, 5)]),
            }
        )),
        set([(4, 4)])
    )


def test_pawn_legal_moves_middle_3():
    assert_equal(
        set(pawn_legal_moves(
            (1, 7),
            {
                (1, 7): YELLOW,
                (1, 6): GREEN,
            },
            {
                HORIZONTAL: set([(0, 5), (1, 7)]),
                VERTICAL: set([(0, 6), (1, 6)]),
            }
        )),
        set()
    )


def test_pawn_legal_moves_middle_4():
    assert_equal(
        set(pawn_legal_moves(
            (6, 2),
            {
                (5, 2): YELLOW,
                (6, 2): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set([(5, 1)]),
            }
        )),
        set([(6, 1), (7, 2), (6, 3)])
    )


def test_is_correct_pawn_move_correct_1():
    assert_true(
        is_correct_pawn_move(
            (4, 0),
            (4, 1),
            {
                (4, 0): YELLOW,
                (4, 8): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set([(4, 4)]),
            }
        )
    )


def test_is_correct_pawn_move_correct_2():
    assert_true(
        is_correct_pawn_move(
            (5, 6),
            (5, 5),
            {
                (3, 2): YELLOW,
                (5, 6): GREEN,
            },
            {
                HORIZONTAL: set([(1, 4)]),
                VERTICAL: set([(7, 2)]),
            }
        )
    )


def test_is_correct_pawn_move_correct_3():
    assert_true(
        is_correct_pawn_move(
            (2, 4),
            (3, 5),
            {
                (2, 4): YELLOW,
                (2, 5): GREEN,
            },
            {
                HORIZONTAL: set([(2, 5)]),
                VERTICAL: set([(2, 3)]),
            }
        )
    )


def test_is_correct_pawn_move_wrong_1():
    assert_false(
        is_correct_pawn_move(
            (0, 0),
            (0, 2),
            {
                (0, 0): YELLOW,
                (4, 3): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )
    )


def test_is_correct_pawn_move_wrong_2():
    assert_false(
        is_correct_pawn_move(
            (0, 7),
            (-1, 6),
            {
                (0, 6): YELLOW,
                (0, 7): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )
    )


def test_is_correct_pawn_move_wrong_3():
    assert_false(
        is_correct_pawn_move(
            (7, 5),
            (9, 5),
            {
                (7, 5): YELLOW,
                (8, 5): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )
    )


def test_is_correct_pawn_move_wrong_4():
    assert_false(
        is_correct_pawn_move(
            (4, 5),
            (4, 2),
            {
                (4, 4): YELLOW,
                (4, 5): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )
    )


def test_is_correct_pawn_move_wrong_5():
    assert_false(
        is_correct_pawn_move(
            (3, 3),
            (3, 3),
            {
                (3, 3): YELLOW,
                (3, 4): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )
    )


def test_is_correct_pawn_move_wrong_6():
    assert_false(
        is_correct_pawn_move(
            (5, 1),
            (5, 3),
            {
                (5, 1): YELLOW,
                (5, 3): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )
    )


def test_wall_intersects_1():
    assert_false(
        wall_intersects(
            VERTICAL,
            (0, 0),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_wall_intersects_2():
    assert_false(
        wall_intersects(
            VERTICAL,
            (4, 4),
            {
                HORIZONTAL: set([(3, 4), (5, 4), (4, 3), (4, 5)]),
                VERTICAL: set([(4, 2), (4, 6)])
            }
        )
    )


def test_wall_intersects_3():
    assert_false(
        wall_intersects(
            HORIZONTAL,
            (7, 0),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_wall_intersects_4():
    assert_false(
        wall_intersects(
            HORIZONTAL,
            (2, 1),
            {
                HORIZONTAL: set([(0, 1), (4, 1)]),
                VERTICAL: set([(1, 1), (2, 0), (2, 2), (3, 1)])
            }
        )
    )


def test_wall_intersects_5():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            (5, 6),
            {
                HORIZONTAL: set([(4, 6)]),
                VERTICAL: set()
            }
        )
    )


def test_wall_intersects_6():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            (3, 1),
            {
                HORIZONTAL: set([(4, 1)]),
                VERTICAL: set()
            }
        )
    )


def test_wall_intersects_7():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            (7, 7),
            {
                HORIZONTAL: set(),
                VERTICAL: set([(7, 7)])
            }
        )
    )


def test_wall_intersects_8():
    assert_true(
        wall_intersects(
            VERTICAL,
            (0, 1),
            {
                HORIZONTAL: set(),
                VERTICAL: set([(0, 0)])
            }
        )
    )


def test_wall_intersects_9():
    assert_true(
        wall_intersects(
            VERTICAL,
            (2, 6),
            {
                HORIZONTAL: set(),
                VERTICAL: set([(2, 7)])
            }
        )
    )


def test_wall_intersects_10():
    assert_true(
        wall_intersects(
            VERTICAL,
            (2, 2),
            {
                HORIZONTAL: set([(2, 2)]),
                VERTICAL: set()
            }
        )
    )


def test_wall_intersects_11():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            (5, 5),
            {
                HORIZONTAL: set([(5, 5)]),
                VERTICAL: set()
            }
        )
    )


def test_pawn_can_reach_goal_1():
    assert_true(
        pawn_can_reach_goal(
            YELLOW,
            (3, 4),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_pawn_can_reach_goal_2():
    assert_true(
        pawn_can_reach_goal(
            GREEN,
            (2, 5),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_pawn_can_reach_goal_3():
    assert_true(
        pawn_can_reach_goal(
            YELLOW,
            (4, 0),
            {
                HORIZONTAL: set([
                    (1, 0), (3, 1), (5, 1), (0, 2), (2, 2), (5, 2), (7, 2)
                ]),
                VERTICAL: set()
            }
        )
    )


def test_pawn_can_reach_goal_4():
    assert_true(
        pawn_can_reach_goal(
            GREEN,
            (4, 4),
            {
                HORIZONTAL: set([
                    (2, 2), (3, 3), (4, 4), (4, 2), (1, 4)
                ]),
                VERTICAL: set([
                    (1, 3), (5, 3)
                ])
            }
        )
    )


def test_pawn_can_reach_goal_4():
    assert_false(
        pawn_can_reach_goal(
            YELLOW,
            (4, 4),
            {
                HORIZONTAL: set([
                    (2, 2), (3, 3), (4, 4), (4, 2), (2, 4)
                ]),
                VERTICAL: set([
                    (1, 3), (5, 3)
                ])
            }
        )
    )


def test_pawn_can_reach_goal_5():
    assert_false(
        pawn_can_reach_goal(
            GREEN,
            (3, 8),
            {
                HORIZONTAL: set([
                    (0, 0), (2, 0), (4, 0), (6, 0), (7, 1)
                ]),
                VERTICAL: set([
                    (7, 0)
                ])
            }
        )
    )


def test_is_correct_wall_move_1():
    assert_true(
        is_correct_wall_move(
            HORIZONTAL,
            (4, 0),
            {YELLOW: (4, 0), GREEN: (4, 8)},
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_is_correct_wall_move_2():
    assert_true(
        is_correct_wall_move(
            HORIZONTAL,
            (6, 5),
            {YELLOW: (4, 0), GREEN: (4, 8)},
            {
                HORIZONTAL: set([
                    (0, 5), (2, 5), (4, 5), (0, 1), (2, 1), (4, 1), (6, 1)
                ]),
                VERTICAL: set([
                    (7, 1), (7, 3), (7, 5)
                ])
            }
        )
    )
