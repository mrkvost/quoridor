import sys
import copy
import random
import datetime

from contextlib import closing

from quoridor.commonsettings import DB_PATH
from quoridor.db.utils import make_db_session, db_save_game
from quoridor.core.game import YELLOW, GREEN, GameException


TRAINING_STATES = {
    # only winning for YELLOW

    # 0: (    # terminal states
    #     (0, 80, 77, 9, 4, frozenset([87, 30, 103, 41, 106, 107, 62])),
    #     (0, 78, 24, 1, 3, frozenset([64, 11, 15, 16, 85, 25, 27, 92, 94, 31, 96, 98, 36, 41, 107, 111])),
    # ),

    0: (
        # easiest, one move to win
        (0, 67, 13, 10, 10, frozenset()),
        (0, 70, 9, 5, 5, frozenset([1, 3, 14, 40, 59, 61, 66, 76, 94, 113])),
        (0, 59, 68, 0, 0, frozenset([64, 67, 4, 10, 13, 15, 80, 18, 85, 91, 92, 29, 33, 37, 105, 108, 45, 50, 117, 54])),
        (0, 70, 21, 0, 0, frozenset([64, 1, 7, 10, 76, 13, 80, 23, 25, 92, 29, 98, 103, 41, 47, 48, 116, 53, 60, 127])),
        (0, 68, 79, 4, 5, frozenset([115, 102, 40, 43, 78, 111, 16, 83, 84, 53, 89])),
        (0, 67, 29, 8, 1, frozenset([64, 32, 98, 102, 39, 113, 82, 21, 118, 57, 63])),
        (0, 69, 78, 8, 7, frozenset([88, 56, 60, 63, 68])),
        (0, 67, 60, 2, 5, frozenset([64, 66, 3, 70, 40, 10, 77, 47, 16, 82, 83, 26, 127])),
        (0, 65, 74, 7, 5, frozenset([56, 1, 111, 81, 51, 122, 94])),
        (0, 65, 74, 6, 4, frozenset([18, 20, 56, 1, 105, 51, 53, 55, 89, 122])),
        (0, 59, 68, 4, 2, frozenset([96, 93, 39, 72, 10, 109, 14, 47, 40, 83, 57, 79, 124, 125])),
        (0, 58, 67, 1, 3, frozenset([22, 6, 39, 104, 106, 48, 50, 19, 118, 120, 90, 95, 101, 58, 127])),

        # simple path to goal
        (0, 51, 35, 0, 0, frozenset([1, 66, 68, 69, 11, 78, 25, 91, 30, 35, 100, 37, 104, 44, 47, 49, 115, 118, 55, 59])),
        (0, 35, 52, 0, 0, frozenset([1, 66, 68, 69, 11, 78, 25, 91, 30, 35, 100, 37, 104, 44, 47, 49, 115, 118, 55, 59])),
        (0, 67, 77, 7, 5, frozenset([97, 69, 16, 49, 116, 57, 60, 37])),
        (0, 67, 56, 3, 4, frozenset([64, 51, 99, 69, 10, 83, 20, 54, 25, 122, 60, 42, 126])),
        (0, 69, 66, 1, 0, frozenset([2, 4, 8, 75, 76, 85, 28, 30, 95, 33, 99, 38, 45, 112, 49, 55, 121, 59, 61])),
    ),

    1: (
        # more difficult path to goal
        (0, 66, 47, 2, 2, frozenset([11, 21, 49, 51, 57, 59, 68, 78, 82, 91, 94, 98, 100, 124])),
        (0, 31, 49, 0, 0, frozenset([3, 12, 22, 26, 36, 39, 49, 51, 53, 55, 56, 68, 71, 83, 85, 94, 97, 104, 107, 123])),
        (0, 45, 67, 0, 0, frozenset([2, 4, 70, 8, 73, 76, 16, 82, 20, 85, 86, 88, 29, 32, 34, 99, 37, 46, 56, 62])),

        # still easy solution
        (0, 31, 49, 6, 6, frozenset([67, 76, 83, 92, 99, 108, 115, 124])),
        (0, 25, 33, 1, 0, frozenset([64, 65, 68, 9, 13, 78, 80, 20, 85, 24, 30, 101, 105, 108, 45, 112, 115, 121, 59])),
        (0, 59, 75, 3, 4, frozenset([65, 3, 5, 38, 9, 106, 12, 110, 81, 116, 121, 122, 29])),
        (0, 25, 60, 4, 9, frozenset([29, 32, 45, 86, 87, 102, 114])),
        (0, 52, 50, 1, 1, frozenset([65, 3, 7, 8, 14, 16, 18, 90, 91, 29, 96, 101, 48, 115, 54, 119, 122, 124])),
        (0, 57, 30, 1, 2, frozenset([1, 70, 8, 21, 24, 89, 91, 31, 33, 101, 40, 105, 43, 115, 53, 55, 60])),
        (0, 57, 66, 0, 2, frozenset([67, 9, 74, 79, 84, 26, 91, 94, 31, 33, 103, 104, 105, 43, 52, 54, 58, 63])),
        (0, 65, 74, 6, 6, frozenset([56, 59, 76, 92, 108, 121, 122, 124])),
    ),

    2: (
        # computational problem
        (0, 66, 47, 1, 1, frozenset([2, 7, 12, 14, 25, 36, 43, 58, 60, 67, 86, 93, 97, 103, 106, 113, 117, 123])),
        (0, 51, 70, 5, 9, frozenset([32, 116, 119, 59, 12, 31])),
        (0, 30, 46, 6, 3, frozenset([64, 99, 37, 102, 71, 12, 77, 55, 92, 126, 127])),

        # most complicated, open with many possibilities
        (0, 58, 13, 8, 10, frozenset([1, 5])),          # need horizontal
        (0, 67, 14, 8, 9, frozenset([3, 7, 59])),       # need horizontal
        (0, 58, 23, 8, 9, frozenset([3, 7, 59])),
        (0, 58, 16, 7, 10, frozenset([2, 4, 6])),       # need vertical
        (0, 58, 16, 7, 9, frozenset([2, 4, 6, 60])),    # need vertical
        (0, 58, 22, 10, 10, frozenset()),   # down - very uncommon situation
        (0, 49, 31, 10, 10, frozenset()),   # down - very uncommon situation
        (0, 40, 31, 10, 10, frozenset()),
        (0, 51, 22, 7, 10, frozenset([73, 37, 77])),
        (0, 44, 70, 9, 10, frozenset([111])),
    ),
}

