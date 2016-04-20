import re
import abc
import sys
import copy
import random
import itertools
import collections

from core import (
    YELLOW,
    GREEN,
    FOLLOWING_PLAYER,
    UP,
    RIGHT,
    DOWN,
    LEFT,

    PAWN_MOVE_PATHS,

    InvalidMove,
)

from db import (
    make_db_session,
    db_load_network,
    db_save_network,
    db_update_network,
)
from ai import MLMCPerceptron


class Player(object):
    __metaclass__ = abc.ABCMeta

    def __call__(self, state, context):
        return self.play(state, context)

    @abc.abstractmethod
    def play(self, state, context):
        pass

    def __init__(self, game):
        self.game = game
        super(Player, self).__init__()


class PathPlayer(Player):
    def move_pawn(self, new_state, context, player, next_):
        current_position = context[player]['path'].pop()
        new_position = context[player]['path'][-1]
        if new_position == new_state[1 + next_]:
            if len(context[player]['path']) > 1:    # jump
                context[player]['path'].pop()
                new_position = context[player]['path'][-1]
            else: # opponent occupies final position
                final = context[player]['path'][-1]
                new_path = self.game.shortest_path(
                    new_state, player, set([final])
                )
                if new_path is None or len(new_path) != 3:
                    context[player]['path'].append(current_position)
                    if player == YELLOW:
                        new_position = (
                            current_position + self.game.move_deltas[UP]
                        )
                    else:
                        new_position = (
                            current_position + self.game.move_deltas[DOWN]
                        )
                    context[player]['path'].append(new_position)
                else:   # ok to finish
                    new_position = new_path[0]

        move = self.game.delta_moves[new_position - current_position]

        context['history'].append(self.game.wall_moves + move)
        context[player]['goal_cut'].clear()
        context[player]['blockers'] = self.game.path_blockers(
            context[player]['path'],
            context['crossers'],
            context[player]['goal_cut']
        )
        new_state[1 + player] = new_position
        new_state[0] = next_

    def play(self, state, context):
        player = state[0]
        next_ = FOLLOWING_PLAYER[player]
        new_state = list(state)
        self.move_pawn(new_state, context, player, next_)
        return tuple(new_state)


class HeuristicPlayer(PathPlayer):
    def __init__(self, game, pawn_moves=0.6, **kwargs):
        super(HeuristicPlayer, self).__init__(game)
        self.pawn_moves = pawn_moves

    def good_blockers(self, context, player, next_):
        for action in context[next_]['blockers']:
            if action not in context[player]['blockers']:
                if action not in context['crossers']:
                    if action not in context[next_]['goal_cut']:
                        yield action

    def should_move(self, state, context):
        # TODO: is there heurisic for defending wall?
        player = state[0]
        next_ = FOLLOWING_PLAYER[player]
        if not state[3 + player]:
            return True     # no walls left
        elif len(context[player]['path']) == 2:
            return True     # last winning move
        elif state[1 + player] in self.game.goal_positions[next_]:
            return True     # on the first line is probably the beginning
        elif len(context[next_]['blockers']) > 3:
            # has enough time to block at least once in the future
            return random.random() < self.pawn_moves
        else:
            # probably one of the last changes to block
            return False

    def _try_good_wall(self, state, temp_state, context, action):
        next_ = FOLLOWING_PLAYER[state[0]]
        temp_state[5].add(action)
        new_opponent_path = self.game.shortest_path(temp_state, next_)
        if new_opponent_path is None:
            temp_state[5].remove(action)
            context[next_]['goal_cut'].add(action)
            return False
        # TODO: may be better if played only when making opponents path longer
        state[5] = frozenset(temp_state[5])
        state[3 + state[0]] -= 1
        context[next_]['path'] = new_opponent_path
        new_crossers = self.game.wall_crossers(action)
        context['crossers'] = context['crossers'].union(new_crossers)
        context[next_]['blockers'] = self.game.path_blockers(
            new_opponent_path,
            context['crossers'],
            context[next_]['goal_cut']
        )
        state[0] = next_
        context['history'].append(action)
        return True

    def play(self, state, context):
        """
        choose between shortest path and wall
        updates context for effectiveness with action played
        and returns new_state

        context can be initialized with make_context
        """
        # TODO: if state in self.openings... play by it

        player = state[0]
        next_ = FOLLOWING_PLAYER[player]
        new_state = list(state)

        if not self.should_move(state, context):  # try place good wall
            temp_state = new_state[:5] + [set(new_state[5])]
            for action in self.good_blockers(context, player, next_):
                if self._try_good_wall(new_state, temp_state, context, action):
                    return tuple(new_state)
            # TODO: is there something more to try?

        self.move_pawn(new_state, context, player, next_)
        return tuple(new_state)


