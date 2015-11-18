# TODO: make test names more descriptive and apparent

from nose.tools import (
    assert_true, assert_false, assert_equal,
)

from q2 import (
    Vector,
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
    assert_equal(
        add_direction(Vector(row=0, col=0), VERTICAL),
        Vector(row=1, col=0)
    )


def test_add_direction_2():
    assert_equal(
        add_direction(Vector(row=2, col=6), VERTICAL),
        Vector(row=3, col=6)
    )


def test_add_direction_3():
    assert_equal(
        add_direction(Vector(row=8, col=4), VERTICAL),
        Vector(row=9, col=4)
    )


def test_add_direction_4():
    assert_equal(
        add_direction(Vector(row=5, col=1), HORIZONTAL),
        Vector(row=5, col=2)
    )


def test_add_direction_5():
    assert_equal(
        add_direction(Vector(row=3, col=0), HORIZONTAL),
        Vector(row=3, col=1)
    )


def test_add_direction_6():
    assert_equal(
        add_direction(Vector(row=7, col=8), HORIZONTAL),
        Vector(row=7, col=9)
    )


def test_substract_direction_1():
    assert_equal(
        substract_direction(Vector(row=0, col=7), VERTICAL),
        Vector(row=-1, col=7)
    )


def test_substract_direction_2():
    assert_equal(
        substract_direction(Vector(row=8, col=8), VERTICAL),
        Vector(row=7, col=8)
    )


def test_substract_direction_3():
    assert_equal(
        substract_direction(Vector(row=3, col=4), HORIZONTAL),
        Vector(row=3, col=3)
    )


def test_substract_direction_4():
    assert_equal(
        substract_direction(Vector(row=6, col=0), HORIZONTAL),
        Vector(row=6, col=-1)
    )


def test_adjacent_move_direction_wrong_1():
    assert_equal(
        adjacent_move_direction(Vector(row=0, col=0), Vector(0, 0)),
        None
    )


def test_adjacent_move_direction_wrong_2():
    assert_equal(
        adjacent_move_direction(Vector(row=0, col=0), Vector(3, 3)),
        None
    )


def test_adjacent_move_direction_wrong_3():
    assert_equal(
        adjacent_move_direction(Vector(row=2, col=5), Vector(2, 0)),
        None
    )


def test_adjacent_move_direction_vertical_1():
    assert_equal(
        adjacent_move_direction(Vector(row=0, col=0), Vector(row=1, col=0)),
        VERTICAL
    )


def test_adjacent_move_direction_vertical_2():
    assert_equal(
        adjacent_move_direction(Vector(row=7, col=5), Vector(row=6, col=5)),
        VERTICAL
    )


def test_adjacent_move_direction_horizontal_1():
    assert_equal(
        adjacent_move_direction(Vector(row=8, col=3), Vector(row=8, col=2)),
        HORIZONTAL
    )


def test_adjacent_move_direction_horizontal_2():
    assert_equal(
        adjacent_move_direction(Vector(row=0, col=7), Vector(row=0, col=8)),
        HORIZONTAL
    )


def test_pawn_within_board_wrong_1():
    assert_false(pawn_within_board(Vector(0, -1)))


def test_pawn_within_board_wrong_2():
    assert_false(pawn_within_board(Vector(1, 257)))


def test_pawn_within_board_wrong_3():
    assert_false(pawn_within_board(Vector(2147483649, -2147483649)))


def test_pawn_within_board_correct_1():
    assert_true(pawn_within_board(Vector(0, 0)))


def test_pawn_within_board_correct_2():
    assert_true(pawn_within_board(Vector(3, 7)))


def test_pawn_within_board_correct_3():
    assert_true(pawn_within_board(Vector(8, 8)))


def test_adjacent_pawn_spaces_left_top_corner():
    expected = set([Vector(row=1, col=0), Vector(row=0, col=1)])
    assert_equal(
        set(adjacent_pawn_spaces(Vector(row=0, col=0))),
        expected
    )


def test_adjacent_pawn_spaces_right_bottom_corner():
    expected = set([Vector(row=7, col=8), Vector(row=8, col=7)])
    assert_equal(
        set(adjacent_pawn_spaces(Vector(row=8, col=8))),
        expected
    )


def test_adjacent_pawn_spaces_right_side():
    expected = set([
        Vector(row=2, col=8),
        Vector(row=4, col=8),
        Vector(row=3, col=7),
    ])
    assert_equal(
        set(adjacent_pawn_spaces(Vector(row=3, col=8))),
        expected
    )


def test_adjacent_pawn_spaces_middle():
    expected = set([
        Vector(row=4, col=3),
        Vector(row=3, col=4),
        Vector(row=4, col=5),
        Vector(row=5, col=4),
    ])
    assert_equal(
        set(adjacent_pawn_spaces(Vector(row=4, col=4))),
        expected
    )


def test_wall_within_board_correct_1():
    assert_true(wall_within_board(Vector(row=0, col=0)))


def test_wall_within_board_correct_2():
    assert_true(wall_within_board(Vector(row=7, col=0)))


def test_wall_within_board_correct_3():
    assert_true(wall_within_board(Vector(row=4, col=5)))


def test_wall_within_board_correct_4():
    assert_true(wall_within_board(Vector(row=7, col=7)))


def test_wall_within_board_correct_5():
    assert_true(wall_within_board(Vector(row=4, col=0)))


def test_wall_within_board_wrong_1():
    assert_false(wall_within_board(Vector(row=2, col=-1)))


def test_wall_within_board_wrong_2():
    assert_false(wall_within_board(Vector(row=-3, col=8)))


def test_wall_within_board_wrong_3():
    assert_false(wall_within_board(Vector(row=2, col=8)))


def test_wall_within_board_wrong_4():
    assert_false(wall_within_board(Vector(row=2147483651, col=5)))


def test_wall_within_board_wrong_5():
    assert_false(wall_within_board(Vector(row=-1, col=0)))


def test_wall_within_board_wrong_6():
    assert_false(wall_within_board(Vector(row=-1, col=65538)))


def test_wall_within_board_wrong_7():
    assert_false(wall_within_board(Vector(row=-4294967296, col=4294967296)))


def test_pawn_move_distance_no_walls_1():
    assert_equal(
        pawn_move_distance_no_walls(
            Vector(row=0, col=0),
            Vector(row=5, col=5),
        ),
        10
    )


def test_pawn_move_distance_no_walls_2():
    assert_equal(
        pawn_move_distance_no_walls(
            Vector(row=7, col=7),
            Vector(row=6, col=2),
        ),
        6
    )


def test_pawn_move_distance_no_walls_3():
    assert_equal(
        pawn_move_distance_no_walls(
            Vector(row=1, col=4),
            Vector(row=7, col=3)
        ),
        7
    )


def test_pawn_move_distance_no_walls_4():
    assert_equal(
        pawn_move_distance_no_walls(
            Vector(row=2, col=5),
            Vector(row=2, col=5)
        ),
        0
    )


def test_is_occupied_1():
    assert_true(
        is_occupied(
            Vector(row=4, col=4),
            {Vector(row=4, col=3): 0, Vector(row=4, col=4): 1},
        )
    )


def test_is_occupied_2():
    assert_false(
        is_occupied(
            Vector(row=0, col=0),
            {Vector(row=1, col=7): 0, Vector(row=0, col=1): 1},
        )
    )


def test_is_wall_between_1():
    assert_true(
        is_wall_between(
            Vector(row=4, col=2),
            Vector(row=5, col=2),
            {HORIZONTAL: set([Vector(row=4, col=1)]), VERTICAL: set()}
        )
    )


def test_is_wall_between_2():
    assert_true(
        is_wall_between(
            Vector(row=6, col=6),
            Vector(row=5, col=6),
            {HORIZONTAL: set([Vector(row=5, col=6)]), VERTICAL: set()}
        )
    )


def test_is_wall_between_3():
    assert_true(
        is_wall_between(
            Vector(row=3, col=1),
            Vector(row=3, col=2),
            {HORIZONTAL: set(), VERTICAL: set([Vector(row=3, col=1)])}
        )
    )


def test_is_wall_between_4():
    assert_true(
        is_wall_between(
            Vector(row=1, col=4),
            Vector(row=1, col=3),
            {HORIZONTAL: set(), VERTICAL: set([Vector(row=0, col=3)])}
        )
    )


def test_is_wall_between_5():
    assert_true(
        is_wall_between(
            Vector(row=2, col=7),
            Vector(row=2, col=6),
            {HORIZONTAL: set(), VERTICAL: set([Vector(row=2, col=6)])}
        )
    )


def test_is_wall_between_6():
    assert_false(
        is_wall_between(
            Vector(row=0, col=0),
            Vector(row=1, col=0),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_is_wall_between_7():
    assert_false(
        is_wall_between(
            Vector(row=7, col=0),
            Vector(row=7, col=1),
            {
                HORIZONTAL: set([Vector(row=1, col=7)]),
                VERTICAL: set([Vector(row=2, col=6)]),
            }
        )
    )


def test_is_wall_between_8():
    assert_false(
        is_wall_between(
            Vector(row=3, col=3),
            Vector(row=2, col=3),
            {
                HORIZONTAL: set([Vector(row=2, col=1), Vector(row=2, col=4)]),
                VERTICAL: set([Vector(row=2, col=2)])
            }
        )
    )


def test_is_wall_between_wrong_1():
    assert_equal(
        is_wall_between(
            Vector(row=0, col=0),
            Vector(row=5, col=5),
            {HORIZONTAL: set(), VERTICAL: set()},
        ),
        None,
    )


def test_is_wall_between_wrong_2():
    assert_equal(
        is_wall_between(
            Vector(row=3, col=6),
            Vector(row=0, col=6),
            {HORIZONTAL: set(), VERTICAL: set()},
        ),
        None
    )


def test_is_wall_between_wrong_3():
    assert_equal(
        is_wall_between(
            Vector(row=6, col=7),
            Vector(row=6, col=2),
            {HORIZONTAL: set(), VERTICAL: set()},
        ),
        None
    )


def test_is_wall_between_wrong_4():
    assert_equal(
        is_wall_between(
            Vector(row=7, col=0),
            Vector(row=7, col=0),
            {HORIZONTAL: set(), VERTICAL: set()},
        ),
        None
    )


def test_adjacent_pawn_spaces_not_blocked_corner_1():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=8, col=0),
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=7, col=0), Vector(row=8, col=1)])
    )


