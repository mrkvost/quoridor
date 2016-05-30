import os
import time
import random
import numpy as np
import tensorflow as tf

from optparse import OptionParser

from core.game import YELLOW, GREEN, Quoridor2
from core.context import QuoridorContext
from ai.players import (
    Player,
    PathPlayer,
    RandomPlayerWithPath,
    HeuristicPlayer,
    HumanPlayer,
)
from ai.utils import input_vector_from_game_state, calculate_input_size
from quoridor import ConsoleGame

# MLP parameters
INPUT_LAYER_SIZE = 151
HIDDEN_LAYER_SIZE = 100
OUTPUT_LAYER_SIZE = 140
LEARNING_RATE = 0.01
MINI_BATCH_SIZE = 100
REWARD_FACTOR = 100

# Q-learning parameters
FUTURE_REWARD_DISCOUNT = 0.99
GAME_COUNT = 10000


def train():
    # INIT MLP WEIGHTS
    W_hid = tf.Variable(tf.truncated_normal([INPUT_LAYER_SIZE, HIDDEN_LAYER_SIZE], stddev=0.01))
    b_hid = tf.Variable(tf.constant(0.01, shape=[HIDDEN_LAYER_SIZE]))

    W_out = tf.Variable(tf.truncated_normal([HIDDEN_LAYER_SIZE, OUTPUT_LAYER_SIZE], stddev=0.01))
    b_out = tf.Variable(tf.constant(0.01, shape=[OUTPUT_LAYER_SIZE]))

    # INIT LAYERS
    input_layer = tf.placeholder(tf.float32, [None, INPUT_LAYER_SIZE])
    hidden_layer = tf.sigmoid(tf.matmul(input_layer, W_hid) + b_hid)
    output_layer = tf.matmul(hidden_layer, W_out) + b_out

    # PLACEHOLDER FOR DESIRED OUTPUT
    desired = tf.placeholder(tf.float32, [None, OUTPUT_LAYER_SIZE])

    # COST FUNCTION - MEAN SQUARE ERROR
    mse = tf.reduce_mean(tf.square(desired - output_layer))

    # ONE TRAINING STEP
    train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(mse)


    # INIT GAME
    game = Quoridor2()
    context = QuoridorContext(game)
    heuristic = HeuristicPlayer(game)
    players = {
        YELLOW: {'name': 'heuristic', 'player': heuristic},
        GREEN: {'name': 'heuristic', 'player': heuristic},
    }

    # PLACEHOLDERS
    state_min_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    action_min_vector = np.zeros([MINI_BATCH_SIZE], dtype=np.int32)
    reward_min_vector = np.zeros([MINI_BATCH_SIZE])

    state_max_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    action_max_vector = np.zeros([MINI_BATCH_SIZE], dtype=np.int32)
    reward_max_vector = np.zeros([MINI_BATCH_SIZE])

    next_state_min_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    next_state_max_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])

    desired_vectors = tf.Variable(tf.zeros([MINI_BATCH_SIZE, OUTPUT_LAYER_SIZE]))
    des = tf.Variable(tf.zeros([MINI_BATCH_SIZE * OUTPUT_LAYER_SIZE]))

    # INIT TENSORFLOW
    session = tf.Session()
    init = tf.initialize_all_variables()
    session.run(init)
    saver = tf.train.Saver()

    context.reset(players=players)
    state = input_vector_from_game_state(context)
    state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])

    i = 0
    move_min = 0
    move_max = 0
    while i < GAME_COUNT:
        if context.state[0] == GREEN: # min turn
            # store current state
            state_min_vectors[move_min, :] = state

            # proceed to next state
            heuristic.play(context)
            next_state = input_vector_from_game_state(context)
            next_state = np.array(list(next_state)).reshape([1, INPUT_LAYER_SIZE])

            # store action
            action_min_vector[move_min] = (140 * move_min) + context.last_action

            # store reward
            reward_min_vector[move_min] = context.is_terminal * (1 - context.state[0] * 2) * REWARD_FACTOR

            # store next state
            next_state_min_vectors[move_min, :] = next_state

            move_min += 1
        else: # max turn
            # store current state
            state_max_vectors[move_max, :] = state

            # proceed to next state
            heuristic.play(context)
            next_state = input_vector_from_game_state(context)
            next_state = np.array(list(next_state)).reshape([1, INPUT_LAYER_SIZE])

            # store action
            action_max_vector[move_max] = (140 * move_max) + context.last_action

            # store reward
            reward_max_vector[move_max] = context.is_terminal * (1 - context.state[0] * 2) * REWARD_FACTOR

            # store next state
            next_state_max_vectors[move_max, :] = next_state

            move_max += 1


        if context.is_terminal:
            i += 1
            print('GAME ', i)
            context.reset(players=players)
            state = input_vector_from_game_state(context)
            state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])
        else:
            state = next_state

        if move_min == MINI_BATCH_SIZE:
            mq = session.run(tf.reduce_min(output_layer, reduction_indices=1), feed_dict={input_layer: next_state_min_vectors})
            new_q = tf.add(FUTURE_REWARD_DISCOUNT * mq, reward_min_vector)
            desired_vectors.assign(session.run(output_layer, feed_dict={input_layer: state_min_vectors}))
            des.assign(tf.reshape(desired_vectors, [140 * 100]))
            des.assign(tf.scatter_update(des, action_min_vector, new_q))
            desired_vectors.assign(tf.reshape(des, [100, 140]))

            session.run(train_step, feed_dict={input_layer: state_min_vectors, desired: desired_vectors.eval(session=session)})

            move_min = 0

        if move_max == MINI_BATCH_SIZE:
            mq = session.run(tf.reduce_max(output_layer, reduction_indices=1), feed_dict={input_layer: next_state_max_vectors})
            new_q = tf.add(FUTURE_REWARD_DISCOUNT * mq, reward_max_vector)
            desired_vectors.assign(session.run(output_layer, feed_dict={input_layer: state_max_vectors}))
            des.assign(tf.reshape(desired_vectors, [140 * 100]))
            des.assign(tf.scatter_update(des, action_max_vector, new_q))
            desired_vectors.assign(tf.reshape(des, [100, 140]))

            session.run(train_step, feed_dict={input_layer: state_max_vectors, desired: desired_vectors.eval(session=session)})

            move_max = 0

    save_path = saver.save(session, "model.ckpt")
    print("Model saved in file: %s" % save_path)

    session.close()