# LOOKS NICE:
# (0, 41, 67, 4, 3, frozenset([4, 7, 72, 73, 12, 28, 48, 114, 119, 58, 60, 125, 63]))
# (0, 58, 36, 6, 5, frozenset([64, 10, 107, 108, 18, 30, 56, 26, 62]))

# GREEN WIN:
# (0, 31, 41, 3, 6, frozenset([11, 27, 33, 35, 48, 53, 63, 68, 84, 98, 108, 119, 124, 126])),
# (0, 30, 41, 0, 1, frozenset([0, 2, 11, 28, 30, 40, 50, 52, 54, 67, 71, 82, 84, 99, 103, 105, 108, 124, 127]))


class TrainingStateGenerator(object):
    def __init__(self, goal, probability=0.5):
        self.goal = goal
        self.categories = len(TRAINING_STATES)
        self.step = goal // self.categories
        self.last_counter = 0

        self.probability = probability
        self.prob_step = probability / goal
        self.category = -1
        self.update(0)

    def update(self, counter):
        self.probability -= (counter - self.last_counter) * self.prob_step
        category = counter // self.step
        if category != self.category:
            self.category = category
            self.states = []
            for i in range(category + 1):
                self.states += TRAINING_STATES[i]
        self.last_counter = counter

    def get_state(self, counter):
        if counter > self.goal or self.probability < random.random():
            return
        self.update(counter)
        return random.choice(self.states)


OVERALL_FMT = (
    u'\rgames:{games:>6}| sec.:{seconds:>6}s| sec./game:{pace:>4.2f}s| '
    u'won/lost: {won:>4} /{lost:5}|  '
)