def test_adjacent_pawn_spaces_not_blocked_corner_2():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=8, col=8),
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=7, col=7)]),
            }
        )),
        set([Vector(row=7, col=8)])
    )


def test_adjacent_pawn_spaces_not_blocked_side_1():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=8, col=4),
            {
                HORIZONTAL: set([Vector(row=7, col=3)]),
                VERTICAL: set([Vector(row=7, col=4)]),
            }
        )),
        set([Vector(row=8, col=3)])
    )


def test_adjacent_pawn_spaces_not_blocked_side_2():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=7, col=0),
            {
                HORIZONTAL: set([Vector(row=6, col=0)]),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=8, col=0), Vector(row=7, col=1)])
    )


def test_adjacent_pawn_spaces_not_blocked_side_3():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=5, col=8),
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=6, col=8), Vector(row=4, col=8), Vector(row=5, col=7)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_1():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=4, col=4),
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([
            Vector(row=4, col=3),
            Vector(row=3, col=4),
            Vector(row=5, col=4),
            Vector(row=4, col=5),
        ])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_2():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=7, col=2),
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=6, col=1)]),
            }
        )),
        set([Vector(row=7, col=3), Vector(row=6, col=2), Vector(row=8, col=2)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_3():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=3, col=5),
            {
                HORIZONTAL: set([Vector(row=3, col=4)]),
                VERTICAL: set([Vector(row=2, col=5)]),
            }
        )),
        set([Vector(row=3, col=4), Vector(row=2, col=5)])
    )


