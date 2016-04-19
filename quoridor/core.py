import collections

# TODO: documentation


HORIZONTAL = 0
VERTICAL = 1
YELLOW = 0
GREEN = 1
PLAYER_COLOR_NAME = {YELLOW: 'Yellow', GREEN: 'Green'}
FOLLOWING_PLAYER = {YELLOW: GREEN, GREEN: YELLOW}
PLAYER_UTILITIES = {YELLOW: 1, GREEN: -1}
STARTING_WALL_COUNT = 10

UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3

UPUP = 4
RIGHTRIGHT = 5
DOWNDOWN = 6
LEFTLEFT = 7

UPRIGHT = 8
UPLEFT = 9
DOWNRIGHT = 10
DOWNLEFT = 11

PAWN_MOVE_PATHS = {
    0: [[UP]],
    1: [[RIGHT]],
    2: [[DOWN]],
    3: [[LEFT]],

    4: [[UP, UP]],
    5: [[RIGHT, RIGHT]],
    6: [[DOWN, DOWN]],
    7: [[LEFT, LEFT]],

    8: [[UP, RIGHT], [RIGHT, UP]],
    9: [[UP, LEFT], [LEFT, UP]],
    10: [[DOWN, RIGHT], [RIGHT, DOWN]],
    11: [[DOWN, LEFT], [LEFT, DOWN]],
}

BOARD_SIZE_DEFAULT = 9


def _make_initial_state(board_size):
    half, mod = divmod(board_size, 2)
    return (
        YELLOW,                                     # on_move
        half,                                       # YELLOW's position
        (board_size ** 2) - half - int(bool(mod)),  # GREEN's position
        STARTING_WALL_COUNT,                        # YELLOW's walls
        STARTING_WALL_COUNT,                        # GREEN's walls
        # TODO: only one frozenset for all walls 0...127
        frozenset(),                                # horizontal walls
        frozenset(),                                # vertical walls
    )


def _make_blocker_positions(board_size):
    # assert board_size > 1
    blocker_positions = {}
    wall_board_size = board_size - 1
    for position in range(board_size * board_size):
        row = position // board_size
        col = position % board_size
        blocker_positions[position] = {}

        if row != 0:                # can move up
            blocker_positions[position][UP] = set()
            new_row = wall_board_size * (row - 1)
            if col != 0:
                blocker_positions[position][UP].add(new_row + col - 1)
            if col != wall_board_size:
                blocker_positions[position][UP].add(new_row + col)

        if col != wall_board_size:  # can move right
            blocker_positions[position][RIGHT] = set()
            new_row = wall_board_size * row
            if row != 0:
                blocker_positions[position][RIGHT].add(
                    new_row - wall_board_size + col
                )
            if row != wall_board_size:
                blocker_positions[position][RIGHT].add(new_row + col)

        if row != wall_board_size:  # can move down
            blocker_positions[position][DOWN] = set()
            new_row = wall_board_size * row
            if col != 0:
                blocker_positions[position][DOWN].add(new_row + col - 1)
            if col != wall_board_size:
                blocker_positions[position][DOWN].add(new_row + col)

        if col != 0:                # can move left
            blocker_positions[position][LEFT] = set()
            new_col = col - 1
            new_row = wall_board_size * row
            if row != 0:
                blocker_positions[position][LEFT].add(
                    new_row - wall_board_size + new_col
                )
            if row != wall_board_size:
                blocker_positions[position][LEFT].add(new_row + new_col)

    return blocker_positions


def _make_goal_positions(board_size):
    return {
        YELLOW: frozenset(
            range((board_size - 1) * board_size, board_size ** 2)
        ),
        GREEN: frozenset(range(board_size)),
    }


def _make_move_deltas(board_size):
    return {
        UP: -board_size,
        RIGHT: +1,
        DOWN: +board_size,
        LEFT: -1,
    }


def _make_delta_moves(board_size):
    return {
        -board_size: UP,
        +1: RIGHT,
        +board_size: DOWN,
        -1: LEFT,

        -2 * board_size: UPUP,
        +2: RIGHTRIGHT,
        2 * board_size: DOWNDOWN,
        -2: LEFTLEFT,

        1-board_size: UPRIGHT,
        -1-board_size: UPLEFT,
        1+board_size: DOWNRIGHT,
        board_size-1: DOWNLEFT,
    }


