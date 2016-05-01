import re
import abc
import random
import operator
import itertools

from sqlalchemy.orm.exc import NoResultFound

from quoridor.commonsettings import DB_PATH
from quoridor.ai.perceptron import MLMCPerceptron
from quoridor.db.utils import (
    make_db_session,
    db_load_network,
    db_save_network,
    db_update_network,
)
from quoridor.core.game import (
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


class Player(object):
    __metaclass__ = abc.ABCMeta

    def __call__(self, context):
        return self.play(context)

    def __init__(self, game):
        self.game = game
        super(Player, self).__init__()


class HumanPlayer(Player):
    GAME_INPUT_PATTERN = (
        r'(?i)'
        r'(?P<type>menu|save|load|undo|quit|[hv]|[urdl]{1,2})?'
        r'(?P<number>[-+]?\d+)?'
        r'$'
    )
    GAME_INPUT_RE = re.compile(GAME_INPUT_PATTERN)

    def __init__(self, game, messages=None, game_controls=None,
                 fail_callback=None):
        super(HumanPlayer, self).__init__(game)
        self.messages = (
            messages if messages else {'enter_choice': 'enter choice:'}
        )
        self.controls = (
            game_controls if game_controls else set(['quit', 'unknown'])
        )
        self.fail_callback = fail_callback

    def play(self, context):
        while True:
            try:
                action = self.get_human_action()
                if action not in self.controls:
                    context.update(action)
                return action
            except InvalidMove as e:
                if self.fail_callback:
                    self.fail_callback(context, action, e)

    def get_human_action(self):
        user_input = raw_input(self.messages['enter_choice']).strip()
        if not user_input:
            return 'unknown'

        match = self.GAME_INPUT_RE.match(user_input)
        if match is None:
            return 'unknown'

        data = match.groupdict()
        # if not any([data.values()]):
        #     return self._unknown('human_human')

        if data['type'] is None:
            if data['number'] is None:
                return 'unknown'
            action = int(data['number'])
            if action in self.game.possible_game_actions:
                return action
            return 'unknown'

        data['type'] = data['type'].lower()
        if data['type'] in self.controls:
            return data['type']
        elif data['type'] in self.game.PAWN_MOVES:
            return self.game.PAWN_MOVES[data['type']] + self.game.wall_moves
        elif data['type'] not in ('h', 'v'):
            return 'unknown'
        elif data['number'] is None:
            return 'unknown'

        number = int(data['number'])
        if data['type'] == 'h' and number >= self.game.wall_board_positions:
            return 'unknown'

        direction_offset = 0
        if data['type'] == 'v':
            direction_offset = self.game.wall_board_positions
        return number + direction_offset


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

        context.history.append(self.game.wall_moves + move)
        context[player]['goal_cut'].clear()
        context[player]['blockers'] = self.game.path_blockers(
            context[player]['path'],
            context['crossers'],
            context[player]['goal_cut']
        )
        new_state[1 + player] = new_position
        new_state[0] = next_

    def play(self, context):
        player = context.state[0]
        next_ = FOLLOWING_PLAYER[player]
        new_state = list(context.state)
        self.move_pawn(new_state, context, player, next_)
        context['state'] = tuple(new_state)


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

    def should_move(self, context):
        # TODO: is there heurisic for defending wall?
        player = context.state[0]
        next_ = FOLLOWING_PLAYER[player]
        if not context.state[3 + player]:
            return True     # no walls left
        elif len(context[player]['path']) == 2:
            return True     # last winning move
        elif context.state[1 + player] in self.game.goal_positions[next_]:
            return True     # on the first line is probably the beginning
        elif len(context[next_]['blockers']) > 2:
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

    def play(self, context):
        """
        choose between shortest path and wall
        updates context for effectiveness with action played
        and returns new_state

        context can be initialized with make_context
        """
        # TODO: if state in self.openings... play by it

        player = context.state[0]
        next_ = FOLLOWING_PLAYER[player]
        new_state = list(context.state)

        if not self.should_move(context):  # try place good wall
            temp_state = new_state[:5] + [set(new_state[5])]
            for action in self.good_blockers(context, player, next_):
                if self._try_good_wall(new_state, temp_state, context, action):
                    context['state'] = tuple(new_state)
                    return
            # TODO: is there something more to try?

        self.move_pawn(new_state, context, player, next_)
        context['state'] = tuple(new_state)


class NetworkPlayer(Player):
    SIZES_PATTERN = r'\d+(_\d+)+'
    SIZES_NAME_RE = re.compile(SIZES_PATTERN)

    def __init__(self, game, db_name):
        super(NetworkPlayer, self).__init__(game)

        self.db_name = db_name
        db_session = make_db_session(DB_PATH)
        self.load_from_db(db_session)

    def load_from_db(self, db_session):
        try:
            network_attributes = db_load_network(db_session, self.db_name)
            self.perceptron = MLMCPerceptron(**network_attributes)
        except NoResultFound:
            message_fmt = 'Network {name!r} not found in db. Creating new...'
            print message_fmt.format(name=self.db_name),
            assert self.SIZES_NAME_RE.match(self.db_name)
            sizes = [int(size) for size in self.db_name.split('_')]
            self.perceptron = MLMCPerceptron(
                sizes,
                alpha=0.01,
                exploration_probability=0.1,
            )
            db_save_network(db_session, self.perceptron, name=self.db_name)
            print 'created'

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
        self.explore = False
        self.random_choose_from = frozenset()

    def activations_from_state(self, state):
        input_vector = tuple(self.input_vector_from_game_state(state))
        activations = tuple(self.perceptron.propagate_forward(input_vector))
        return activations

    def _choose_random(self):
        choices = self.random_choose_from
        for action in random.sample(choices, len(choices)):
            yield action

    def _choose_from_activations(self):
        q_values = self.activations[-1]
        q_values_to_action = sorted(
            enumerate(q_values),
            key=operator.itemgetter(1),
            reverse=True,
        )
        for action, value in q_values_to_action:
            yield action

    def play(self, context):
        # TODO: when learning, should it be here any randomness? e.g. first few
        #       q_values have similar probability to be chosend to play?
        self.activations = self.activations_from_state(context.state)
        if self.explore:
            choose_from = self._choose_random()
        else:
            choose_from = self._choose_from_activations()
        for action in choose_from:
            try:
                context.update(action)
                break
            except InvalidMove:
                # TODO: add to desired output vector with bad reward?
                pass