def test_adjacent_pawn_spaces_not_blocked_middle_4():
    assert_equal(
        set(adjacent_pawn_spaces_not_blocked(
            Vector(row=1, col=2),
            {
                HORIZONTAL: set([Vector(row=0, col=2), Vector(row=1, col=1)]),
                VERTICAL: set([Vector(row=0, col=1)]),
            }
        )),
        set([Vector(row=1, col=3)])
    )


def test_pawn_legal_moves_corner_1():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=0, col=0),
            {
                Vector(row=0, col=0): YELLOW,
                Vector(row=5, col=5): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=1, col=0), Vector(row=0, col=1)])
    )


def test_pawn_legal_moves_corner_2():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=8, col=8),
            {
                Vector(row=7, col=8): YELLOW,
                Vector(row=8, col=8): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=8, col=7), Vector(row=7, col=7), Vector(row=6, col=8)])
    )


def test_pawn_legal_moves_corner_3():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=8, col=0),
            {
                Vector(row=7, col=0): YELLOW,
                Vector(row=8, col=0): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=7, col=0)]),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=8, col=1)])
    )


def test_pawn_legal_moves_corner_4():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=0, col=8),
            {
                Vector(row=0, col=8): YELLOW,
                Vector(row=1, col=8): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=1, col=7)]),
                VERTICAL: set(),
            }
        )),
        set([Vector(row=0, col=7), Vector(row=1, col=7)])
    )