def show_training_status(start_time, game_counter, qlnn_wins):
    delta_time = datetime.datetime.now() - start_time
    seconds = delta_time.total_seconds()
    message = OVERALL_FMT.format(
        seconds=int(seconds),
        games=game_counter,
        pace=(float(seconds) / game_counter),
        won=qlnn_wins,
        lost=game_counter - qlnn_wins,
    )
    sys.stdout.write(message)
    sys.stdout.flush()


def save(qlnn, results, context):
    sys.stdout.write('saving weights into database... ')
    sys.stdout.flush()
    with closing(make_db_session(DB_PATH)) as db_session:
        qlnn.update_in_db(db_session)   # save weights and NN attributes
        for result in results[:-1]:
            db_save_game(
                db_session,
                yellow='qlnn',
                green=context[GREEN]['name'],
                winner=int(not result),
                is_training=True,
            )
        db_save_game(
            db_session,
            start_state=context['start_state'],
            yellow='qlnn',
            green=context[GREEN]['name'],
            winner=int(not results[-1]),
            actions=context.history,
            is_training=True,
        )
        db_session.commit()
        sys.stdout.write('saved\n')


GAME_LENGTH_MAX = 500
LONG_GAME_MESSAGE_FMT = (
    '\nGame too long!\nStart state: {state!r}\nHistory: {hist!r}\n'
)


def error_on_long_game(context):
    if len(context.history) < GAME_LENGTH_MAX:
        return
    raise GameException(LONG_GAME_MESSAGE_FMT.format(
        state=context['start_state'], hist=context.history
    ))


def set_exploration_probability(qlnn, start, counter, goal, minimum=0.005):
    # TODO: maybe decrease random move probability only after wins
    probability = start * (1.0 - float(counter) / goal) + minimum
    qlnn.perceptron.exploration_probability = probability


def desired_output(activations, new_values, context, previous_action):
    output = copy.copy(activations[-1])

    if context.is_terminal:
        player = context.state[0]   # YELLOW or GREEN
        if player == YELLOW:        # qlnn plays only YELLOW
            new_value = 1 + max(new_values)
        else:
            new_value = 0
    else:
        new_value = max(new_values)
    output[previous_action] = new_value

    return output


def play_game(context):
    qlnn = context[YELLOW]['player']    # qlnn is only YELLOW!
    while not context.is_terminal:
        error_on_long_game(context)

        player = context.state[0]

        if context[player]['name'] == 'qlnn':
            if len(context.history) > 1:
                desired = desired_output(
                    activations,
                    qlnn.activations_from_state(context.state)[-1],
                    context,
                    last_qlnn_action,
                )
                qlnn.perceptron.propagate_backward(activations, desired)
            explore = qlnn.perceptron.exploration_probability
            if explore and explore > random.random():
                invalid_actions = set(context.invalid_actions)
                qlnn.explore = True
                choices = context.game.all_actions - invalid_actions
                qlnn.random_choose_from = choices
            context[player]['player'](context)
            activations = qlnn.activations
            last_qlnn_action = context.last_action
            qlnn.explore = False
        else:
            context[player]['player'](context)

    # assert context.is_terminal
    desired = desired_output(
        activations,
        qlnn.activations_from_state(context.state)[-1],
        context,
        last_qlnn_action,
    )
    qlnn.perceptron.propagate_backward(activations, desired)
    win = context.state[0] != YELLOW
    return win


def handle_training(context, status_every=20, save_cycle=100):
    counter = wins = 0
    goal = 200000
    results = []

    players = context.players_dict
    qlnn = players[YELLOW]['player']
    random_start = qlnn.perceptron.exploration_probability

    state_generator = TrainingStateGenerator(goal)
    start_time = datetime.datetime.now()

    while True:
        state = state_generator.get_state(counter)
        # state = None  # default state
        context.reset(players=players, state=state)
        win = play_game(context)
        results.append(win)
        wins += win
        counter += 1

        set_exploration_probability(qlnn, random_start, counter, goal)

        if not counter % status_every:
            show_training_status(start_time, counter, wins)
        if not counter % save_cycle:
            save(qlnn, results, context)
            results[:] = []
