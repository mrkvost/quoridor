# TODO: make test names more descriptive and apparent

from nose.tools import (
    assert_true, assert_false, assert_equal,
)

from quoridor.core import (
    Vector,
    YELLOW,
    GREEN,
    VERTICAL,
    HORIZONTAL,
    add_direction,
    substract_direction,
    adjacent_move_direction,
    pawn_within_board,
    wall_within_board,
    pawn_move_distance_no_walls,
    is_occupied,
    is_wall_between,
    pawn_legal_moves,
    is_correct_pawn_move,
    wall_intersects,
    player_can_reach_goal,
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
            {
                'pawns': {
                    YELLOW: Vector(row=4, col=3),
                    GREEN: Vector(row=4, col=4),
                },
            },
            Vector(row=4, col=4),
        )
    )


def test_is_occupied_2():
    assert_false(
        is_occupied(
            {
                'pawns': {
                    YELLOW: Vector(row=1, col=7),
                    GREEN: Vector(row=0, col=1),
                },
            },
            Vector(row=0, col=0),
        )
    )


def test_is_wall_between_1():
    assert_true(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=4, col=1)]),
                    VERTICAL: set(),
                },
            },
            Vector(row=4, col=2),
            Vector(row=5, col=2),
        )
    )


def test_is_wall_between_2():
    assert_true(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=5, col=6)]),
                    VERTICAL: set(),
                },
            },
            Vector(row=6, col=6),
            Vector(row=5, col=6),
        )
    )


def test_is_wall_between_3():
    assert_true(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=3, col=1)]),
                },
            },
            Vector(row=3, col=1),
            Vector(row=3, col=2),
        )
    )


def test_is_wall_between_4():
    assert_true(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=0, col=3)]),
                },
            },
            Vector(row=1, col=4),
            Vector(row=1, col=3),
        )
    )


def test_is_wall_between_5():
    assert_true(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=2, col=6)]),
                },
            },
            Vector(row=2, col=7),
            Vector(row=2, col=6),
        )
    )


def test_is_wall_between_6():
    assert_false(
        is_wall_between(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            Vector(row=0, col=0),
            Vector(row=1, col=0),
        )
    )


def test_is_wall_between_7():
    assert_false(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=1, col=7)]),
                    VERTICAL: set([Vector(row=2, col=6)]),
                },
            },
            Vector(row=7, col=0),
            Vector(row=7, col=1),
        )
    )


def test_is_wall_between_8():
    assert_false(
        is_wall_between(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=2, col=1), Vector(row=2, col=4)]),
                    VERTICAL: set([Vector(row=2, col=2)])
                },
            },
            Vector(row=3, col=3),
            Vector(row=2, col=3),
        )
    )


def test_is_wall_between_wrong_1():
    assert_equal(
        is_wall_between(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            Vector(row=0, col=0),
            Vector(row=5, col=5),
        ),
        None,
    )


def test_is_wall_between_wrong_2():
    assert_equal(
        is_wall_between(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            Vector(row=3, col=6),
            Vector(row=0, col=6),
        ),
        None
    )


def test_is_wall_between_wrong_3():
    assert_equal(
        is_wall_between(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            Vector(row=6, col=7),
            Vector(row=6, col=2),
        ),
        None
    )


def test_is_wall_between_wrong_4():
    assert_equal(
        is_wall_between(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            Vector(row=7, col=0),
            Vector(row=7, col=0),
        ),
        None
    )


def test_pawn_legal_moves_corner_1():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=0),
                    GREEN: Vector(row=5, col=5),
                },
            },
            Vector(row=0, col=0),
        )),
        set([Vector(row=1, col=0), Vector(row=0, col=1)])
    )


def test_pawn_legal_moves_corner_2():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=7, col=8),
                    GREEN: Vector(row=8, col=8),
                },
            },
            Vector(row=8, col=8),
        )),
        set([Vector(row=8, col=7), Vector(row=7, col=7), Vector(row=6, col=8)])
    )


def test_pawn_legal_moves_corner_3():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=7, col=0)]),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=7, col=0),
                    GREEN: Vector(row=8, col=0),
                },
            },
            Vector(row=8, col=0),
        )),
        set([Vector(row=8, col=1)])
    )


def test_pawn_legal_moves_corner_4():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=1, col=7)]),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=8),
                    GREEN: Vector(row=1, col=8),
                },
            },
            Vector(row=0, col=8),
        )),
        set([Vector(row=0, col=7), Vector(row=1, col=7)])
    )


def test_pawn_legal_moves_corner_5():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=1, col=0)]),
                    VERTICAL: set([Vector(row=0, col=0)]),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=0),
                    GREEN: Vector(row=1, col=0),
                },
            },
            Vector(row=0, col=0),
        )),
        set()
    )


def test_pawn_legal_moves_side_1():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=1, col=3)]),
                    VERTICAL: set([Vector(row=0, col=2)]),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=3),
                    GREEN: Vector(row=1, col=3),
                },
            },
            Vector(row=0, col=3),
        )),
        set([Vector(row=0, col=4), Vector(row=1, col=4)])
    )


