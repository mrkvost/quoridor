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

HIDDEN_LAYER_SIZE_DEFAULT = 1000
OUTPUT_LAYER_SIZE_DEFAULT = 140
LEARNING_RATE_DEFAULT = 0.001
MINI_BATCH_SIZE_DEFAULT = 1000
STANDARD_DEVIATION_DEFAULT = 0.01
REPEAT_POSITION_NEURONS_DEFAULT = 1

CKPT_MODELS_PATH = 'tf_models/'

OPPONENTS = {
    'random': RandomPlayerWithPath,
    'path': PathPlayer,
    'heuristic': HeuristicPlayer,
}


def tf_play(colors_on, special):
    game = ConsoleGame(console_colors=colors_on, special_chars=special)

    # INIT TENSORFLOW
    session = tf.Session()
    ann = TFPlayer(game, session)
    saver = tf.train.Saver()
    saver.restore(session, 'model.ckpt')

    kwargs = {
        'messages': game.messages,
        'game_controls': game.GAME_CONTROLS,
        'fail_callback': game.wrong_human_move,
    }
    hp = HumanPlayer(game, **kwargs)
    context = QuoridorContext(game)
    get_players = players_creator_factory(hp, 'human', ann)
    context.reset(players=get_players())

    while not context.is_terminal:
        game.display_on_console(context)
        context.current['player'](context)
    game.display_on_console(context)

    session.close()


def players_creator_factory(opponent, opponent_type, ann):
    opp = {'name': opponent_type, 'player': opponent}
    ann = {'name': 'ann', 'player': ann}
    choices = ({YELLOW: opp, GREEN: ann}, {YELLOW: ann, GREEN: opp})
    def random_players_order():
        """Random starting colors for players"""
        return choices[random.random() < 0.5]
    return random_players_order


class TFPlayer(Player):
    def __init__(self, game, tf_session,
                 hidden=HIDDEN_LAYER_SIZE_DEFAULT,
                 output=OUTPUT_LAYER_SIZE_DEFAULT,
                 stddev=STANDARD_DEVIATION_DEFAULT,
                 repeat=REPEAT_POSITION_NEURONS_DEFAULT,
                 alpha=LEARNING_RATE_DEFAULT):
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

        # PLACEHOLDER FOR DESIRED OUTPUT
        self.desired = tf.placeholder(tf.float32, [None, output])

        # COST FUNCTION - MEAN SQUARE ERROR
        self.mse = tf.reduce_mean(tf.square(self.desired - self.output_layer))

        # ONE TRAINING STEP
        self.train_step = tf.train.AdamOptimizer(alpha).minimize(self.mse)

        self.saver = tf.train.Saver(max_to_keep=None)

    def load(self, filename=None):
        if filename is None:
            filename = self.last_model_filename()
        self.saver.restore(self.tf_session, filename)

    def save(self, filename=None):
        if filename is None:
            filename = os.path.join(CKPT_MODELS_PATH, 'model.ckpt')
        save_path = self.saver.save(self.tf_session, filename)

    def last_model_filename(self):
        return tf.train.latest_checkpoint(CKPT_MODELS_PATH)

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
    # ann = TFPlayer(game, session)
    # saver = tf.train.Saver()
    # saver.restore(session, 'model.ckpt')
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


def train(colors_on, special):
    game = ConsoleGame(console_colors=colors_on, special_chars=special)
    opponent = HeuristicPlayer(game)

    # INIT TENSORFLOW
    session = tf.Session()
    ann = TFPlayer(game, session)
    while True:
        filename = ann.last_model_filename()
        prompt_fmt = 'Continue training ({filename}) y/[N]? '
        user_input = raw_input(prompt_fmt.format(filename=filename)).lower()
        if user_input in ('y', 'yes'):
            ann.load()
        elif user_input in ('', 'n', 'no'):
            init = tf.initialize_all_variables()
            session.run(init)
        else:
            print 'Incorrect answer!'
            continue
        break

    # PLACEHOLDERS FOR INPUTS/DESIRED
    input_vectors = np.zeros([MINI_BATCH_SIZE_DEFAULT, ann.input])
    desired_vectors = np.zeros(([MINI_BATCH_SIZE_DEFAULT, ann.output]))

    context = QuoridorContext(game)
    get_players = players_creator_factory(opponent, 'heuristic', ann)
    players = get_players()

    # INIT GAME
    context.reset(players=players)
    state = input_vector_from_game_state(context)
    state = np.array(list(state)).reshape([1, ann.input])

    game_num = 0
    move = 0

    while True:
        if context.state[0] == GREEN: # training only green player
            # store current state
            input_vectors[move, :] = state

            # proceed to next state
            opponent.play(context)
            state = input_vector_from_game_state(context)
            state = np.array(list(state)).reshape([1, ann.input])

            # update desired vector
            action = context.last_action
            desired_vectors[move, action] = 100

            move += 1
        else:
            opponent.play(context)

        if context.is_terminal:
            game_num += 1
            context.reset(players=players)
            state = input_vector_from_game_state(context)
            state = np.array(list(state)).reshape([1, ann.input])

            if game_num % 5000 == 0:
                print('GAME ', game_num)
                filename = "training_model.ckpt.{num}".format(num=game_num)
                ann.save(os.path.join(CKPT_MODELS_PATH, filename))

        if move == MINI_BATCH_SIZE_DEFAULT:
            feed_dict = {
                ann.input_layer: input_vectors,
                ann.desired: desired_vectors,
            }
            session.run(ann.train_step, feed_dict=feed_dict)
            move = 0


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
        train(colors_on, options.special)
    else:
        tf_play(colors_on, options.special)
