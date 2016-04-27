# -*- coding: utf-8 -*-

import os
import re
import sys
import copy
import numpy
import random
import datetime
import collections

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

Vector = collections.namedtuple('Vector', ['row', 'col'])

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
        'mode': 'quit',
        'player_names': None,
        'text': 'Quit',
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


def desired_output(player, invalid_actions, activations, last_action,
                   is_terminal, new_values):
    reward = (1 - player * 2) * REWARD
    output = copy.deepcopy(activations[-1])
    # for action in invalid_actions:
    #     output[action] -= reward

    # update qvalue for current action
    best_value = max(new_values) if player else min(new_values)
    if is_terminal:
        best_value += reward
    output[last_action] = best_value

    return output


class ConsoleGame(Quoridor2):

    GAME_CONTROLS = set([
        'quit',
        'menu',
        'undo',
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

        self.output_base = self.make_output_base()

        self.possible_game_actions = frozenset(range(
            ((self.board_size - 1) ** 2) * 2 + 12
        ))

        # self.console_colors = console_colors
        self.color_end = self.red = self.green = self.yellow = self.cyan = u''
        if console_colors:
            self.red = u'\x1b[1m\x1b[31m'
            self.green = u'\x1b[1m\x1b[32m'
            self.yellow = u'\x1b[1m\x1b[33m'
            self.cyan = u'\x1b[1m\x1b[36m'
            self.color_end = COLOR_END_CONSOLE
        self.pawn_colors = {YELLOW: self.yellow, GREEN: self.green}
        self.messages = self.make_output_messages()

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
            Vector(row=0, col=0): u'\u2554',
            Vector(row=0, col=self.board_width - 1): u'\u2557',
            Vector(row=self.board_height - 1, col=0): u'\u255a',
            Vector(
                row=self.board_height - 1,
                col=self.board_width - 1
            ): u'\u255d',
        }

        # top and bottom:
        for col in range(BOARD_BORDER_THICKNESS, self.board_width - 1):
            base[Vector(row=0, col=col)] = u'\u2550'
            base[Vector(row=self.board_height - 1, col=col)] = u'\u2550'

        # left and right:
        for row in range(BOARD_BORDER_THICKNESS, self.board_height - 1):
            base[Vector(row=row, col=0)] = u'\u2551'
            base[Vector(row=row, col=self.board_width - 1)] = u'\u2551'

        fw2 = (self.field_width // 2)
        for col in range(self.board_size):
            # position = Vector(row=0, col=(1 + col) * self.field_width)
            position = Vector(row=0, col=col * self.field_width + fw2)
            base[position] = ''.join([
                u'\x1b[47m\x1b[1m\x1b[30m',
                u'ABCDEFGHIJ'[col],
                COLOR_END_CONSOLE
            ])

        fh2 = (self.field_height // 2)
        for row in range(self.board_size):
            base[Vector(row=row * self.field_height + fh2, col=0)] = ''.join([
                u'\x1b[47m\x1b[1m\x1b[30m',
                u'0123456789'[row],
                COLOR_END_CONSOLE
            ])

        for row in range(BOARD_BORDER_THICKNESS, self.board_height - 1):
            for col in range(BOARD_BORDER_THICKNESS, self.board_width - 1):
                col_mod = (
                    col % (self.field_inner_width + self.wall_thickness) == 0
                )
                if row % (self.field_inner_height + self.wall_thickness) == 0:
                    if col % 2 == 0 and not col_mod:
                        base[Vector(row=row, col=col)] = '-'
                    else:
                        base[Vector(row=row, col=col)] = ' '
                else:
                    if row % 2 != 0 and col_mod:
                        base[Vector(row=row, col=col)] = '|'
                    else:
                        base[Vector(row=row, col=col)] = ' '
        return base

    def walls_to_base(self, state, base):
        row_offset = self.field_height
        col_offset = self.field_width
        for row in range(self.wall_board_size):
            for col in range(self.wall_board_size):
                num = str(row * self.wall_board_size + col)
                for i in range(len(num)):
                    position = Vector(
                        row=row_offset + row * self.field_height,
                        col=col_offset + col * self.field_width - i,
                    )
                    base[position] = num[-i - 1]

        for wall in state[5]:
            if wall < self.wall_board_positions:
                row, col = divmod(wall, self.wall_board_size)
                row_offset = (row + 1) * self.field_height
                col_offset = col * self.field_width + 1
                for col_delta in range(self.wall_length_horizontal):
                    position = Vector(
                        row=row_offset, col=col_offset + col_delta
                    )
                    base[position] = u'\u2550'
                continue

            row, col = divmod(
                wall - self.wall_board_positions,
                self.wall_board_size
            )
            row_offset = row * self.field_height + 1
            col_offset = (col + 1) * self.field_width
            for row_delta in range(self.wall_length_vertical):
                position = Vector(row=row_offset + row_delta, col=col_offset)
                base[position] = u'\u2551'

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
                base[Vector(row=top, col=column)] = u'\u203e'
                base[Vector(row=bottom, col=column)] = u'_'

            # left and right sides:
            for row in range(top, bottom + 1):
                base[Vector(row=row, col=leftmost)] = (
                    color_start + u'\u23b8'
                )
                base[Vector(row=row, col=rightmost)] = (
                    u'\u23b9' + self.color_end
                )

            # corners:
            base.update({
                Vector(row=top, col=leftmost): color_start + u'\u27cb',
                Vector(row=top, col=rightmost): u'\u27cd' + self.color_end,
                Vector(row=bottom, col=leftmost): color_start + u'\u27cd',
                Vector(row=bottom, col=rightmost): u'\u27cb' + self.color_end,
            })

            # text:
            name = PLAYER_COLOR_NAME[player]
            row = int(round(0.25 + float(top + bottom) / 2))
            for offset in range(1, rightmost - leftmost):
                position = Vector(row=row, col=leftmost + offset)
                if offset <= len(name):
                    base[position] = name[offset - 1]

    def display_on_console(self, context):
        # TODO: menu possibilities
        # TODO: history list
        # TODO: winner info
        base = copy.deepcopy(self.output_base)
        self.walls_to_base(context.state, base)
        self.pawns_to_base(context.state, base)

        print '\n'.join([
            ''.join([
                base[Vector(row=row, col=col)]
                for col in range(self.board_width + 100)
                if Vector(row=row, col=col) in base
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
            'game_ended': ''.join([
                self.cyan, ' - GAME ENDED -', self.color_end
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
        print self.messages['game_ended']
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
                invalid_actions = context.invalid_actions
                activations = qlnn.activations_from_state(context.state)
                players[player]['player'](context)
                new_activations = qlnn.activations
                last_qlnn_action = context.last_action
                desired = desired_output(
                    player,
                    invalid_actions,
                    activations,
                    last_qlnn_action,
                    context.is_terminal,
                    new_activations[-1],
                )
                qlnn.perceptron.propagate_backward(activations, desired)
            else:
                players[player]['player'](context)

        if display:
            self.display_on_console(context)

        if YELLOW == context.state[0]:
            assert context.is_terminal
            new_activations = qlnn.activations_from_state(context.state)
            desired = copy.deepcopy(activations[-1])
            desired[last_qlnn_action] -= REWARD
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
        try:
            while True:
                show_and_save = not (game_counter + 1) % show_save_cycle
                display_game = show_and_save and display_games
                context.reset(
                    players=players,
                    state=random.choice(TRAINING_STATES)
                )
                # context.reset(players=players)
                win = int(self.train_game(context, players, display_game))
                qlnn_wins += win
                game_counter += 1
                qlnn.perceptron.exploration_probability = (
                    0.1 * (600000 - game_counter) / 600000
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
                    choice = self.handle_menu()
                    game_mode = choice['mode']
                    player_names = choice['player_names']
                    if player_names:
                        players = {}
                        for color, name in player_names.items():
                            kwargs = {}
                            if name == 'human':
                                kwargs = {
                                    'messages': self.messages,
                                    # 'game_controls': self.game_controls,
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
            return choice

    def print_menu(self):
        print self.messages['menu_choose']
        for i in range(len(MENU_CHOICE)):
            print '{number:2} - {choice}'.format(
                number=i,
                choice=MENU_CHOICE[i]['text'],
            )
        print


# def random_walls(game, state):
#     for i in range(random.randint(10, 30)):
#         position = Vector(
#             row=random.randint(WALL_POS_MIN, WALL_POS_MAX),
#             col=random.randint(WALL_POS_MIN, WALL_POS_MAX),
#         )
#         direction = random.choice(DIRECTIONS)
#         try:
#             game.execute_action(state, (direction, position))
#         except InvalidMove:
#             pass
#
#
# def random_pawn_positions(game, state):
#     state['pawns'] = {}
#     for color, goal_row in GOAL_ROW.items():
#         position = Vector(
#             row=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
#             col=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
#         )
#         while position in state['pawns'] or position.row == goal_row:
#             position = Vector(
#                 row=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
#                 col=random.randint(PAWN_POS_MIN, PAWN_POS_MAX),
#             )
#
#         state['pawns'][color] = position
#
#
# def status_line_to_base(row, line, base):
#     for offset, char in enumerate(u' ' + line):
#         base[Vector(row=row, col=BOARD_WIDTH + offset)] = char
#
#
#
# def history_to_base(base, history):
#     status_line_to_base(12, 'HISTORY:', base)
#     for n, action in enumerate(history[-10:]):
#         row = 13 + n
#         action_type, position = action
#         move = ACTION_TYPE[action_type](row=position.row, col=position.col)
#         status_line_to_base(row, ' ' + repr(move), base)
#
#
# COLUMN_LETTERS = u'abcdefghi'
# WALL_INPUT_PATTERN = (
#     ur'(?:wall|w|)\s*'
#     ur'(?P<direction>h|v)\s*'
#     ur'(?P<row>\d+)\s*'
#     ur'(?P<col>[{column_letters}])'
# ).format(column_letters=COLUMN_LETTERS)
# WALL_INPUT_RE = re.compile(WALL_INPUT_PATTERN, re.I)
# INPUT_DIRECTIONS = {'h': HORIZONTAL, 'v': VERTICAL}
#
# MOVE_INPUT_PATTERN = (
#     ur'(?:pawn|p|)\s*'
#     ur'(?P<row>\d+)\s*'
#     ur'(?P<col>[{column_letters}])'
# ).format(column_letters=COLUMN_LETTERS)
# MOVE_INPUT_RE = re.compile(MOVE_INPUT_PATTERN, re.I)
#
# QUIT_INPUT_PATTERN = u'quit|q|exit|end'
# QUIT_INPUT_RE = re.compile(QUIT_INPUT_PATTERN, re.I)
#
# UNDO_INPUT_PATTERN = u'u|undo|back'
# UNDO_INPUT_RE = re.compile(UNDO_INPUT_PATTERN, re.I)
#
# ACTION_UNKNOWN = 'unknown'
# ACTION_END = 'end'
# ACTION_MOVE = 'move'
# ACTION_UNDO = 'undo'
#
#
#
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
#
#
# def random_players(moves=None, with_clear=True):
#     game = Quoridor2()
#     state = game.initial_state()
#     # rp = RandomPlayer(game)
#     rpwp = RandomPlayerWithPath(game)
#     if moves is None:
#         moves = 1000
#     history = []
#     while moves > 0:
#         action = rpwp.play(state)
#         action_type, position = action
#         game.execute_action(state, action)
#         history.append(action)
#         display_on_console(state, True, history=history, with_clear=with_clear)
#         # print ACTION_TYPE[action_type](row=position.row, col=position.col)
#         if game.is_terminal(state):
#             break
#         time.sleep(0.1)
#         moves -= 1
#
#
# def console_run(options):
#
#     try:
#         if options.random:
#             random_players(with_clear=options.with_clear)
#             return
#         elif options.qlearn:
#             qlearn(with_clear=options.with_clear)
#             return
#     except (EOFError, KeyboardInterrupt, SystemExit):
#         pass
#     finally:
#         # TODO: look:
#         if traceback.format_exc() != 'None\n':
#             traceback.print_exc()


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