def test_pawn_legal_moves_side_2():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=1, col=7)]),
                },
                'pawns': {
                    YELLOW: Vector(row=1, col=8),
                    GREEN: Vector(row=2, col=8),
                },
            },
            Vector(row=1, col=8),
        )),
        set([Vector(row=0, col=8), Vector(row=3, col=8)])
    )


def test_pawn_legal_moves_side_3():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=7, col=7),
                    GREEN: Vector(row=8, col=7),
                },
            },
            Vector(row=8, col=7),
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
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=1, col=0)]),
                    VERTICAL: set([Vector(row=2, col=0)]),
                },
                'pawns': {
                    YELLOW: Vector(row=2, col=1),
                    GREEN: Vector(row=2, col=0),
                },
            },
            Vector(row=2, col=0),
        )),
        set([Vector(row=3, col=0)])
    )


def test_pawn_legal_moves_middle_1():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=2, col=4),
                    GREEN: Vector(row=3, col=4),
                },
            },
            Vector(row=2, col=4),
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
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=5, col=4), Vector(row=4, col=5)]),
                    VERTICAL: set([Vector(row=5, col=3), Vector(row=5, col=5)]),
                },
                'pawns': {
                    YELLOW: Vector(row=5, col=4),
                    GREEN: Vector(row=5, col=5),
                },
            },
            Vector(row=5, col=5),
        )),
        set([Vector(row=4, col=4)])
    )


def test_pawn_legal_moves_middle_3():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=5, col=0), Vector(row=7, col=1)]),
                    VERTICAL: set([Vector(row=6, col=0), Vector(row=6, col=1)]),
                },
                'pawns': {
                    YELLOW: Vector(row=7, col=1),
                    GREEN: Vector(row=6, col=1),
                },
            },
            Vector(row=7, col=1),
        )),
        set()
    )


def test_pawn_legal_moves_middle_4():
    assert_equal(
        set(pawn_legal_moves(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=1, col=5)]),
                },
                'pawns': {
                    YELLOW: Vector(row=2, col=5),
                    GREEN: Vector(row=2, col=6),
                },
            },
            Vector(row=2, col=6),
        )),
        set([Vector(row=1, col=6), Vector(row=2, col=7), Vector(row=3, col=6)])
    )


def test_is_correct_pawn_move_correct_1():
    assert_true(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=4, col=4)]),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=4),
                    GREEN: Vector(row=8, col=4),
                },
            },
            Vector(row=0, col=4),
            Vector(row=1, col=4),
        )
    )


def test_is_correct_pawn_move_correct_2():
    assert_true(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=4, col=1)]),
                    VERTICAL: set([Vector(row=2, col=7)]),
                },
                'pawns': {
                    YELLOW: Vector(row=2, col=3),
                    GREEN: Vector(row=6, col=5),
                },
            },
            Vector(row=6, col=5),
            Vector(row=5, col=5),
        )
    )


def test_is_correct_pawn_move_correct_3():
    assert_true(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=5, col=2)]),
                    VERTICAL: set([Vector(row=3, col=2)]),
                },
                'pawns': {
                    YELLOW: Vector(row=4, col=2),
                    GREEN: Vector(row=5, col=2),
                },
            },
            Vector(row=4, col=2),
            Vector(row=5, col=3),
        )
    )


def test_is_correct_pawn_move_wrong_1():
    assert_false(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=0),
                    GREEN: Vector(row=3, col=4),
                },
            },
            Vector(row=0, col=0),
            Vector(row=2, col=0),
        )
    )


def test_is_correct_pawn_move_wrong_2():
    assert_false(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=6, col=0),
                    GREEN: Vector(row=7, col=0),
                },
            },
            Vector(row=7, col=0),
            Vector(row=-1, col=6),
        )
    )


def test_is_correct_pawn_move_wrong_3():
    assert_false(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=5, col=7),
                    GREEN: Vector(row=5, col=8),
                },
            },
            Vector(row=5, col=7),
            Vector(row=5, col=9),
        )
    )


def test_is_correct_pawn_move_wrong_4():
    assert_false(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    Vector(row=4, col=4): YELLOW,
                    Vector(row=5, col=4): GREEN,
                },
            },
            Vector(row=5, col=4),
            Vector(row=2, col=4),
        )
    )


def test_is_correct_pawn_move_wrong_5():
    assert_false(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    Vector(row=3, col=3): YELLOW,
                    Vector(row=4, col=3): GREEN,
                },
            },
            Vector(row=3, col=3),
            Vector(row=3, col=3)
        )
    )


def test_is_correct_pawn_move_wrong_6():
    assert_false(
        is_correct_pawn_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=1, col=5),
                    GREEN: Vector(row=3, col=5),
                },
            },
            Vector(row=1, col=5),
            Vector(row=3, col=5)
        )
    )


def test_wall_intersects_1():
    assert_false(
        wall_intersects(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            VERTICAL,
            Vector(row=0, col=0),
        )
    )


