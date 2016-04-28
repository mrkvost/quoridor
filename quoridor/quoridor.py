# -*- coding: utf-8 -*-

import os
import re
import sys
import copy
import numpy
import random
import datetime

from optparse import OptionParser

from commonsettings import DB_PATH
from db.utils import make_db_session
from ai.players import (
    HumanPlayer,
    PathPlayer,
    HeuristicPlayer,
    QlearningNetworkPlayer,
)
from core.game import (
    YELLOW,
    GREEN,
    PLAYER_COLOR_NAME,
    FOLLOWING_PLAYER,
    BOARD_SIZE_DEFAULT,
    STARTING_WALL_COUNT,

    InvalidMove,
    Quoridor2,
)
from core.context import QuoridorContext


numpy.set_printoptions(suppress=True)

BOARD_BORDER_THICKNESS = 1

FIELD_INNER_HEIGHT_DEFAULT = 3
FIELD_INNER_WIDTH_DEFAULT = 7
WALL_THICKNESS_DEFAULT = 1

PLAYER_GOAL_INFO = {
    YELLOW: u' (goes to the bottom \u21ca)',
    GREEN: u' (goes to the top \u21c8)',
}

COLOR_START_CONSOLE = {YELLOW: u'\x1b[1m\x1b[33m', GREEN: u'\x1b[1m\x1b[32m'}
COLOR_END_CONSOLE = u'\x1b[0m'
CONSOLE_CLEAR = {'nt': 'cls', 'posix': 'clear'}
CONSOLE_COLORS_DEFALUT = False

MENU_CHOICE = {
    0: {
        'mode': 'game',
        'player_names': {YELLOW: 'human', GREEN: 'human'},
        'text': 'New Game Human only',
    },
    1: {
        'mode': 'game',
        'player_names': {YELLOW: 'human', GREEN: 'heuristic'},
        'text': 'New Game vs Heuristic (Human First)',
    },
    2: {
        'mode': 'game',
        'player_names': {YELLOW: 'heuristic', GREEN: 'human'},
        'text': 'New Game vs Heuristic (Human Second)',
    },
    3: {
        'mode': 'game',
        'player_names': {YELLOW: 'heuristic', GREEN: 'heuristic'},
        'text': 'Watch Game Heuristic vs Heuristic',
    },
    4: {
        'mode': 'game',
        'player_names': {YELLOW: 'qlnn', GREEN: 'human'},
        'text': 'New Game vs QL Neural Network (Human Second)',
    },
    5: {
        'mode': 'game',
        'player_names': {YELLOW: 'qlnn', GREEN: 'heuristic'},
        'text': 'Watch QL Neural Network vs Heuristic',
    },

    6: {
        'mode': 'train',
        'player_names': {YELLOW: 'qlnn', GREEN: 'heuristic'},
        'text': 'Train QLNN vs Heuristic',
    },

    7: {
        'mode': 'train',
        'player_names': {YELLOW: 'qlnn', GREEN: 'path'},
        'text': 'Train QLNN vs Path',
    },

    8: {
        'mode': 'random_state',
        'player_names': None,
        'text': 'Generate random state',
    },

    9: {
        'mode': 'quit',
        'player_names': None,
        'text': 'Quit (q, quit, exit)',
    },

    # TODO: temporal difference player
    #       simple qlearning player
    #       random player with path
    #       random player
    #       'save',
    #       'load',
    #       'quit',
}

PLAYERS = {
    'human': HumanPlayer,
    'path': PathPlayer,
    'heuristic': HeuristicPlayer,
    'qlnn': QlearningNetworkPlayer,
}

OVERALL_FMT = (
    u'\rgames:{games: 4}| sec.:{seconds: 5}s| sec./game:{pace:.2}s| '
    u'won/lost: {won: 3} /{lost: 4}|  '
)