class NetworkPlayer(Player):
    SIZES_PATTERN = r'\d+(_\d+)+'
    SIZES_NAME_RE = re.compile(SIZES_PATTERN)

    def __init__(self, game, db_name, create=False):
        super(NetworkPlayer, self).__init__(game)

        self.db_name = db_name
        db_session = make_db_session('data.db')     # TODO: fixed/variable?
        if create:
            assert self.SIZES_NAME_RE.match(db_name)
            sizes = [int(size) for size in db_name.split('_')]
            self.perceptron = MLMCPerceptron(sizes)
            db_save_network(db_session, self.perceptron, name=self.db_name)
        else:
            self.load_from_db(db_session)

    def load_from_db(self, db_session):
        network_attributes = db_load_network(db_session, self.db_name)
        self.perceptron = MLMCPerceptron(**network_attributes)

    def update_in_db(self, db_session):
        db_update_network(db_session, self.db_name, self.perceptron)

    def input_vector_from_game_state(self, state):
        """
        1: player on the move
        2: yellow player position (0, 1, ..., 80)
        3: green player position
        4: yellow player walls stock (0, ..., 10)
        5: gren player walls stock

        6...69: horizonal walls (0 or 1)
        70...133: vecrical walls
        """

        # TODO: add shortest path lengths for both players?
        return itertools.chain(
            state[:5],
            [int(i in state[5]) for i in range(self.game.wall_moves)],
        )


class QlearningNetworkPlayer(NetworkPlayer):
    ORDER = {YELLOW: reversed, GREEN: sorted}

    def __init__(self, *args, **kwargs):
        assert args
        if len(args) < 2:
            args += (kwargs.pop('db_name', '133_200_140'), )
        super(QlearningNetworkPlayer, self).__init__(*args, **kwargs)

    def activations_from_state(self, state):
        input_vector = tuple(self.input_vector_from_game_state(state))
        activations = tuple(self.perceptron.propagate_forward(input_vector))
        return activations

    def play(self, state, context):
        # TODO: when learning, should it be here any randomness? e.g. first few
        #       q_values have similar probability to be chosend to play?
        self.activations = self.activations_from_state(state)
        q_values = self.activations[-1]
        q_values_to_action = self.ORDER[state[0]]([
            (value, action) for action, value in enumerate(q_values)
        ])
        for value, action in q_values_to_action:
            try:
                new_state = self.game.execute_action(state, action)
                context['history'].append(action)
                if not self.game.is_terminal(new_state):
                    self.game.update_context(new_state, context)
                break
            except InvalidMove:
                # TODO: add to desired output vector with bad reward?
                pass
        return new_state

    def invalid_actions(self, state, context):
        invalid_pawn_moves = [
            move + 128
            for move in range(12)
            if not self.game.is_valid_pawn_move(state, move)
        ]
        return itertools.chain(
            context['crossers'],
            context[YELLOW]['goal_cut'],
            context[GREEN]['goal_cut'],
            invalid_pawn_moves,
        )

    def desired_output_vector(self, player, invalid_actions, old_activations,
                              last_action, new_state, new_activations):
        reward = 100 + player * (-200)
        desired_output_vector = copy.deepcopy(old_activations[-1])

        for action in invalid_actions:
            desired_output_vector[action] -= reward

        if player == YELLOW:
            best_value = max(new_activations[-1])
        else:
            best_value = min(new_activations[-1])
        desired_output_vector[last_action] = best_value

        if self.game.is_terminal(new_state):
            desired_output_vector[last_action] += reward
        return desired_output_vector

    def learn(self, old_activations, desired_output):
        self.perceptron.propagate_backward(old_activations, desired_output)


