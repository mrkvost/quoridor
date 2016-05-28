# -*- coding: utf-8 -*-

import os
import re
import copy
import random

import operator
import tensorflow as tf
import numpy as np

from optparse import OptionParser
from contextlib import closing

from commonsettings import DB_PATH
from db.models import Game
from db.utils import make_db_session, db_save_game
from ai.players import (
    HumanPlayer,
    PathPlayer,
    HeuristicPlayer,
    QlearningNetworkPlayer,
)
from ai.training import handle_training
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
from ai.utils import input_vector_from_game_state


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

PLAYERS_DEFAULT = {YELLOW: 'human', GREEN: 'human'}
MENU_CHOICE = {
    0: {
        'mode': 'game',
        'player_names': PLAYERS_DEFAULT,
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
        'mode': 'save',
        'player_names': None,
        'text': 'Save last game',
    },
    10: {
        'mode': 'load',
        'player_names': None,
        'text': 'Load game',
    },
    11: {
        'mode': 'quit',
        'player_names': None,
        'text': 'Quit (q, quit, exit)',
    },

    # TODO: temporal difference player
    #       simple qlearning player
    #       random player with path
    #       random player
    #       'quit',
}

PLAYERS = {
    'human': HumanPlayer,
    'path': PathPlayer,
    'heuristic': HeuristicPlayer,
    'qlnn': QlearningNetworkPlayer,
}