TRAINING_STATES = (
    # YELLOW WIN:
    # simple down
    (0, 67, 13, 10, 10, frozenset()),
    (0, 70, 9, 5, 5, frozenset([1, 3, 14, 40, 59, 61, 66, 76, 94, 113])),

    # simple path
    (0, 31, 49, 0, 0, frozenset([3, 12, 22, 26, 36, 39, 49, 51, 53, 55, 56, 68, 71, 83, 85, 94, 97, 104, 107, 123])),
    (1, 35, 52, 0, 0, frozenset([1, 66, 68, 69, 11, 78, 25, 91, 30, 35, 100, 37, 104, 44, 47, 49, 115, 118, 55, 59])),

    # harder
    (0, 66, 47, 2, 2, frozenset([11, 21, 49, 51, 57, 59, 68, 78, 82, 91, 94, 98, 100, 124])),
    (0, 66, 47, 1, 1, frozenset([2, 7, 12, 14, 25, 36, 43, 58, 60, 67, 86, 93, 97, 103, 106, 113, 117, 123])),

    # need horizontal
    (0, 58, 13, 8, 10, frozenset([1, 5])),
    (0, 67, 14, 8, 9, frozenset([3, 7, 59])),
    (0, 58, 23, 8, 9, frozenset([3, 7, 59])),
    (0, 31, 49, 6, 6, frozenset([67, 76, 83, 92, 99, 108, 115, 124])),

    # need vertical
    (0, 58, 16, 7, 10, frozenset([2, 4, 6])),
    (0, 58, 16, 7, 9, frozenset([2, 4, 6, 60])),

    # down - very uncommon situation:
    (0, 58, 22, 10, 10, frozenset()),
    (0, 49, 31, 10, 10, frozenset()),

    # hard - very common real life situation
    (0, 40, 31, 10, 10, frozenset()),

    # GREEN WIN:
    # (0, 31, 41, 3, 6, frozenset([11, 27, 33, 35, 48, 53, 63, 68, 84, 98, 108, 119, 124, 126])),
    # (0, 30, 41, 0, 1, frozenset([0, 2, 11, 28, 30, 40, 50, 52, 54, 67, 71, 82, 84, 99, 103, 105, 108, 124, 127]))
)

REWARD = 1000


def desired_output(player, activations, last_action, is_terminal, new_values):
    # reward = (1 - player * 2) * REWARD
    reward = 1 - player
    output = copy.deepcopy(activations[-1])

    # update qvalue for current action
    best_value = max(new_values) if player else min(new_values)
    if is_terminal:
        best_value += reward
    output[last_action] = best_value

    return output