# MAX_NUMBER_OF_CHOICES = 2 * (WALL_BOARD_SIZE ** 2)
# # MAX_MISSING_CHOICES = 4 + 2 * 3 * STARTING_WALL_COUNT_2_PLAYERS
# # MIN_NUMBER_OF_CHOICES_WITH_WALLS = MAX_NUMBER_OF_CHOICES - MAX_MISSING_CHOICES
# # MIN_NUMBER_OF_WALL_CHOICES = MIN_NUMBER_OF_CHOICES_WITH_WALLS - 2
# 
# MAX_INTEGER = sys.maxint - 1
# 
# 
# ONE_THIRD = 1.0/3
# 
# 
# class RandomPlayer(Player):
#     def __init__(self, *args, **kwargs):
#         self.pawn_move_probability = kwargs.pop(
#             'pawn_move_probability',
#             ONE_THIRD
#         )
#         super(RandomPlayer, self).__init__(*args, **kwargs)
# 
#     def _play_pawn(self, state):
#         positions = list(
#             pawn_legal_moves(state, current_pawn_position(state))
#         )
#         return (None, random.choice(positions))
# 
#     def _play_wall(self, state):
#         random_number = random.randint(0, MAX_NUMBER_OF_CHOICES)
#         actions = []
#         for number, action in enumerate(wall_legal_moves(state)):
#             if number == random_number:
#                 action_type, position = action
#                 if not is_correct_wall_move(state, action_type, position):
#                     continue
#                 return action
#             else:
#                 actions.append(action)
# 
#         while True:
#             action = random.choice(actions)
#             action_type, position = action
#             if not is_correct_wall_move(state, action_type, position):
#                 continue
#             return action
# 
#     def play(self, state):
#         if not state['walls'][state['on_move']] or (
#                 random.random() < self.pawn_move_probability):
#             return self._play_pawn(state)
#         return self._play_wall(state)
# 
# 
# class RandomPlayerWithPath(RandomPlayer):
#     def _play_pawn(self, state):
#         current_position = current_pawn_position(state)
#         to_visit = collections.deque(
#             adjacent_spaces_not_blocked(state, current_position)
#         )
#         visited = set([current_position])
#         paths = {}
#         for position in set(to_visit):
#             if is_occupied(state, position):
#                 to_visit.remove(position)
#                 jumps = adjacent_spaces_not_blocked(state, position)
#                 for jump in jumps:
#                     to_visit.append(jump)
#                     paths[jump] = [jump]
#             else:
#                 paths[position] = [position]
# 
#         while to_visit:
#             position = to_visit.popleft()
#             if position.row == GOAL_ROW[state['on_move']]:
#                 return (None, paths[position][0])
# 
#             visited.add(position)
#             for new_position in adjacent_spaces_not_blocked(state, position):
#                 if new_position not in visited:
#                     to_visit.append(new_position)
#                 if new_position not in paths:
#                     paths[new_position] = copy.copy(paths[position])
#                     paths[new_position].append(new_position)
# 
#         raise InvalidMove('Player cannot reach the goal row.')
# 
# 
# class QLPlayer(RandomPlayerWithPath):
#     def __init__(self, *args, **kwargs):
#         self.Q = kwargs.pop('Q', {})
#         super(QLPlayer, self).__init__(*args, **kwargs)
# 
#     def play(self, state, path_probability=0.7):
#         if random.random() < path_probability:
#             return self._play_pawn(state)
# 
#         mq, best_action = self.find_mq_and_action(
#             state,
#             PLAYER_UTILITIES[state['on_move']]
#         )
#         return best_action
# 
#     def reward(self, state):
#         if self.game.is_terminal(state):
#             return self.game.utility(state, state['on_move']) * 10000
#         return 0
# 
#     def set_Q(self, state, action, value):
#         key = self.game.make_key(state)
#         if key not in self.Q:
#             self.Q[key] = {}
#         self.Q[key][action] = value
# 
#     def get_Q(self, state, action):
#         key = self.game.make_key(state)
#         if key not in self.Q:
#             return 0.0
#         return self.Q[key].get(action, 0.0)
# 
#     def find_mq_and_action(self, state, multiplier):
#         mq = multiplier * -MAX_INTEGER
#         best_action = None
#         for action in self.game.actions(state):
#             Q = self.get_Q(state, action)
#             if (multiplier * mq) < (multiplier * Q):
#                 mq = Q
#                 best_action = action
#         return mq, best_action
# 
#     def learn(self, previous_state, last_action, current_state, alpha=0.1,
#               gamma=0.9):
#         mq = 0.0
#         if not self.game.is_terminal(current_state):
#             mq, best_action = self.find_mq_and_action(
#                 current_state,
#                 PLAYER_UTILITIES[current_state['on_move']]
#             )
# 
#         reward = self.reward(current_state)
#         q_value = self.get_Q(previous_state, last_action)
#         q_value += alpha * (reward + gamma * mq - q_value)
#         self.set_Q(previous_state, last_action, q_value)
# 
#     def save_Q(self, filename='q_values.txt'):
#         with open(filename, 'w') as f:
#             f.write(repr(self.Q))