def is_horizontal_wall_crossing(board_size, horizontal_walls, vertical_walls,
                                wall):
    wall_board_size = board_size - 1
    if wall in horizontal_walls:
        return True
    elif wall in vertical_walls:
        return True
    elif wall % wall_board_size != 0 and (wall - 1) in horizontal_walls:
        return True
    elif (wall + 1) % wall_board_size != 0 and (wall + 1) in horizontal_walls:
        return True
    else:
        return False


def is_vertical_wall_crossing(board_size, horizontal_walls, vertical_walls,
                              wall):
    wall_board_size = board_size - 1
    row = wall // wall_board_size
    if wall in horizontal_walls:
        return True
    elif wall in vertical_walls:
        return True
    elif row != 0 and (wall - wall_board_size) in vertical_walls:
        return True
    elif row != (wall_board_size - 1) and (
            (wall + wall_board_size) in vertical_walls):
        return True
    else:
        return False


IS_WALL_CROSSING = {
    0: is_horizontal_wall_crossing,
    1: is_vertical_wall_crossing,
}


def horizontal_crossers(state, wall_board_size, wall_board_positions, wall):
    yield wall
    yield wall + wall_board_positions
    col = wall % wall_board_size
    if col != 0:
        yield wall - 1
    if col != wall_board_size - 1:
        yield wall + 1


def vertical_crossers(state, wall_board_size, wall_board_positions, wall):
    yield wall
    yield wall + wall_board_positions
    row = wall // wall_board_size
    if row != 0:
        yield wall - wall_board_size + wall_board_positions
    if row != wall_board_size - 1:
        yield wall + wall_board_size + wall_board_positions


def crossing_actions(state, wall_board_size):
    actions = set()
    wall_board_positions = wall_board_size ** 2
    for wall in state[5]:
        crossers = horizontal_crossers(
            state,
            wall_board_size,
            wall_board_positions,
            wall
        )
        for crosser in crossers:
            actions.add(crosser)

    for wall in state[6]:
        crossers = vertical_crossers(
            state,
            wall_board_size,
            wall_board_positions,
            wall
        )
        for crosser in crossers:
            actions.add(crosser)

    return actions


class InvalidMove(Exception):
    pass