def test_pawn_legal_moves_corner_5():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=0, col=0),
            {
                Vector(row=0, col=0): YELLOW,
                Vector(row=1, col=0): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=1, col=0)]),
                VERTICAL: set([Vector(row=0, col=0)]),
            }
        )),
        set()
    )


def test_pawn_legal_moves_side_1():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=0, col=3),
            {
                Vector(row=0, col=3): YELLOW,
                Vector(row=1, col=3): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=1, col=3)]),
                VERTICAL: set([Vector(row=0, col=2)]),
            }
        )),
        set([Vector(row=0, col=4), Vector(row=1, col=4)])
    )


def test_pawn_legal_moves_side_2():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=1, col=8),
            {
                Vector(row=1, col=8): YELLOW,
                Vector(row=2, col=8): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=1, col=7)]),
            }
        )),
        set([Vector(row=0, col=8), Vector(row=3, col=8)])
    )


def test_pawn_legal_moves_side_3():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=8, col=7),
            {
                Vector(row=7, col=7): YELLOW,
                Vector(row=8, col=7): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([
            Vector(row=8, col=6),
            Vector(row=6, col=7),
            Vector(row=8, col=8),
            Vector(row=7, col=6),
            Vector(row=7, col=8),
        ])
    )


def test_pawn_legal_moves_side_4():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=2, col=0),
            {
                Vector(row=2, col=1): YELLOW,
                Vector(row=2, col=0): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=1, col=0)]),
                VERTICAL: set([Vector(row=2, col=0)]),
            }
        )),
        set([Vector(row=3, col=0)])
    )


def test_pawn_legal_moves_middle_1():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=2, col=4),
            {
                Vector(row=2, col=4): YELLOW,
                Vector(row=3, col=4): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set(),
            }
        )),
        set([
            Vector(row=2, col=3),
            Vector(row=2, col=5),
            Vector(row=1, col=4),
            Vector(row=3, col=5),
            Vector(row=3, col=3),
            Vector(row=4, col=4),
        ])
    )


def test_pawn_legal_moves_middle_2():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=5, col=5),
            {
                Vector(row=5, col=4): YELLOW,
                Vector(row=5, col=5): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=5, col=4), Vector(row=4, col=5)]),
                VERTICAL: set([Vector(row=5, col=3), Vector(row=5, col=5)]),
            }
        )),
        set([Vector(row=4, col=4)])
    )


def test_pawn_legal_moves_middle_3():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=7, col=1),
            {
                Vector(row=7, col=1): YELLOW,
                Vector(row=6, col=1): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=5, col=0), Vector(row=7, col=1)]),
                VERTICAL: set([Vector(row=6, col=0), Vector(row=6, col=1)]),
            }
        )),
        set()
    )


def test_pawn_legal_moves_middle_4():
    assert_equal(
        set(pawn_legal_moves(
            Vector(row=2, col=6),
            {
                Vector(row=2, col=5): YELLOW,
                Vector(row=2, col=6): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=1, col=5)]),
            }
        )),
        set([Vector(row=1, col=6), Vector(row=2, col=7), Vector(row=3, col=6)])
    )


