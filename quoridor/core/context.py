import itertools

from quoridor.core.game import (
    YELLOW,
    GREEN,
    PLAYER_COLOR_NAME,
    FOLLOWING_PLAYER,
    ANTI_MOVE,
    PAWN_MOVE_PATHS,
    InvalidMove,
)


CONTEXT_FMT = '''\
state: {state}
history: {history}
yellow: {yellow}
green: {green}
crossers({cross_num}): {crossers}
'''


class QuoridorContext(object):
    def __init__(self, game, **kwargs):
        self.game = game
        self._data = dict()

    def reset(self, state=None, players=None):
        state = state if state else self.game.initial_state()
        players = players if players else {YELLOW: {}, GREEN: {}}
        self._data['state'] = state
        self._data['start_state'] = state
        self._data['history'] = []
        self._data['crossers'] = self.game.crossing_actions(state)
        for color in (YELLOW, GREEN):
            path = self.game.shortest_path(state, color)
            color_name = PLAYER_COLOR_NAME[color]
            assert path is not None, 'no path to goal for ' + color_name
            blockers = self.game.path_blockers(path, self._data['crossers'])
            self._data[color] = {
                'name': players[color].get('name', ''),
                # 'player': players[color].get('player', None),
                'path': path,
                'blockers': blockers,
                'goal_cut': set(),  # TODO: consider using ordered set
            }

    def undo(self):
        action = self.last_action
        if action is None or not (0 <= action < self.game.all_moves):
            raise InvalidMove('Cannot undo!')
        new_state = list(self.state)
        current_player = new_state[0]
        previous_player = FOLLOWING_PLAYER[current_player]
        if 0 <= action < self.game.wall_moves:
            if not new_state[5] or action not in new_state[5]:
                raise InvalidMove('Cannot undo!')
            new_state[3 + previous_player] += 1
            new_state[5].remove(action)
            for color in (YELLOW, GREEN):
                self._data['crossers'] = self.game.crossing_actions(new_state)
                path = self.game.shortest_path(new_state, color)
                blockers = self.game.path_blockers(path, self._data['crossers'])
                self._data[color]['blockers'] = blockers
                self._data[color]['path'] = path
                self._data[color]['goal_cut'].clear()
        else:
            move = action - self.game.wall_moves
            anti_move = ANTI_MOVE[move]
            if not self.game.is_valid_pawn_move(new_state, anti_move):
                raise InvalidMove('Cannot undo!')
            new_state[1 + previous_player] += sum([
                self.game.move_deltas[pawn_move]
                for pawn_move in PAWN_MOVE_PATHS[anti_move][0]
            ])
            path = self.game.shortest_path(new_state, previous_player)
            blockers = self.game.path_blockers(path, self._data['crossers'])
            self._data[previous_player]['blockers'] = blockers
            self._data[previous_player]['path'] = path
            self._data[previous_player]['goal_cut'].clear()
        self._data['history'].pop()
        new_state[0] = previous_player
        self._data['state'] = tuple(new_state)

    def update(self, action, checks_on=True):
        assert not self.is_terminal
        player = self.state[0]
        if checks_on:
            state = self.game.execute_action(self.state, action)
        else:
            state = self.game.execute_action(self.state, action, False, False)

        self._data['history'].append(action)
        self._data['state'] = state
        if self.is_terminal:
            self._data[player]['path'] = [state[1 + player]]
            return

        if 0 <= action < self.game.wall_moves:  # wall
            new_crossers = self.game.wall_crossers(action)
            self._data['crossers'] = self._data['crossers'].union(new_crossers)
            for color in (YELLOW, GREEN):
                if action in self._data[color]['blockers']:
                    path = self.game.shortest_path(state, color)
                    self._data[color]['path'] = path
                    self._data[color]['blockers'] = self.game.path_blockers(
                        path,
                        self._data['crossers'],
                        self._data[color]['goal_cut']
                    )
            return state

        path = self._data[player]['path']
        if path[-2] == state[1 + player]:   # one step along the path
            path.pop()
        elif len(path) > 2 and path[-3] == state[1 + player]:  # jump
            path.pop()
            path.pop()
        else:
            # TODO: can this be optimized?
            self._data[player]['path'] = self.game.shortest_path(state, player)

        self._data[player]['goal_cut'].clear()
        self._data[player]['blockers'] = self.game.path_blockers(
            self._data[player]['path'],
            self._data['crossers'],
            self._data[player]['goal_cut']
        )

    @property
    def invalid_actions(self):
        invalid_pawn_moves = [
            move + self.game.wall_moves
            for move in range(12)
            if not self.game.is_valid_pawn_move(self.state, move)
        ]
        return itertools.chain(
            self._data['crossers'],
            self.yellow['goal_cut'],
            self.green['goal_cut'],
            invalid_pawn_moves,
        )

    @property
    def state(self):
        return self._data['state']

    @property
    def player(self):
        return self.state[0]

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    @property
    def yellow(self):
        return self._data[YELLOW]

    @property
    def green(self):
        return self._data[GREEN]

    @property
    def is_terminal(self):
        return self.game.is_terminal(self.state)

    @property
    def history(self):
        return self._data['history']

    @property
    def last_action(self):
        if self._data['history']:
            return self._data['history'][-1]

    def __str__(self):
        return CONTEXT_FMT.format(
            state=self.state,
            history=self.history,
            yellow=self.yellow,
            green=self.green,
            cross_num=len(self._data['crossers']),
            crossers=self._data['crossers'],
        )