class Quoridor2(object):

    def __init__(self, board_size=BOARD_SIZE_DEFAULT):
        assert board_size > 2
        # assert int(board_size) == board_size
        self.board_size = board_size
        self.board_positions = board_size ** 2
        self.wall_board_size = board_size - 1
        self.wall_board_positions = self.wall_board_size ** 2
        self.wall_moves = 2 * self.wall_board_positions
        self.all_moves = self.wall_moves + 12

        self.blocker_positions = _make_blocker_positions(self.board_size)
        self.goal_positions = _make_goal_positions(self.board_size)
        self.move_deltas = _make_move_deltas(self.board_size)
        self.delta_moves = _make_delta_moves(self.board_size)

    def is_move_impossible(self, state, position, pawn_move):
        intercepting_walls = self.blocker_positions[position].get(pawn_move)
        return intercepting_walls is None or (
            intercepting_walls & state[5 + (pawn_move % 2)]
        )

    def is_valid_pawn_move(self, state, move):
        current_pawn = state[1 + state[0]]
        other_pawn = state[1 + FOLLOWING_PLAYER[state[0]]]
        pawn_move_paths = PAWN_MOVE_PATHS.get(move, [])

        if 0 <= move <= 3:
            next_position = current_pawn + self.move_deltas[move]
            if next_position == other_pawn:
                return False
            return not self.is_move_impossible(state, current_pawn, move)

        for pawn_moves in pawn_move_paths:
            next_position = current_pawn + self.move_deltas[pawn_moves[0]]
            if next_position != other_pawn:
                continue

            position = current_pawn
            for pawn_move in pawn_moves:
                if self.is_move_impossible(state, position, pawn_move):
                    break
                position += self.move_deltas[pawn_move]
            else:
                return True
        return False

    def shortest_path(self, state, player, avoid=None):
        avoid = avoid or set()
        current_position = state[1 + player]
        to_visit = collections.deque((current_position, ))
        visited = set()
        previous_positions = {}

        while to_visit:
            position = to_visit.popleft()
            if position in visited:
                continue

            if position in self.goal_positions[player] and (
                    position not in avoid):
                # TODO: consider using ordered set:
                path = [position]
                while True:
                    previous_position = previous_positions.get(path[-1])
                    path.append(previous_position)
                    if previous_position == current_position:
                        return path

            visited.add(position)
            for move in self.blocker_positions[position]:
                placed_walls = state[5 + (move % 2)]
                intercepting_walls = self.blocker_positions[position][move]
                if placed_walls is None or not (
                        intercepting_walls & placed_walls):
                    new_position = position + self.move_deltas[move]
                    if new_position not in visited:
                        to_visit.append(new_position)
                    if new_position not in previous_positions:
                        previous_positions[new_position] = position

    def player_can_reach_goal(self, state, player):
        player_position = state[1 + player]
        to_visit = set([player_position])
        visited = set()
        while to_visit:
            position = to_visit.pop()
            if position in self.goal_positions[player]:
                return True
            visited.add(position)
            for move in self.blocker_positions[position]:
                intercepting_walls = self.blocker_positions[position][move]
                placed_walls = state[5 + (move % 2)]
                if not intercepting_walls & placed_walls:
                    new_position = position + self.move_deltas[move]
                    if new_position not in visited:
                        to_visit.add(new_position)
        return False

    def players_can_reach_goal(self, state):
        return self.player_can_reach_goal(state, YELLOW) and (
            self.player_can_reach_goal(state, GREEN)
        )

    def initial_state(self):
        return _make_initial_state(self.board_size)

    def is_terminal(self, state):
        if state[1] in self.goal_positions[YELLOW]:
            return True
        elif state[2] in self.goal_positions[GREEN]:
            return True
        else:
            return False

    def utility(self, state, player):
        if self.is_terminal(state):
            return PLAYER_UTILITIES[player]
        return 0

    def execute_action(self, state, action, check_crossing=True,
                       check_paths_to_goal=True):
        player = state[0]
        new_state = list(state)

        if 0 <= action < self.wall_moves:                   # wall
            if not state[3 + player]:
                raise InvalidMove('Not enough walls!')

            if check_crossing:
                direction = int(action >= self.wall_board_positions)
                wall = action - direction * self.wall_board_positions
                is_wall_crossing = IS_WALL_CROSSING[direction](
                    self.board_size, state[5], state[6], wall
                )
                if is_wall_crossing:
                    raise InvalidMove('Wall crosses already placed walls!')
                new_state[5 + direction] = state[5 + direction].union((wall, ))

            if check_paths_to_goal:
                if not self.players_can_reach_goal(new_state):
                    raise InvalidMove('Pawn can not reach the goal!')

            new_state[3 + player] -= 1

        elif self.wall_moves <= action <= self.all_moves:   # pawn move
            move = action - self.wall_moves
            if not self.is_valid_pawn_move(state, move):
                raise InvalidMove('Pawn cannot move there!')

            new_state[1 + player] += sum([
                self.move_deltas[pawn_move]
                for pawn_move in PAWN_MOVE_PATHS[move][0]
            ])

        else:
            raise InvalidMove('Unknown action {action}!'.format(action=action))

        new_state[0] = FOLLOWING_PLAYER[player]
        return tuple(new_state)

    # def actions(self, state):
    #     for position in pawn_legal_moves(state, current_pawn_position(state)):
    #         yield (None, position)

    #     for action in wall_legal_moves(state):
    #         yield action

    # def undo(self, state, action):
    #     direction, position = action
    #     last_player = FOLLOWING_PLAYER[state['on_move']]
    #     if direction is None:
    #         pawn_position = state['pawns'][last_player]
    #         if not is_correct_pawn_move(state, pawn_position, position):
    #             raise InvalidMove('Incorrect undo move.')
    #         state['pawns'][last_player] = position
    #     else:
    #         if position not in state['placed_walls'][direction]:
    #             raise InvalidMove('Incorrect undo move.')
    #         state['placed_walls'][direction].remove(position)
    #         state['walls'][last_player] += 1
    #     state['on_move'] = last_player

# def wall_affects(state, direction, wall_position):
#     yield direction, wall_position
#     yield direction, add_direction(wall_position, direction)
#     yield direction, substract_direction(wall_position, direction)
#     yield ORTOGONAL_DIRECTION[direction], wall_position


# def wall_legal_moves(state):
#     if not state['walls'][state['on_move']]:
#         return
#     # TODO: what to do with leaving the paths to goals?
#     result_walls = {
#         HORIZONTAL: set(ALL_WALL_POSITIONS),
#         VERTICAL: set(ALL_WALL_POSITIONS),
#     }
#     for dimension, walls in state['placed_walls'].items():
#         for position in walls:
#             affected = wall_affects(state, dimension, position)
#             for direction, position in affected:
#                 result_walls[direction].discard(position)
#
#     for direction, walls in result_walls.items():
#         for wall in walls:
#             yield (direction, wall)