class ConsoleGame(Quoridor2):

    GAME_CONTROLS = set([
        'quit',
        'menu',
        'undo',
        'unknown',
        'save',
        'load',
        # TODO:
        # ''next', 'help', hint_move, change_players
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
        ' menu',
        ' quit',
        ' save',
        ' load',
        ' undo',
        '',
        ' PLACE WALL',
        ' [h]0-63',
        ' (horizontal)',
        '',
        ' v0-63',
        ' (vertical)',
        '',
        ' MOVE PAWN',
        ' u (up)',
        ' l (left)',
        ' d (down)',
        ' r (right)',
        '',
        ' JUMP PAWN',
        ' uu, ur, rr,',
        ' rd, dd, dl,',
        ' ll, lu',
    ]

    def __init__(self, board_size=BOARD_SIZE_DEFAULT,
                 wall_thickness=WALL_THICKNESS_DEFAULT,
                 field_inner_width=FIELD_INNER_WIDTH_DEFAULT,
                 field_inner_height=FIELD_INNER_HEIGHT_DEFAULT,
                 console_colors=CONSOLE_COLORS_DEFALUT,
                 special_chars=False,
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

        if special_chars:
            self.pawn_top = u'\u203e'
            self.pawn_left_side = u'\u23b8'
            self.pawn_right_side = u'\u23b9'
            self.pawn_corner_45 = u'\u27cb'
            self.pawn_corner_135 = u'\u27cd'
        else:
            self.pawn_top = u'-'
            self.pawn_left_side = u'|'
            self.pawn_right_side = u'|'
            self.pawn_corner_45 = u'/'
            self.pawn_corner_135 = u'\\'

        self.console_colors = console_colors
        self.output_base = self.make_output_base()

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
                base[(top, column)] = self.pawn_top
                base[(bottom, column)] = u'_'

            # left and right sides:
            for row in range(top, bottom + 1):
                base[(row, leftmost)] = color_start + self.pawn_left_side
                base[(row, rightmost)] = self.pawn_right_side + self.color_end

            # corners:
            base.update({
                (top, leftmost): color_start + self.pawn_corner_45,
                (top, rightmost): self.pawn_corner_135 + self.color_end,
                (bottom, leftmost): color_start + self.pawn_corner_135,
                (bottom, rightmost): self.pawn_corner_45 + self.color_end,
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
        max_ = self.board_height - start_row - 1
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
                context.following['name'][:2].upper(),
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
            'cannot_undo': ''.join([
                self.red, 'Cannot undo!', self.color_end,
            ]),
            'cannot_save': ''.join([
                self.red, 'No move played, cannot save!', self.color_end,
            ]),
            'save_success': ''.join([
                self.green, 'Successfully saved!', self.color_end,
            ]),
            'sure_load': ''.join([
                self.yellow,
                'Are you sure you want to leave this game and load another',
                ' one? (y/N): ',
                self.color_end,
            ]),
            'game_not_found': ''.join([
                self.red,
                'No such game found in database. Please, try again!',
                self.color_end,
            ]),
            'load_success': ''.join([
                self.green,
                'Game succesfully loaded!',
                self.color_end,
            ]),
            'cancelled': ''.join([
                self.yellow,
                'Cancelled!',
                self.color_end,
            ]),
        }

    def prompt(self, message):
        user_input = raw_input(message)
        return user_input.strip()

    def handle_game(self, context):
        while not context.is_terminal:
            self.display_on_console(context)
            # print context
            player = context.state[0]
            if context[player]['name'] == 'human':
                action = context[player]['player'](context)
                if action in ('quit', 'menu'):
                    return action
                elif action == 'undo':
                    next_ = FOLLOWING_PLAYER[player]
                    repeat = 1
                    if context[next_]['name'] != 'human':
                        repeat = 2
                        if len(context.history) < 2:
                            print self.messages['cannot_undo']
                            continue
                    try:
                        for _ in range(repeat):
                            context.undo()
                    except InvalidMove as e:
                        print self.red + str(e) + self.color_end
                elif action == 'unknown':
                    print self.messages['unknown_choice'],
                elif action == 'save':
                    self.save_menu(context)
                elif action == 'load':
                    while True:
                        user_input = self.prompt(self.messages['sure_load'])
                        user_input = user_input.lower()
                        if user_input in ('y', 'yes', 'ok'):
                            # TODO: ...
                            game_mode = self.load_menu(context)
                            if game_mode == 'game':
                                break
                            elif game_mode == 'quit':
                                return 'quit'
                            elif game_mode == 'menu':
                                break
                        elif user_input in ('', 'n', 'no'):
                            print self.messages['cancelled']
                            break
                        print self.messages['unknown_choice'],
            elif context[player]['name'] == 'qlnn':
                action = context[player]['player'](context)
            else:
                context[player]['player'](context)

        self.display_on_console(context)
        return 'menu'

    def train(self, context):
        handle_training(context, save_cycle=1000)
        return 'quit'

    def tf_play(self):
        # MLP parameters
        INPUT_LAYER_SIZE = 151
        HIDDEN_LAYER_SIZE = 100
        OUTPUT_LAYER_SIZE = 140
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
            'messages': self.messages,
            'game_controls': self.GAME_CONTROLS,
            'fail_callback': self.wrong_human_move,
        }
        hp = HumanPlayer(self, **kwargs)

        # INIT TENSORFLOW
        session = tf.Session()
        saver = tf.train.Saver()
        saver.restore(session, 'model.ckpt')

        context = QuoridorContext(self)
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
            self.display_on_console(context)
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

    def wrong_human_move(self, context, action, error):
        print self.red + str(error) + self.color_end
        self.display_on_console(context)

    def get_players(self, player_names):
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
        return players

    def run(self):
        try:
            self.handle_menu()
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
        context = QuoridorContext(self)
        game_mode = 'menu'
        while game_mode != 'quit':
            self.print_menu()
            choice = self.get_menu_input()
            if isinstance(choice, basestring):
                if choice == 'unknown':
                    print self.messages['unknown_choice']
                    continue
                elif choice == 'quit':
                    return

            game_mode = choice['mode']

            if game_mode == 'quit':
                return
            elif game_mode == 'random_state':
                self.generate_random_state()
                continue
            elif game_mode == 'save':
                if not context.history:
                    print self.messages['cannot_save']
                    continue
                game_mode = self.save_menu(context)
                continue

            if game_mode == 'load':
                game_mode = self.load_menu(context)
                if game_mode == 'game':
                    game_mode = self.handle_game(context)
                continue

            players = self.get_players(choice['player_names'])
            context.reset(players=players)
            if game_mode == 'game':
                game_mode = self.handle_game(context)
                continue
            elif game_mode == 'train':
                game_mode = self.train(context)
                continue

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
        exclude = self.goal_positions[YELLOW]
        new_state[1] = random.choice(tuple(board_positions - exclude))
        # new_state[1] = random.choice(range(72, 81))   # goal line
        exclude = self.goal_positions[GREEN] | set([new_state[1]])
        new_state[2] = random.choice(tuple(board_positions - exclude))
        # new_state[2] = new_state[1] + 9

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
            new_state[5].add(action)
            if not self.players_can_reach_goal(new_state):
                new_state[5].remove(action)
                continue
            place_walls -= 1
        new_state[5] = frozenset(new_state[5])

        context = QuoridorContext(self)
        context.reset(state=tuple(new_state))
        self.display_on_console(context)
        print context

    def save_menu(self, context):
        if not context.history:
            print self.messages['cannot_save']
            return 'menu'

        input_re = re.compile(r'[0123]|db|file|b|back|menu|q|quit|exit', re.I)
        success = False
        while True:
            print self.messages['menu_choose']
            print '0 - save in database (db)'
            print '1 - save in the file (file)'
            print '2 - back (b, back, menu)'
            print '3 - Quit (q, quit, exit)'

            user_input = self.prompt(self.messages['enter_choice']).lower()
            match = input_re.match(user_input)
            if match is None:
                print self.messages['unknown_choice']
                continue

            if user_input in ('0', 'db'):
                success = self.save_db_menu(context)
            elif user_input in ('1', 'file'):
                success = self.save_file_menu(context)
            elif user_input in ('2', 'b', 'back', 'menu'):
                return 'menu'
            elif user_input in ('3', 'q', 'quit', 'exit'):
                return 'quit'

            if success:
                print self.messages['save_success']
                return 'menu'
            continue

    def save_db_menu(self, context):
        message = ''.join([
            self.yellow,
            'Please, enter game name or type \'back\' to go back: ',
            self.color_end
        ])
        user_input = self.prompt(message)
        if user_input.lower() == 'back':
            return False

        with closing(make_db_session(DB_PATH)) as db_session:
            db_save_game(
                db_session,
                start_state=context['start_state'],
                yellow=context.yellow['name'],
                green=context.green['name'],
                winner=context.winner,
                actions=context.history,
                description=user_input,
            )
            db_session.commit()
            return True

    def save_file_menu(self, context):
        message = ''.join([
            self.yellow,
            '(note: this rewrites existing files!)\n',
            'Please, enter file name or type \'back\' to go back: ',
            self.color_end
        ])

        while True:
            user_input = self.prompt(message)
            if not user_input:
                continue
            elif user_input.lower() == 'back':
                return False

            try:
                with open(user_input, 'w') as f:
                    f.write(
                        '\n'.join([
                            str(context['start_state']),
                            str(context.history),
                        ])
                    )
            except EnvironmentError as e:
                print self.red + str(e) + self.color_end
                continue
            return True

    def load_menu(self, context):
        input_re = re.compile(r'[0123]|db|file|b|back|menu|q|quit|exit', re.I)
        success = False
        while True:
            print self.messages['menu_choose']
            print '0 - load from database (db)'
            print '1 - load from the file (file)'
            print '2 - back (b, back, menu)'
            print '3 - Quit (q, quit, exit)'

            user_input = self.prompt(self.messages['enter_choice']).lower()
            match = input_re.match(user_input)
            if match is None:
                print self.messages['unknown_choice']
                continue

            if user_input in ('0', 'db'):
                success = self.load_db_menu(context)
            elif user_input in ('1', 'file'):
                success = self.load_file_menu(context)
            elif user_input in ('2', 'b', 'back', 'menu'):
                return 'menu'
            elif user_input in ('3', 'q', 'quit', 'exit'):
                return 'quit'

            if success:
                print self.messages['load_success']
                return 'game'

    def load_db_menu(self, context):
        message = ''.join([
            self.yellow,
            'Please, enter game name or type \'back\' to go back: ',
            self.color_end
        ])
        players = self.get_players(PLAYERS_DEFAULT)     # TODO
        with closing(make_db_session(DB_PATH)) as db_session:
            while True:
                user_input = self.prompt(message)
                if not user_input:
                    continue
                elif user_input.lower() == 'back':
                    return False

                query = db_session.query(Game)
                game = query.filter_by(description=user_input).first()
                if not game:
                    print self.messages['game_not_found']
                    continue
                placed_walls = []
                if game.start_state.placed_walls:
                    placed_walls = game.start_state.placed_walls.split(',')
                state = (
                    game.start_state.on_move,
                    game.start_state.yellow_position,
                    game.start_state.green_position,
                    game.start_state.yellow_walls,
                    game.start_state.green_walls,
                    frozenset([int(wall) for wall in placed_walls])
                )
                context.reset(state=state, players=players)
                for move in game.moves:
                    context.update(move.action, checks_on=False)
                return True

    def load_file_menu(self, context):
        LIST_PATTERN = (
            r'\[\s*(?:\d+(?:\s*,\s*\d+)*\s*,?)?\s*\]'
        )
        FILE_STATE_PATTERN = (
            r'\('
            r'(?P<on_move>[01])'
            r'\s*,\s*'
            r'(?P<yellow_position>\d+)'
            r'\s*,\s*'
            r'(?P<green_position>\d+)'
            r'\s*,\s*'
            r'(?P<yellow_walls>\d+)'
            r'\s*,\s*'
            r'(?P<green_walls>\d+)'
            r'\s*,\s*'
            r'(?:frozen)?set\((?P<placed_walls>\[.*\])\)'
            r'\)'
        )
        FILE_STATE_RE = re.compile(FILE_STATE_PATTERN)
        LIST_RE = re.compile(LIST_PATTERN)
        message = self.yellow + 'Please, write file name or type \'back\' to go back: ' + self.color_end
        players = self.get_players(PLAYERS_DEFAULT)     # TODO
        incorrect_msg_fmt = self.red + 'Incorrect file! {exp}' + self.color_end

        while True:
            user_input = self.prompt(message)
            if not user_input:
                continue
            elif user_input.lower() == 'back':
                return False
            try:
                with open(user_input, 'r') as f:
                    state_line = f.readline()
                    history_line = f.readline().strip()
            except Exception as e:
                print self.red + str(e) + self.color_end
                continue

            state_match = FILE_STATE_RE.match(state_line)
            if not state_match:
                print incorrect_msg_fmt.format(exp='State not correct.')
                continue
            placed_walls = state_match.group('placed_walls')
            placed_walls_match = LIST_RE.match(placed_walls)
            if not placed_walls_match:
                print incorrect_msg_fmt.format(exp='Placed walls not correct.')
                continue
            history_match = LIST_RE.match(history_line)
            if not history_match:
                print incorrect_msg_fmt.format(exp='History not correct.')
                continue

            state = (
                int(state_match.group('on_move')),
                int(state_match.group('yellow_position')),
                int(state_match.group('green_position')),
                int(state_match.group('yellow_walls')),
                int(state_match.group('green_walls')),
                frozenset([
                    int(wall) for wall in placed_walls[1:-1].split(',') if wall
                ])
            )
            history = [
                int(action)
                for action in history_line[1:-1].split(',') if action
            ]
            context.reset(state=state, players=players)
            for i, action in enumerate(history):
                try:
                    context.update(action)
                except InvalidMove as e:
                    explanation = ''.join([
                        'Impossible move (',
                        str(i),
                        ': ',
                        str(action),
                        '). ',
                        str(e),
                    ])
                    print incorrect_msg_fmt.format(exp=explanation)
                    break
            else:
                return True


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
    parser.add_option(
        '-t', '--tf', dest='tf', default=False, action='store_true',
        help='Play against network trained in tensorflow.'
    )
    parser.add_option(
        '-s', '--no-special-chars', dest='special', default=True,
        action='store_false', help='Display pawns with simpler characters.'
    )
    options, args = parser.parse_args()

    colors_on = options.colors_on
    if os.getenv('ANSI_COLORS_DISABLED') is not None:
        colors_on = False

    game = ConsoleGame(console_colors=colors_on, special_chars=options.special)
    if options.tf:
        game.tf_play()
    game.run()