def test_is_correct_pawn_move_correct_1():
    assert_true(
        is_correct_pawn_move(
            Vector(row=0, col=4),
            Vector(row=1, col=4),
            {
                Vector(row=0, col=4): YELLOW,
                Vector(row=8, col=4): GREEN,
            },
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=4, col=4)]),
            }
        )
    )


def test_is_correct_pawn_move_correct_2():
    assert_true(
        is_correct_pawn_move(
            Vector(row=6, col=5),
            Vector(row=5, col=5),
            {
                Vector(row=2, col=3): YELLOW,
                Vector(row=6, col=5): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=4, col=1)]),
                VERTICAL: set([Vector(row=2, col=7)]),
            }
        )
    )


def test_is_correct_pawn_move_correct_3():
    assert_true(
        is_correct_pawn_move(
            Vector(row=4, col=2),
            Vector(row=5, col=3),
            {
                Vector(row=4, col=2): YELLOW,
                Vector(row=5, col=2): GREEN,
            },
            {
                HORIZONTAL: set([Vector(row=5, col=2)]),
                VERTICAL: set([Vector(row=3, col=2)]),
            }
        )
    )


def test_is_correct_pawn_move_wrong_1():
    assert_false(
        is_correct_pawn_move(
            Vector(row=0, col=0),
            Vector(row=2, col=0),
            {
                Vector(row=0, col=0): YELLOW,
                Vector(row=3, col=4): GREEN,
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
            Vector(row=7, col=0),
            (-1, 6),
            {
                Vector(row=6, col=0): YELLOW,
                Vector(row=7, col=0): GREEN,
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
            Vector(row=5, col=7),
            Vector(row=5, col=9),
            {
                Vector(row=5, col=7): YELLOW,
                Vector(row=5, col=8): GREEN,
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
            Vector(row=5, col=4),
            Vector(row=2, col=4),
            {
                Vector(row=4, col=4): YELLOW,
                Vector(row=5, col=4): GREEN,
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
            Vector(row=3, col=3),
            Vector(row=3, col=3),
            {
                Vector(row=3, col=3): YELLOW,
                Vector(row=4, col=3): GREEN,
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
            Vector(row=1, col=5),
            Vector(row=3, col=5),
            {
                Vector(row=1, col=5): YELLOW,
                Vector(row=3, col=5): GREEN,
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
            Vector(row=0, col=0),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_wall_intersects_2():
    assert_false(
        wall_intersects(
            VERTICAL,
            Vector(row=4, col=4),
            {
                HORIZONTAL: set([
                    Vector(row=4, col=3),
                    Vector(row=4, col=5),
                    Vector(row=3, col=4),
                    Vector(row=5, col=4),
                ]),
                VERTICAL: set([
                    Vector(row=2, col=4),
                    Vector(row=6, col=4),
                ])
            }
        )
    )


def test_wall_intersects_3():
    assert_false(
        wall_intersects(
            HORIZONTAL,
            Vector(row=0, col=7),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_wall_intersects_4():
    assert_false(
        wall_intersects(
            HORIZONTAL,
            Vector(row=1, col=2),
            {
                HORIZONTAL: set([
                    Vector(row=1, col=0),
                    Vector(row=1, col=4),
                ]),
                VERTICAL: set([
                    Vector(row=1, col=1),
                    Vector(row=0, col=2),
                    Vector(row=2, col=2),
                    Vector(row=1, col=3),
                ])
            }
        )
    )


def test_wall_intersects_5():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            Vector(row=6, col=5),
            {
                HORIZONTAL: set([Vector(row=6, col=4)]),
                VERTICAL: set()
            }
        )
    )


def test_wall_intersects_6():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            Vector(row=1, col=3),
            {
                HORIZONTAL: set([Vector(row=1, col=4)]),
                VERTICAL: set()
            }
        )
    )


def test_wall_intersects_7():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            Vector(row=7, col=7),
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=7, col=7)])
            }
        )
    )


def test_wall_intersects_8():
    assert_true(
        wall_intersects(
            VERTICAL,
            Vector(row=1, col=0),
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=0, col=0)])
            }
        )
    )


