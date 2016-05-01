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

ANTI_MOVE = {
    UP: DOWN,
    DOWN: UP,
    LEFT: RIGHT,
    RIGHT: LEFT,
    UPUP: DOWNDOWN,
    DOWNDOWN: UPUP,
    LEFTLEFT: RIGHTRIGHT,
    RIGHTRIGHT: LEFTLEFT,
    UPRIGHT: DOWNLEFT,
    DOWNLEFT: UPRIGHT,
    UPLEFT: DOWNRIGHT,
    DOWNRIGHT: UPLEFT,
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
        frozenset(),                                # walls
    )


def _make_blocker_positions(board_size):
    # assert board_size > 1
    blocker_positions = {}
    wall_board_size = board_size - 1
    wall_board_positions = wall_board_size ** 2
    shift = {HORIZONTAL: 0, VERTICAL: wall_board_positions}

    for position in range(board_size * board_size):
        row, col = divmod(position, board_size)
        blocker_positions[position] = {}

        if row:                # can move up
            blocker_positions[position][UP] = set()
            new_row = wall_board_size * (row - 1)
            if col:
                blocker_positions[position][UP].add(new_row + col - 1)
            if col != wall_board_size:
                blocker_positions[position][UP].add(new_row + col)

        if row != wall_board_size:  # can move down
            blocker_positions[position][DOWN] = set()
            new_row = wall_board_size * row
            if col:
                blocker_positions[position][DOWN].add(new_row + col - 1)
            if col != wall_board_size:
                blocker_positions[position][DOWN].add(new_row + col)

        new_row = wall_board_size * row + wall_board_positions
        if col != wall_board_size:  # can move right
            blocker_positions[position][RIGHT] = set()
            if row:
                blocker_positions[position][RIGHT].add(
                    new_row - wall_board_size + col
                )
            if row != wall_board_size:
                blocker_positions[position][RIGHT].add(new_row + col)

        if col:                # can move left
            blocker_positions[position][LEFT] = set()
            new_col = col - 1
            if row:
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
        self.all_actions = frozenset(range(self.all_moves))

    def is_wall_crossing(self, walls, wall):
        if wall in walls:
            return True

        if wall < self.wall_board_positions:
            return (
                wall + self.wall_board_positions in walls or \
                (wall % self.wall_board_size != 0 and (wall - 1) in walls) or \
                ((wall + 1) % self.wall_board_size != 0 and (wall + 1) in walls)
            )

        position = wall - self.wall_board_positions
        row = position // self.wall_board_size
        return (
            position in walls or \
            (row != 0 and (wall - self.wall_board_size) in walls) or \
            (
                row != (self.wall_board_size - 1) and \
                (wall + self.wall_board_size) in walls
            )
        )

    def wall_crossers(self, wall):
        actions = set((wall, ))
        if wall < self.wall_board_positions:
            actions.add(wall + self.wall_board_positions)
            col = wall % self.wall_board_size
            if col:
                actions.add(wall - 1)
            if col != self.wall_board_size - 1:
                actions.add(wall + 1)
        else:
            actions.add(wall - self.wall_board_positions)
            position = wall - self.wall_board_positions
            actions.add(position)
            row = position // self.wall_board_size
            if row:
                actions.add(wall - self.wall_board_size)
            if row != self.wall_board_size - 1:
                actions.add(wall + self.wall_board_size)
        return actions

    def crossing_actions(self, state):
        actions = set(state[5])
        for wall in state[5]:
            if wall < self.wall_board_positions:
                actions.add(wall + self.wall_board_positions)
                col = wall % self.wall_board_size
                if col:
                    actions.add(wall - 1)
                if col != self.wall_board_size - 1:
                    actions.add(wall + 1)
            else:
                position = wall - self.wall_board_positions
                actions.add(position)
                row = position // self.wall_board_size
                if row:
                    actions.add(wall - self.wall_board_size)
                if row != self.wall_board_size - 1:
                    actions.add(wall + self.wall_board_size)
        return actions

    def is_move_impossible(self, state, position, pawn_move):
        intercepting_walls = self.blocker_positions[position].get(pawn_move)
        return intercepting_walls is None or intercepting_walls & state[5]

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
        player_position = state[1 + player]
        to_visit = collections.deque((player_position, ))
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
                    if previous_position == player_position:
                        return path

            visited.add(position)
            for move, blockers in self.blocker_positions[position].items():
                if not blockers & state[5]:
                    new_position = position + self.move_deltas[move]
                    if new_position not in visited:
                        to_visit.append(new_position)
                    if new_position not in previous_positions:
                        previous_positions[new_position] = position

    def players_can_reach_goal(self, state):
        return bool(self.shortest_path(state, YELLOW)) and bool(
            self.shortest_path(state, GREEN)
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
                if self.is_wall_crossing(state[5], action):
                    raise InvalidMove('Wall crosses already placed walls!')
            new_state[5] = state[5].union((action, ))

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

    def undo(self, state, action):
        player = FOLLOWING_PLAYER[state[0]]
        new_state = list(state)
        new_state[0] = player
        if 0 <= action < self.wall_moves:
            if state[5] and action in state[5]:
                new_state[3 + player] += 1
                new_state[5] = new_state[5].difference((action, ))
                return tuple(new_state)
            raise InvalidMove('Cannot undo!')
        move = action - self.wall_moves
        if move < 12:
            anti_move = ANTI_MOVE[move]
            if self.is_valid_pawn_move(new_state, anti_move):
                new_state[1 + player] += sum([
                    self.move_deltas[pawn_move]
                    for pawn_move in PAWN_MOVE_PATHS[anti_move][0]
                ])
                return tuple(new_state)
        raise InvalidMove('Cannot undo!')

    # def actions(self, state):
    #     for position in pawn_legal_moves(state, current_pawn_position(state)):
    #         yield (None, position)

    #     for action in wall_legal_moves(state):
    #         yield action