def tf_play(colors_on, special):
    game = ConsoleGame(console_colors=colors_on, special_chars=special)

    # INIT MLP WEIGHTS
    W_hid = tf.Variable(tf.truncated_normal([INPUT_LAYER_SIZE, HIDDEN_LAYER_SIZE], stddev=0.01))
    b_hid = tf.Variable(tf.constant(0.01, shape=[HIDDEN_LAYER_SIZE]))

    W_out = tf.Variable(tf.truncated_normal([HIDDEN_LAYER_SIZE, OUTPUT_LAYER_SIZE], stddev=0.01))
    b_out = tf.Variable(tf.constant(0.01, shape=[OUTPUT_LAYER_SIZE]))

    # INIT LAYERS
    input_layer = tf.placeholder(tf.float32, [None, INPUT_LAYER_SIZE])
    hidden_layer = tf.sigmoid(tf.matmul(input_layer, W_hid) + b_hid)
    output_layer = tf.matmul(hidden_layer, W_out) + b_out

    players = {
        YELLOW: {'name': 'heuristic', 'player': None},
        GREEN: {'name': 'heuristic', 'player': None},
    }

    kwargs = {
        'messages': game.messages,
        'game_controls': game.GAME_CONTROLS,
        'fail_callback': game.wrong_human_move,
    }
    hp = HumanPlayer(game, **kwargs)

    # INIT TENSORFLOW
    session = tf.Session()
    saver = tf.train.Saver()
    saver.restore(session, 'model.ckpt')

    context = QuoridorContext(game)
    context.reset(players=players)

    def _choose_from_activations(acts, color):
        print acts
        q_values_to_action = sorted(
            enumerate(acts[0]),
            key=operator.itemgetter(1),
            reverse=True,
        )
        for action, value in q_values_to_action:
            print action
            yield action

    while not context.is_terminal:
        game.display_on_console(context)
        # print context.state
        if context.state[0] == GREEN:
            action = hp(context)
            # print action
            # context.update(action)
            continue

        # print 'ide qlnn'
        state = input_vector_from_game_state(context)
        state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])
        qlnn_actions = session.run(output_layer, feed_dict={input_layer: state})
        for action in _choose_from_activations(qlnn_actions, context.state[0]):
            try:
                context.update(action)
                break
            except InvalidMove:
                pass

    session.close()


def get_tf_nn_action(context):
    pass


OPPONENTS = {
    'random': RandomPlayerWithPath,
    'path': PathPlayer,
    'heuristic': HeuristicPlayer,
}