def test_wall_intersects_9():
    assert_true(
        wall_intersects(
            VERTICAL,
            Vector(row=6, col=2),
            {
                HORIZONTAL: set(),
                VERTICAL: set([Vector(row=7, col=2)])
            }
        )
    )


def test_wall_intersects_10():
    assert_true(
        wall_intersects(
            VERTICAL,
            Vector(row=2, col=2),
            {
                HORIZONTAL: set([Vector(row=2, col=2)]),
                VERTICAL: set()
            }
        )
    )


def test_wall_intersects_11():
    assert_true(
        wall_intersects(
            HORIZONTAL,
            Vector(row=5, col=5),
            {
                HORIZONTAL: set([Vector(row=5, col=5)]),
                VERTICAL: set()
            }
        )
    )


def test_pawn_can_reach_goal_1():
    assert_true(
        pawn_can_reach_goal(
            YELLOW,
            Vector(row=4, col=3),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_pawn_can_reach_goal_2():
    assert_true(
        pawn_can_reach_goal(
            GREEN,
            Vector(row=5, col=2),
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_pawn_can_reach_goal_3():
    assert_true(
        pawn_can_reach_goal(
            YELLOW,
            Vector(row=0, col=4),
            {
                HORIZONTAL: set([
                    Vector(row=0, col=1),
                    Vector(row=1, col=3),
                    Vector(row=1, col=5),
                    Vector(row=2, col=0),
                    Vector(row=2, col=2),
                    Vector(row=2, col=5),
                    Vector(row=2, col=7),
                ]),
                VERTICAL: set()
            }
        )
    )


def test_pawn_can_reach_goal_4():
    assert_false(
        pawn_can_reach_goal(
            YELLOW,
            Vector(row=4, col=4),
            {
                HORIZONTAL: set([
                    Vector(row=2, col=2),
                    Vector(row=3, col=3),
                    Vector(row=4, col=4),
                    Vector(row=2, col=4),
                    Vector(row=4, col=2),
                ]),
                VERTICAL: set([
                    Vector(row=3, col=1),
                    Vector(row=3, col=5),
                ])
            }
        )
    )


def test_pawn_can_reach_goal_5():
    assert_false(
        pawn_can_reach_goal(
            GREEN,
            Vector(row=8, col=3),
            {
                HORIZONTAL: set([
                    Vector(row=0, col=0),
                    Vector(row=0, col=2),
                    Vector(row=0, col=4),
                    Vector(row=0, col=6),
                    Vector(row=1, col=7),
                ]),
                VERTICAL: set([
                    Vector(row=0, col=7),
                ])
            }
        )
    )


def test_is_correct_wall_move_1():
    assert_true(
        is_correct_wall_move(
            HORIZONTAL,
            Vector(row=0, col=4),
            {YELLOW: Vector(row=0, col=4), GREEN: Vector(row=8, col=4)},
            {HORIZONTAL: set(), VERTICAL: set()}
        )
    )


def test_is_correct_wall_move_2():
    assert_true(
        is_correct_wall_move(
            HORIZONTAL,
            Vector(row=5, col=6),
            {YELLOW: Vector(row=0, col=4), GREEN: Vector(row=8, col=4)},
            {
                HORIZONTAL: set([
                    Vector(row=5, col=0),
                    Vector(row=5, col=2),
                    Vector(row=5, col=4),
                    Vector(row=1, col=0),
                    Vector(row=1, col=2),
                    Vector(row=1, col=4),
                    Vector(row=1, col=6),
                ]),
                VERTICAL: set([
                    Vector(row=1, col=7),
                    Vector(row=3, col=7),
                    Vector(row=5, col=7),
                ])
            }
        )
    )


def test_is_correct_wall_move_using_tuples_1():
    assert_true(
        is_correct_wall_move(
            HORIZONTAL,
            Vector(row=5, col=6),
            {YELLOW: (0, 4), GREEN: (8, 4)},
            {
                HORIZONTAL: set([
                    (5, 0),
                    (5, 2),
                    (5, 4),
                    (1, 0),
                    (1, 2),
                    (1, 4),
                    (1, 6),
                ]),
                VERTICAL: set([
                    (1, 7),
                    (3, 7),
                    (5, 7),
                ])
            }
        )
    )