def test_wall_intersects_2():
    assert_false(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set([
                        Vector(row=4, col=3),
                        Vector(row=4, col=5),
                        Vector(row=3, col=4),
                        Vector(row=5, col=4),
                    ]),
                    VERTICAL: set([
                        Vector(row=2, col=4),
                        Vector(row=6, col=4),
                    ]),
                },
            },
            VERTICAL,
            Vector(row=4, col=4),
        )
    )


def test_wall_intersects_3():
    assert_false(
        wall_intersects(
            {'placed_walls': {HORIZONTAL: set(), VERTICAL: set()}},
            HORIZONTAL,
            Vector(row=0, col=7),
        )
    )


def test_wall_intersects_4():
    assert_false(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set([
                        Vector(row=1, col=0),
                        Vector(row=1, col=4),
                    ]),
                    VERTICAL: set([
                        Vector(row=1, col=1),
                        Vector(row=0, col=2),
                        Vector(row=2, col=2),
                        Vector(row=1, col=3),
                    ]),
                },
            },
            HORIZONTAL,
            Vector(row=1, col=2),
        )
    )


def test_wall_intersects_5():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=6, col=4)]),
                    VERTICAL: set()
                },
            },
            HORIZONTAL,
            Vector(row=6, col=5),
        )
    )


def test_wall_intersects_6():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=1, col=4)]),
                    VERTICAL: set()
                }
            },
            HORIZONTAL,
            Vector(row=1, col=3),
        )
    )


def test_wall_intersects_7():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=7, col=7)])
                },
            },
            HORIZONTAL,
            Vector(row=7, col=7),
        )
    )


def test_wall_intersects_8():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=0, col=0)])
                },
            },
            VERTICAL,
            Vector(row=1, col=0),
        )
    )


def test_wall_intersects_9():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set([Vector(row=7, col=2)])
                },
            },
            VERTICAL,
            Vector(row=6, col=2),
        )
    )


def test_wall_intersects_10():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=2, col=2)]),
                    VERTICAL: set()
                },
            },
            VERTICAL,
            Vector(row=2, col=2),
        )
    )


def test_wall_intersects_11():
    assert_true(
        wall_intersects(
            {
                'placed_walls': {
                    HORIZONTAL: set([Vector(row=5, col=5)]),
                    VERTICAL: set(),
                },
            },
            HORIZONTAL,
            Vector(row=5, col=5),
        )
    )


def test_player_can_reach_goal_1():
    assert_true(
        player_can_reach_goal(
            {
                'placed_walls': {HORIZONTAL: set(), VERTICAL: set()},
                'pawns': {YELLOW: Vector(row=4, col=3)},
            },
            YELLOW,
        )
    )


def test_player_can_reach_goal_2():
    assert_true(
        player_can_reach_goal(
            {
                'placed_walls': {HORIZONTAL: set(), VERTICAL: set()},
                'pawns': {GREEN: Vector(row=5, col=2)},
            },
            GREEN,
        )
    )


def test_player_can_reach_goal_3():
    assert_true(
        player_can_reach_goal(
            {
                'placed_walls': {
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
                },
                'pawns': {YELLOW: Vector(row=0, col=4)},
            },
            YELLOW,
        )
    )


def test_player_can_reach_goal_4():
    assert_false(
        player_can_reach_goal(
            {
                'placed_walls': {
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
                },
                'pawns': {
                    YELLOW: Vector(row=4, col=4),
                },
            },
            YELLOW,
        )
    )


def test_player_can_reach_goal_5():
    assert_false(
        player_can_reach_goal(
            {
                'placed_walls': {
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
                },
                'pawns': {
                    GREEN: Vector(row=8, col=3),
                },
            },
            GREEN,
        )
    )


def test_is_correct_wall_move_1():
    assert_true(
        is_correct_wall_move(
            {
                'placed_walls': {
                    HORIZONTAL: set(),
                    VERTICAL: set(),
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=4),
                    GREEN: Vector(row=8, col=4),
                },
            },
            HORIZONTAL,
            Vector(row=0, col=4),
        )
    )


def test_is_correct_wall_move_2():
    assert_true(
        is_correct_wall_move(
            {
                'placed_walls': {
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
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=4),
                    GREEN: Vector(row=8, col=4),
                },
            },
            HORIZONTAL,
            Vector(row=5, col=6),
        )
    )


def test_is_correct_wall_move_3():
    assert_false(
        is_correct_wall_move(
            {
                'placed_walls': {
                    HORIZONTAL: set([
                        Vector(row=1, col=4),
                    ]),
                    VERTICAL: set([
                        Vector(row=0, col=1),
                        Vector(row=0, col=5),
                        Vector(row=1, col=3),
                    ])
                },
                'pawns': {
                    YELLOW: Vector(row=0, col=4),
                    GREEN: Vector(row=8, col=4)
                },
            },
            HORIZONTAL,
            Vector(row=0, col=2),
        )
    )