def players_creator_factory(opponent, opponent_type, ann):
    opp = {'name': opponent_type, 'player': opponent}
    ann = {'name': 'ann', 'player': ann}
    choices = ({YELLOW: opp, GREEN: ann}, {YELLOW: ann, GREEN: opp})
    def random_players_order():
        """Random starting colors for players"""
        return choices[random.random() < 0.5]
    return random_players_order


HIDDEN_LAYER_SIZE_DEFAULT = 100
OUTPUT_LAYER_SIZE_DEFAULT = 140
LEARNING_RATE_DEFAULT = 0.01
MINI_BATCH_SIZE_DEFAULT = 100
REWARD_FACTOR_DEFAULT = 100
STANDARD_DEVIATION_DEFAULT = 0.01
REPEAT_POSITION_NEURONS_DEFAULT = 1


class TFPlayer(Player):
    def __init__(self, game, tf_session,
                 hidden=HIDDEN_LAYER_SIZE_DEFAULT,
                 output=OUTPUT_LAYER_SIZE_DEFAULT,
                 stddev=STANDARD_DEVIATION_DEFAULT,
                 repeat=REPEAT_POSITION_NEURONS_DEFAULT):
        super(TFPlayer, self).__init__(game)

        self.repeat = repeat
        self.tf_session = tf_session

        self.input = calculate_input_size(repeat)
        self.hidden = hidden
        self.output = output

        # INIT MLP WEIGHTS
        self.W_hid = tf.Variable(
            tf.truncated_normal([self.input, hidden], stddev=stddev)
        )
        self.b_hid = tf.Variable(tf.constant(stddev, shape=[self.hidden]))

        self.W_out = tf.Variable(
            tf.truncated_normal([hidden, output], stddev=stddev)
        )
        self.b_out = tf.Variable(tf.constant(stddev, shape=[output]))

        # INIT LAYERS
        self.input_layer = tf.placeholder(tf.float32, [None, self.input])
        self.hidden_layer = tf.sigmoid(
            tf.matmul(self.input_layer, self.W_hid) + self.b_hid
        )
        self.output_layer = (
            tf.matmul(self.hidden_layer, self.W_out) + self.b_out
        )

    def _generate_action(self, output_vector, color):
        # print output_vector
        values_to_action = sorted(
            enumerate(output_vector[0]),
            key=operator.itemgetter(1),
            reverse=True,
        )
        for action, value in values_to_action:
            # print action, value
            yield action

    def play(self, context):
        state = input_vector_from_game_state(context, repeat=self.repeat)
        state = np.array(list(state)).reshape([1, self.input])
        qlnn_actions = session.run(
            self.output_layer, feed_dict={self.input_layer: state}
        )

        for action in self._generate_action(qlnn_actions, context.state[0]):
            try:
                context.update(action)
                return
            except InvalidMove:
                pass

        # this will not get here, but in case...
        raise Exception('Could not play any action.')


def measure(colors_on, special, opponent_type):
    game = ConsoleGame(console_colors=colors_on, special_chars=special)
    opponent = OPPONENTS[opponent_type](game)

    # INIT TENSORFLOW
    # session = tf.Session()
    # saver = tf.train.Saver()
    # saver.restore(session, 'model.ckpt')
    # ann = TFPlayer(game, session)
    # print 'tfplayer input layer size:', ann.input
    # print 'x'*80

    ann = RandomPlayerWithPath(game)

    context = QuoridorContext(game)
    while True:
        get_players = players_creator_factory(opponent, opponent_type, ann)
        context.reset(players=get_players())
        while not context.is_terminal:
            context.current['player'](context)
        game.display_on_console(context)
        break


def run():
    parser = OptionParser()
    parser.add_option(
        '-c', '--no-colors', dest='colors_on', default=True,
        action='store_false', help='Disable color output in console mode.'
    )
    parser.add_option(
        '-s', '--no-special-chars', dest='special', default=True,
        action='store_false', help='Display pawns with simpler characters.'
    )
    parser.add_option(
        '-t', '--train', dest='train', default=False,
        action='store_true', help='Start training.'
    )

    parser.add_option(
        '-m', '--measure', dest='opponent', type='choice',
        choices=OPPONENTS.keys(),
        help=(
            'Play \'measurement\' games agains specified opponent. Choices '
            'are: {choices}'
        ).format(choices=', '.join(OPPONENTS)),
    )
    options, args = parser.parse_args()

    colors_on = options.colors_on
    if os.getenv('ANSI_COLORS_DISABLED') is not None:
        colors_on = False

    if options.opponent is not None:
        measure(colors_on, options.special, options.opponent)
    elif options.train:
        train()
    else:
        tf_play(colors_on, options.special)
