import abc
import sys
import copy
import random
import collections

from quoridor.core import (
    YELLOW, GREEN, GOAL_ROW, WALL_BOARD_SIZE, STARTING_WALL_COUNT_2_PLAYERS,
    pawn_legal_moves, current_pawn_position, wall_legal_moves,
    is_correct_wall_move, adjacent_spaces_not_blocked, is_occupied,
    PLAYER_UTILITIES,
)


MAX_NUMBER_OF_CHOICES = 2 * (WALL_BOARD_SIZE ** 2)
# MAX_MISSING_CHOICES = 4 + 2 * 3 * STARTING_WALL_COUNT_2_PLAYERS
# MIN_NUMBER_OF_CHOICES_WITH_WALLS = MAX_NUMBER_OF_CHOICES - MAX_MISSING_CHOICES
# MIN_NUMBER_OF_WALL_CHOICES = MIN_NUMBER_OF_CHOICES_WITH_WALLS - 2

MAX_INTEGER = sys.maxint - 1


class Player(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def play(self, state):
        pass

    def __init__(self, game):
        self.game = game
        super(Player, self).__init__()


ONE_THIRD = 1.0/3


class RandomPlayer(Player):
    def __init__(self, *args, **kwargs):
        self.pawn_move_probability = kwargs.pop(
            'pawn_move_probability',
            ONE_THIRD
        )
        super(RandomPlayer, self).__init__(*args, **kwargs)

    def _play_pawn(self, state):
        positions = list(
            pawn_legal_moves(state, current_pawn_position(state))
        )
        return (None, random.choice(positions))

    def _play_wall(self, state):
        random_number = random.randint(0, MAX_NUMBER_OF_CHOICES)
        actions = []
        for number, action in enumerate(wall_legal_moves(state)):
            if number == random_number:
                action_type, position = action
                if not is_correct_wall_move(state, action_type, position):
                    continue
                return action
            else:
                actions.append(action)

        while True:
            action = random.choice(actions)
            action_type, position = action
            if not is_correct_wall_move(state, action_type, position):
                continue
            return action

    def play(self, state):
        if not state['walls'][state['on_move']] or (
                random.random() < self.pawn_move_probability):
            return self._play_pawn(state)
        return self._play_wall(state)


class RandomPlayerWithPath(RandomPlayer):
    def _play_pawn(self, state):
        current_position = current_pawn_position(state)
        to_visit = collections.deque(
            adjacent_spaces_not_blocked(state, current_position)
        )
        visited = set([current_position])
        paths = {}
        for position in set(to_visit):
            if is_occupied(state, position):
                to_visit.remove(position)
                jumps = adjacent_spaces_not_blocked(state, position)
                for jump in jumps:
                    to_visit.append(jump)
                    paths[jump] = [jump]
            else:
                paths[position] = [position]

        while to_visit:
            position = to_visit.popleft()
            if position.row == GOAL_ROW[state['on_move']]:
                return (None, paths[position][0])

            visited.add(position)
            for new_position in adjacent_spaces_not_blocked(state, position):
                if new_position not in visited:
                    to_visit.append(new_position)
                if new_position not in paths:
                    paths[new_position] = copy.copy(paths[position])
                    paths[new_position].append(new_position)

        raise InvalidMove('Player cannot reach the goal row.')


class QLPlayer(RandomPlayerWithPath):
    def __init__(self, *args, **kwargs):
        self.Q = kwargs.pop('Q', {})
        super(QLPlayer, self).__init__(*args, **kwargs)

    def play(self, state, path_probability=0.7):
        if random.random() < path_probability:
            return self._play_pawn(state)

        mq, best_action = self.find_mq_and_action(
            state,
            PLAYER_UTILITIES[state['on_move']]
        )
        return best_action

    def reward(self, state):
        if self.game.is_terminal(state):
            return self.game.utility(state, state['on_move']) * 10000
        return 0

    def set_Q(self, state, action, value):
        key = self.game.make_key(state)
        if key not in self.Q:
            self.Q[key] = {}
        self.Q[key][action] = value

    def get_Q(self, state, action):
        key = self.game.make_key(state)
        if key not in self.Q:
            return 0.0
        return self.Q[key].get(action, 0.0)

    def find_mq_and_action(self, state, multiplier):
        mq = multiplier * -MAX_INTEGER
        best_action = None
        for action in self.game.actions(state):
            Q = self.get_Q(state, action)
            if (multiplier * mq) < (multiplier * Q):
                mq = Q
                best_action = action
        return mq, best_action

    def learn(self, previous_state, last_action, current_state, alpha=0.1,
              gamma=0.9):
        mq = 0.0
        if not self.game.is_terminal(current_state):
            mq, best_action = self.find_mq_and_action(
                current_state,
                PLAYER_UTILITIES[current_state['on_move']]
            )

        reward = self.reward(current_state)
        q_value = self.get_Q(previous_state, last_action)
        q_value += alpha * (reward + gamma * mq - q_value)
        self.set_Q(previous_state, last_action, q_value)

    def save_Q(self, filename='q_values.txt'):
        with open(filename, 'w') as f:
            f.write(repr(self.Q))