class ConsoleGame(Quoridor2):

    GAME_CONTROLS = set([
        'quit',     # 'q', 'exit', 'end'
        'menu',
        'undo',     # 'back'
        'unknown',
        # TODO:
        # ''next', 'save', 'help', hint_move, change_players
    ])

    PAWN_MOVES = {
        'u': 0,     # 'up': 0,
        'r': 1,     # 'right': 1,
        'd': 2,     # 'down': 2,
        'l': 3,     # 'left': 3,

        'uu': 4, 'rr': 5, 'dd': 6, 'll': 7,

        'ur': 8, 'ru': 8,
        'ul': 9, 'lu': 9,
        'dr': 10, 'rd': 10,
        'dl': 11, 'ld': 11,
    }

    HUMAN_MOVES = {
        0: 'u',
        1: 'r',
        2: 'd',
        3: 'l',

        4: 'uu',
        5: 'rr',
        6: 'dd',
        7: 'll',

        8: 'ur',
        9: 'ul',
        10: 'dr',
        11: 'dl',
    }

    GAME_MENU = [
        ' - menu',
        ' - quit',
        # ' save - save game',
        # ' load - load game',
        ' - undo',
        '',
        ' PLACE WALL',
        ' - [h]0-63',
        '   (horizontal)',
        '',
        ' - v0-63',
        '   (vertical)',
        '',
        ' MOVE PAWN',
        ' - u (up)',
        ' - l (left)',
        ' - d (down)',
        ' - r (right)',
        ' - uu (jump up)',
        ' - dl (jump dl)',
        ' ...',
    ]

    def __init__(self, board_size=BOARD_SIZE_DEFAULT,
                 wall_thickness=WALL_THICKNESS_DEFAULT,
                 field_inner_width=FIELD_INNER_WIDTH_DEFAULT,
                 field_inner_height=FIELD_INNER_HEIGHT_DEFAULT,
                 console_colors=CONSOLE_COLORS_DEFALUT,
                 *args, **kwargs):

        super(ConsoleGame, self).__init__(board_size=board_size)

        self.wall_thickness = wall_thickness

        self.field_inner_width = field_inner_width
        self.field_width = field_inner_width + wall_thickness

        self.field_inner_height = field_inner_height
        self.field_height = field_inner_height + wall_thickness

        self.wall_length_horizontal = 2 * field_inner_width + wall_thickness
        self.wall_length_vertical = 2 * field_inner_height + wall_thickness

        board_inner_width = (
            (board_size - 1) * wall_thickness + board_size * field_inner_width
        )
        board_inner_height = (
            (board_size - 1) * wall_thickness + board_size * field_inner_height
        )

        self.board_width = board_inner_width + 2 * BOARD_BORDER_THICKNESS
        self.board_height = board_inner_height + 2 * BOARD_BORDER_THICKNESS

        self.possible_game_actions = frozenset(range(
            ((self.board_size - 1) ** 2) * 2 + 12
        ))

        # self.console_colors = console_colors
        self.color_end = self.red = self.green = self.yellow = self.cyan = u''
        self.white_background = self.bold = u''
        if console_colors:
            self.bold = u'\x1b[1m'
            self.red = self.bold + u'\x1b[31m'
            self.green = self.bold + u'\x1b[32m'
            self.yellow = self.bold + u'\x1b[33m'
            self.cyan = self.bold + u'\x1b[36m'
            self.white_background = u'\x1b[47m\x1b[1m\x1b[30m'
            self.color_end = COLOR_END_CONSOLE
        self.pawn_colors = {YELLOW: self.yellow, GREEN: self.green}
        self.messages = self.make_output_messages()
        options = [''.join([
            ' ',
            self.bold,
            'OPTIONS',
            self.color_end
        ])]
        self.game_menu = options + self.GAME_MENU

        self.console_colors = console_colors
        self.output_base = self.make_output_base()

    def path_blockers(self, path, crossers, avoid=None):
        avoid = set() if avoid is None else avoid
        blockers = set()
        for i in range(len(path) - 1):
            move = self.delta_moves[path[i + 1] - path[i]]
            for wall in self.blocker_positions[path[i]][move]:
                if wall not in crossers and wall not in avoid:
                    blockers.add(wall)
        return blockers

    def make_output_base(self):
        """Creates positions mapped to characters for further concatenation
        and display on the console as a game board.

        Board should look similar to:
        |-------|
        | O |   |
        |-------|
        |   | x |
        |-------|

        For example:
        {
            (0, 0): '>', (0, 1): '<', (0, 2): ')', (0, 3): ')',
            (0, 4): u'\u00b0', (0, 5): '>',
        }
        after concatenation should result in:
        ><))°>

        """

        # corners:
        base = {
            (0, 0): u'\u2554',
            (0, self.board_width - 1): u'\u2557',
            (self.board_height - 1, 0): u'\u255a',
            (self.board_height - 1, self.board_width - 1): u'\u255d',
        }

        # top and bottom:
        row = self.board_height - 1
        for col in range(BOARD_BORDER_THICKNESS, self.board_width - 1):
            base[(0, col)] = u'\u2550'
            base[(row, col)] = u'\u2550'

        # left and right:
        col = self.board_width - 1
        for row in range(BOARD_BORDER_THICKNESS, self.board_height - 1):
            base[(row, 0)] = u'\u2551'
            base[(row, col)] = u'\u2551'

        fw2 = self.field_width // 2
        counter = 0
        for col in range(fw2, self.board_width, self.field_width):
            base[(0, col)] = ''.join([
                self.white_background,
                u'ABCDEFGHIJ'[counter],
                self.color_end
            ])
            counter += 1

        fh2 = (self.field_height // 2)
        counter = 0
        for row in range(fh2, self.board_height, self.field_height):
            base[(row, 0)] = ''.join([
                self.white_background,
                u'\x1b[47m\x1b[1m\x1b[30m',
                u'0123456789'[counter],
                self.color_end
            ])
            counter += 1

        for row in range(BOARD_BORDER_THICKNESS, self.board_height - 1):
            for col in range(BOARD_BORDER_THICKNESS, self.board_width - 1):
                col_mod = col % (self.field_width) == 0
                if row % (self.field_height) == 0:
                    if col % 2 == 0 and not col_mod:
                        base[(row, col)] = '-'
                    else:
                        base[(row, col)] = ' '
                else:
                    if row % 2 != 0 and col_mod:
                        base[(row, col)] = '|'
                    else:
                        base[(row, col)] = ' '
        return base

    def wall_numbers_to_base(self, state, base):
        row_start = self.field_height
        row_stop = row_start + self.wall_board_size * self.field_height
        col_start = self.field_width
        col_stop = col_start + self.wall_board_size * self.field_width
        number = 0
        for row in range(row_start, row_stop, self.field_height):
            for col in range(col_start, col_stop, self.field_width):
                num = str(number)
                for i, digit in enumerate(num, start=1):
                    base[(row, col - len(num) + i)] = digit
                number += 1

    def walls_to_base(self, state, base):
        for wall in state[5]:
            if wall < self.wall_board_positions:
                row, col = divmod(wall, self.wall_board_size)
                row = (row + 1) * self.field_height
                start = col * self.field_width + 1
                stop = start + self.wall_length_horizontal
                for col in range(start, stop):
                    base[(row, col)] = u'\u2550'
                continue

            row, col = divmod(
                wall - self.wall_board_positions,
                self.wall_board_size
            )
            col = (col + 1) * self.field_width
            start = row * self.field_height + 1
            stop = start + self.wall_length_vertical
            for row in range(start, stop):
                base[(row, col)] = u'\u2551'

    def pawns_to_base(self, state, base):
        for player in (YELLOW, GREEN):
            color_start = self.pawn_colors[player]

            row, col = divmod(state[1 + player], self.board_size)
            leftmost = col * self.field_width + BOARD_BORDER_THICKNESS
            rightmost = leftmost + self.field_inner_width - 2
            top = row * self.field_height + BOARD_BORDER_THICKNESS
            bottom = top + self.field_inner_height - 1

            # top and bottom sides:
            for column in range(leftmost, rightmost + 1):
                base[(top, column)] = u'\u203e'
                base[(bottom, column)] = u'_'

            # left and right sides:
            for row in range(top, bottom + 1):
                base[(row, leftmost)] = color_start + u'\u23b8'
                base[(row, rightmost)] = u'\u23b9' + self.color_end

            # corners:
            base.update({
                (top, leftmost): color_start + u'\u27cb',
                (top, rightmost): u'\u27cd' + self.color_end,
                (bottom, leftmost): color_start + u'\u27cd',
                (bottom, rightmost): u'\u27cb' + self.color_end,
            })

            # text:
            name = PLAYER_COLOR_NAME[player]
            row = int(round(0.25 + float(top + bottom) / 2))
            for offset in range(1, rightmost - leftmost):
                if offset <= len(name):
                    base[(row, leftmost + offset)] = name[offset - 1]

    def action_to_human(self, action):
        type_ =''
        number = action
        if action < self.wall_board_positions:
            type_ ='h'
        elif action < self.wall_moves:
            type_ ='v'
            number -= self.wall_board_positions
        else:
            number = self.HUMAN_MOVES[action - self.wall_moves]
        return '[{type_}{number}]'.format(type_=type_, number=number)

    def history_to_base(self, history, base, start_row):
        start_col = self.board_width + 1
        first_line = ''.join([
            ' ',
            self.bold,
            'HISTORY',
            self.color_end
        ])
        for col, letter in enumerate(first_line, start=start_col):
            base[(start_row, col)] = letter

        if not history:
            return
        max_ = self.board_height - start_row
        hist_start = 0 if len(history) <= max_ else len(history) - max_
        displayed = history[hist_start:]
        for row, action_number in enumerate(displayed, start=start_row + 1):
            action = ' ' + self.action_to_human(action_number)
            for col, letter in enumerate(action, start=start_col):
                base[(row, col)] = letter

    def menu_to_base(self, base):
        start_col = self.board_width + 1
        for row, item in enumerate(self.game_menu, start=0):
            for col, letter in enumerate(item, start=start_col):
                base[(row, col)] = letter

    def display_on_console(self, context):
        base = copy.deepcopy(self.output_base)
        self.wall_numbers_to_base(context.state, base)
        self.walls_to_base(context.state, base)
        self.pawns_to_base(context.state, base)
        history_start_row = 0
        if context.current['name'] == 'human':
            self.menu_to_base(base)
            history_start_row = len(self.game_menu) + 1
        self.history_to_base(context.history, base, history_start_row)

        print '\n'.join([
            ''.join([
                base[(row, col)]
                for col in range(self.board_width + 100)
                if (row, col) in base
            ])
            for row in range(self.board_height)
        ])

        print u''.join([
            '#{moves_made:03d} '.format(moves_made=len(context.history)),
            self.yellow,
            u'YELLOW({type_}) walls:{walls:2} dist:{dist:2} {moves}'.format(
                type_=context.yellow['name'][:2].upper(),
                walls=context.state[3],
                dist=len(context.yellow['path']) - 1,
                moves='moves' if context.state[0] == YELLOW else '     ',
            ),
            self.color_end,
            u' | ',
            self.green,
            u'GREEN({type_}) walls:{walls:2} dist:{dist:2} {moves}'.format(
                type_=context.green['name'][:2].upper(),
                walls=context.state[4],
                dist=len(context.green['path']) - 1,
                moves='moves' if context.state[0] == GREEN else '     ',
            ),
            self.color_end,
        ])
        if context.is_terminal:
            player = FOLLOWING_PLAYER[context.state[0]]
            print ''.join([
                self.red,
                'Game ended! ',
                self.cyan,
                PLAYER_COLOR_NAME[player],
                ' player (',
                context.current['name'][:2].upper(),
                ')',
                ' is the winner!',
                '\n',
                self.color_end,
            ]),

    def make_output_messages(self):
        return {
            'enter_choice': ''.join([
                self.yellow,
                'Enter choice: ',
                self.color_end
            ]),
            'menu_choose': ''.join([
                self.yellow,
                u'Please, choose one of the following:',
                self.color_end,
            ]),
            'unknown_choice': ''.join([
                self.red,
                u'Unknown choice. Please, try again.',
                self.color_end,
                '\n',
            ]),
        }

    def prompt(self, message):
        user_input = raw_input(message)
        return user_input.strip()

    def get_human_action(self):
        user_input = self.prompt(self.messages['enter_choice'])
        if not user_input:
            if user_input is None:
                return 'quit'
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
            if action in self.possible_game_actions:
                return action
            return 'unknown'

        data['type'] = data['type'].lower()
        if data['type'] in self.GAME_CONTROLS:
            return data['type']
        elif data['type'] in self.PAWN_MOVES:
            return self.PAWN_MOVES[data['type']] + self.wall_moves
        elif data['type'] not in ('h', 'v'):
            return 'unknown'
        elif data['number'] is None:
            return 'unknown'
        direction_offset = 0
        if data['type'] == 'v':
            direction_offset = self.wall_board_positions
        return int(data['number']) + direction_offset

    def handle_game(self, context, players):
        context.reset(players=players)
        while not context.is_terminal:
            self.display_on_console(context)
            # print context
            player = context.state[0]
            if context[player]['name'] == 'human':
                action = players[player]['player'](context)
                if action in ('quit', 'menu'):
                    # TODO: save, load
                    return action
                elif action == 'undo':
                    next_ = FOLLOWING_PLAYER[player]
                    repeat = 1
                    if context[next_]['name'] != 'human':
                        repeat = 2
                        if len(context.history) < 2:
                            print self.red + 'Cannot undo!' + self.color_end
                            continue
                    try:
                        for _ in range(repeat):
                            context.undo()
                    except InvalidMove as e:
                        print self.red + str(e) + self.color_end
                elif action == 'unknown':
                    print self.messages['unknown_choice'],
            elif context[player]['name'] == 'qlnn':
                action = players[player]['player'](context)
            else:
                # these players update context:
                players[player]['player'](context)

        self.display_on_console(context)
        return 'menu'

    def train_game(self, context, players, display):
        qlnn = players[YELLOW]['player']    # qlnn is only YELLOW!
        if display:
            print
        while not context.is_terminal:
            if len(context.history) > 300:
                print '\nGame too long:', history, '\n'
                break

            if display:
                self.display_on_console(context)

            player = context.state[0]
            if context[player]['name'] == 'qlnn':
                explore = qlnn.perceptron.exploration_probability
                if explore and explore > random.random():
                    invalid_actions = set(context.invalid_actions)
                    qlnn.explore = True
                    qlnn.random_choose_from = (
                        self.all_actions - invalid_actions
                    )
                players[player]['player'](context)
                activations = qlnn.activations
                new_activations = qlnn.activations_from_state(context.state)
                last_qlnn_action = context.last_action
                desired = desired_output(
                    player,
                    # invalid_actions,
                    activations,
                    last_qlnn_action,
                    context.is_terminal,
                    new_activations[-1],
                )
                qlnn.perceptron.propagate_backward(activations, desired)
                qlnn.explore = False
            else:
                players[player]['player'](context)

        if display:
            self.display_on_console(context)

        if YELLOW == context.state[0]:
            assert context.is_terminal
            new_activations = qlnn.activations_from_state(context.state)
            desired = copy.deepcopy(activations[-1])
            desired[last_qlnn_action] -= 1
            qlnn.perceptron.propagate_backward(activations, desired)
            return False
        return True

    def handle_training(self, context, players, show_save_cycle=100,
                        display_games=False):
        game_counter = qlnn_wins = 0
        qlnn = players[YELLOW]['player']
        db_session = make_db_session(DB_PATH)
        start_time = datetime.datetime.now()
        status_every = 50
        random_base = qlnn.perceptron.exploration_probability
        games_goal = 100000
        try:
            while True:
                show_and_save = not (game_counter + 1) % show_save_cycle
                display_game = show_and_save and display_games
                context.reset(
                    players=players,
                    state=random.choice(TRAINING_STATES)
                )
                win = int(self.train_game(context, players, display_game))
                qlnn_wins += win
                game_counter += 1
                qlnn.perceptron.exploration_probability = (
                    random_base * (1 - game_counter / games_goal)
                )
                delta_time = datetime.datetime.now() - start_time
                seconds = int(delta_time.total_seconds())
                if not game_counter % status_every:
                    message = OVERALL_FMT.format(
                        seconds=seconds,
                        games=game_counter,
                        pace=(float(seconds) / game_counter),
                        won=qlnn_wins,
                        lost=game_counter - qlnn_wins,
                    )
                    sys.stdout.write(message)
                    sys.stdout.flush()
                if show_and_save:
                    sys.stdout.write('saving weights into database... ')
                    sys.stdout.flush()
                    qlnn.update_in_db(db_session)
                    sys.stdout.write('saved\n')
        finally:
            db_session.close()
        return 'quit'

    def train(self, context, players):
        self.handle_training(context, players, show_save_cycle=1000)
        return 'quit'

    def wrong_human_move(self, context, action, error):
        print self.red + str(error) + self.color_end
        self.display_on_console(context)

    def run(self):
        context = QuoridorContext(self)
        game_mode = 'menu'
        try:
            while game_mode != 'quit':
                if game_mode == 'menu':
                    choice_or_quit = self.handle_menu()
                    if choice_or_quit == 'quit':
                        break
                    game_mode = choice_or_quit['mode']
                    player_names = choice_or_quit['player_names']
                    if not player_names:
                        continue
                    players = {}
                    for color, name in player_names.items():
                        kwargs = {}
                        if name == 'human':
                            kwargs = {
                                'messages': self.messages,
                                'game_controls': self.GAME_CONTROLS,
                                'fail_callback': self.wrong_human_move,
                            }
                        players[color] = {
                            'name': name,
                            'player': PLAYERS[name](self, **kwargs),
                        }
                elif game_mode == 'game':
                    game_mode = self.handle_game(context, players)
                elif game_mode == 'train':
                    game_mode = self.train(context, players)
                else:
                    raise NotImplementedError()
        except (EOFError, KeyboardInterrupt, SystemExit):
            pass
        print

    def get_menu_input(self):
        user_input = self.prompt(self.messages['enter_choice'])
        if not user_input:
            if user_input is None:
                return 'quit'
            return 'unknown'

        if user_input in ('q', 'quit', 'exit'):
            return 'quit'

        match = re.match(r'(?P<number>\d+)', user_input)
        if match is None:
            return 'unknown'

        number = int(match.group('number'))
        if number not in MENU_CHOICE:
            return 'unknown'

        return MENU_CHOICE[number]

    def handle_menu(self):
        while True:
            self.print_menu()
            choice = self.get_menu_input()
            if choice == 'unknown':
                print self.messages['unknown_choice']
                continue
            elif choice == 'quit':
                return choice
            elif choice['mode'] == 'random_state':
                self.generate_random_state()
                continue
            return choice

    def print_menu(self):
        print self.messages['menu_choose']
        for i in range(len(MENU_CHOICE)):
            print '{number:2} - {choice}'.format(
                number=i,
                choice=MENU_CHOICE[i]['text'],
            )
        print

    def generate_random_state(self):
        new_state = [0, 0, 0, 0, 0, set()]
        board_positions = frozenset(range(self.board_positions))
        new_state[0] = random.choice((YELLOW, GREEN))
        for color in (YELLOW, GREEN):
            new_state[1 + color] = random.choice(
                tuple(board_positions - self.goal_positions[color])
            )
        all_wall_positions = tuple(range(self.wall_moves))

        place_walls = random.randint(0, 2 * STARTING_WALL_COUNT)
        # place_walls = 20
        walls_used = random.randint(
            max(0, place_walls - STARTING_WALL_COUNT),
            min(STARTING_WALL_COUNT, place_walls)
        )
        new_state[3] = STARTING_WALL_COUNT - walls_used
        new_state[4] = STARTING_WALL_COUNT - place_walls + walls_used
        while place_walls:
            action = random.choice(all_wall_positions)
            if self.is_wall_crossing(new_state[5], action):
                continue
            elif not self.players_can_reach_goal(new_state):
                continue
            new_state[5].add(action)
            place_walls -= 1
        new_state[5] = frozenset(new_state[5])

        context = QuoridorContext(self)
        context.reset(state=tuple(new_state))
        self.display_on_console(context)
        print context


# def qlearn(with_clear=True):
#     game = Quoridor2()
#     rpwp = RandomPlayerWithPath(game)
#     ql_player = QLPlayer(game)
#
#     games_to_play = 5
#     games_played = 0
#
#     max_moves = 1000
#     while games_to_play > games_played:
#         current_state = game.initial_state()
#         history = []
#         moves = 0
#
#         while max_moves > moves:
#             if moves % 2 == 0:
#                 action = ql_player.play(current_state)
#             else:
#                 action = rpwp.play(current_state)
#             action_type, position = action
#             previous_state = copy.deepcopy(current_state)
#             game.execute_action(current_state, action)
#             history.append(action)
#             if (games_to_play - 1) == games_played:
#                 display_on_console(
#                     current_state,
#                     True,
#                     history=history,
#                     with_clear=with_clear,
#                 )
#                 time.sleep(0.1)
#             ql_player.learn(previous_state, action, current_state)
#             if game.is_terminal(current_state):
#                 break
#             moves += 1
#
#         games_played += 1
#         print 'games_played:', games_played
#     ql_player.save_Q()


def main():
    parser = OptionParser()
    parser.add_option(
        '-c', '--colors', dest='colors_on', default=True, action='store_false',
        help='Disable color output in console mode. Enabled by default.'
    )
    options, args = parser.parse_args()

    colors_on = options.colors_on
    if os.getenv('ANSI_COLORS_DISABLED') is not None:
        colors_on = False

    game = ConsoleGame(console_colors=colors_on)
    game.run()
