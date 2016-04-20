# -*- coding: utf-8 -*-

import os
import re
import sys
import copy
# import time
import random
import datetime
import collections
# import traceback

# from optparse import OptionParser

from core import (
    YELLOW,
    GREEN,
    PLAYER_COLOR_NAME,
    FOLLOWING_PLAYER,
    BOARD_SIZE_DEFAULT,

    InvalidMove,
    Quoridor2,

)

from players import PathPlayer, HeuristicPlayer, QlearningNetworkPlayer
from db import make_db_session
# from players import RandomPlayer, RandomPlayerWithPath, QLPlayer


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
        'mode': 'human_human',
        'text': 'New Game Human only',
    },
    1: {
        'mode': 'human_heuristic',
        'text': 'New Game vs Heuristic (Human First)',
    },
    2: {
        'mode': 'heuristic_human',
        'text': 'New Game vs Heuristic (Human Second)',
    },
    3: {
        'mode': 'heuristic_heuristic',
        'text': 'Watch Game Heuristic vs Heuristic',
    },
    4: {
        'mode': 'human_qlnn',
        'text': 'New Game vs QL Neural Network (Human First)',
    },
    5: {
        'mode': 'qlnn_human',
        'text': 'New Game vs QL Neural Network (Human Second)',
    },
    6: {
        'mode': 'qlnn_qlnn',
        'text': 'Watch QL Neural Network vs QL Neural Network',
    },
    7: {
        'mode': 'qlnn_heuristic',
        'text': 'Watch QL Neural Network vs Heuristic',
    },
    8: {
        'mode': 'heuristic_qlnn',
        'text': 'Watch Heuristic vs QL Neural Network',
    },

    9: {
        'mode': 'train_vs_heuristic',
        'text': 'Train QLNN vs Heuristic',
    },

    10: {
        'mode': 'train_vs_path',
        'text': 'Train QLNN vs Path',
    },

    11: {
        'mode': 'quit',
        'text': 'Quit',
    },

    # TODO: temporal difference network
    #       simple qlearning player
    #       random player with path
    #       random player

    # 8: 'save',
    # 9: 'load',
    # 10: 'quit',
}

# PLAYERS = {
#     # -1: {'type': 'rand', 'text': 'Random player'},
#     0: {'type': 'human', 'text': 'Human player'},
#     1: {'type': 'path', 'text': 'Path player'},
#     2: {'type': 'heuristic', 'text': 'Heuristic player'},
#     3: {'type': 'qlnn', 'text': 'QLearning Neural Network player'},
#     # 4: {'type': 'tdnn', 'text': 'Temporal Difference Neural Network player'},
# }


def clear_console():
    os.system(CONSOLE_CLEAR[os.name])


def print_context_and_state(context, state):
    print 'context history:', context['history']
    print 'context len(crossers):', len(context['crossers'])
    print 'context crossers:', context['crossers']
    print 'context yellow:', context[YELLOW]
    print 'context green:', context[GREEN]
    print 'state:', state


class ConsoleGame(Quoridor2):
    GAME_INPUT_PATTERN = (
        r'(?i)'
        r'(?P<type>menu|undo|quit|[hv]|[urdl]{1,2})?'
        r'(?P<number>[-+]?\d+)?'
        r'$'
    )
    GAME_INPUT_RE = re.compile(GAME_INPUT_PATTERN)

    GAME_CONTROLS = set([
        'quit',
        'menu',
        'unknown',
        # TODO:
        # 'undo', 'next', 'save', 'help', hint_move, change_players
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
                if wall not in crossers or wall not in avoid:
                    blockers.add(wall)
        return blockers

    def make_context(self, state, types=None):
        types = {YELLOW: 'human', GREEN: 'human'} if types is None else types
        context = {'history': [], 'crossers': self.crossing_actions(state)}

        for color in (YELLOW, GREEN):
            path = self.shortest_path(state, color)
            assert path is not None, (
                'no path to goal for ' + PLAYER_COLOR_NAME[color]
            )
            context[color] = {
                'path': path,
                'blockers': self.path_blockers(path, context['crossers']),
                'type': types[color],
                'goal_cut': set(),  # TODO: consider using ordered set
            }
        return context

    def update_context(self, state, context, action=None):
        """ update context according to last action made. must be specified
        exclusively in action or as last item context['history'][-1]
        """
        if self.is_terminal(state):
            return  # maybe raise error?

        if action is not None:
            context['history'].append(action)
        action = context['history'][-1]

        player = state[0]

        if 0 <= action < self.wall_moves:  # wall
            new_crossers = self.wall_crossers(action)
            context['crossers'] = context['crossers'].union(new_crossers)
            for color in (YELLOW, GREEN):
                if action in context[color]['blockers']:
                    context[color]['path'] = self.shortest_path(state, color)
                    context[color]['blockers'] = self.path_blockers(
                        context[color]['path'],
                        context['crossers'],
                        context[color]['goal_cut']
                    )
            return

        next_ = FOLLOWING_PLAYER[player]
        last_path = context[next_]['path']
        if last_path[-2] == state[1 + next_]:   # one step along the path
            context[next_]['path'].pop()
        elif len(last_path) > 2 and last_path[-3] == state[1 + next_]:  # two
            context[next_]['path'].pop()
            context[next_]['path'].pop()
        else:
            # TODO: can this be optimized?
            context[next_]['path'] = self.shortest_path(state, next_)

        context[next_]['goal_cut'].clear()
        context[next_]['blockers'] = self.path_blockers(
            context[next_]['path'],
            context['crossers'],
            context[next_]['goal_cut']
        )

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

            for offset in range(1, rightmost - leftmost):
                row = int(round(0.25 + float(top + bottom) / 2))
                position = Vector(row=row, col=leftmost + offset)
                if offset <= len(name):
                    base[position] = name[offset - 1]

    def display_on_console(self, state, context):
        base = copy.deepcopy(self.output_base)
        self.walls_to_base(state, base)
        self.pawns_to_base(state, base)

        print '\n'.join([
            ''.join([
                base[Vector(row=row, col=col)]
                for col in range(self.board_width + 100)
                if Vector(row=row, col=col) in base
            ])
            for row in range(self.board_height)
        ])

        print u''.join([
            '#{moves_made:03d} '.format(moves_made=len(context['history'])),
            self.yellow,
            u'YELLOW({type_}) walls:{walls:2} dist:{dist:2} {moves}'.format(
                type_=context[YELLOW]['type'][:2].upper(),
                walls=state[3],
                dist=len(context[YELLOW]['path']) - 1,
                moves='moves' if state[0] == YELLOW else '     ',
            ),
            self.color_end,
            u' | ',
            self.green,
            u'GREEN({type_}) walls:{walls:2} dist:{dist:2} {moves}'.format(
                type_=context[GREEN]['type'][:2].upper(),
                walls=state[4],
                dist=len(context[GREEN]['path']) - 1,
                moves='moves' if state[0] == GREEN else '     ',
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
        try:
            user_input = raw_input(message)
            return user_input.strip()
        except (EOFError, KeyboardInterrupt, SystemExit):
            return None

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

    def human_play(self, state, context):
        assert not self.is_terminal(state)

        wrong_attempts = 0
        while True:
            if wrong_attempts % 4 == 3:
                self.display_on_console(state, context)
                wrong_attempts = 0

            action = self.get_human_action()

            if action in self.GAME_CONTROLS:
                if action in ('quit', 'menu'):
                    return action
                # TODO: help, undo, save, change_players, hint, ...
                wrong_attempts += 1
                print self.messages['unknown_choice']
                continue

            try:
                new_state = self.execute_action(state, action)
            except InvalidMove as e:
                wrong_attempts += 1
                print self.red + str(e) + self.color_end
                continue

            if not self.is_terminal(state):
                self.update_context(new_state, context, action)
            return new_state

    def handle_game(self, state, context):
        assert not self.is_terminal(state)
        while not self.is_terminal(state):
            # TODO: avoid endless loop with move counter?
            #       e.g. assert len(context['history']) < 1000
            # TODO: when training network:
            #       1. save network to db every 50 games
            #       2. print output of the game after save
            #       3. print game counter
            self.display_on_console(state, context)
            # print_context_and_state(context, state)
            if 'human' == context[state[0]]['type']:
                result = self.human_play(state, context)
                if result in ('quit', 'menu'):
                    # TODO: at least undo, save, load
                    return result
                state = result
            elif 'qlnn' == context[state[0]]['type']:
                state = context[state[0]]['player'](state, context)
            elif 'heuristic' == context[state[0]]['type']:
                state = context[state[0]]['player'](state, context)
                continue
            elif 'path' == context[state[0]]['type']:
                state = context[state[0]]['player'](state, context)
                continue
            else:
                raise NotImplemented()

        self.display_on_console(state, context)
        print self.messages['game_ended']
        return 'menu'

    def train_game(self, players, types, show_and_save):
        state = self.initial_state()
        context = self.make_context(state, types)
        for color, type_ in types.items():
            context[color]['player'] = players[type_]
            if type_ == 'qlnn':
                qlnn_color = color
        qlnn = players['qlnn']
        old_activations = qlnn.activations_from_state(state)
        if show_and_save:
            print
        while not self.is_terminal(state):
            if len(context['history']) > 300:
                print '\nGame too long:', context['history'], '\n'
                break

            if show_and_save:
                self.display_on_console(state, context)

            invalid_actions = qlnn.invalid_actions(state, context)
            new_state = context[state[0]]['player'](state, context)

            if context[state[0]]['type'] == 'qlnn':
                new_activations = qlnn.activations
            else:
                new_activations = qlnn.activations_from_state(new_state)

            desired_output = qlnn.desired_output_vector(
                state[0],
                invalid_actions,
                old_activations,
                context['history'][-1],
                new_state,
                new_activations,
            )
            qlnn.learn(old_activations, desired_output)

            old_activations = new_activations
            state = new_state

        if show_and_save:
            self.display_on_console(state, context)

        if qlnn_color == state[0]:
            return False
        return True

    def handle_training(self, players, show_save_cycle=100,
                        display_games=False):
        game_counter = qlnn_wins = 0
        db_session = make_db_session('data.db')
        start = datetime.datetime.now()
        type_keys = [type_ for type_ in players]
        type_base = {
            0: {YELLOW: type_keys[0], GREEN: type_keys[1]},
            1: {YELLOW: type_keys[1], GREEN: type_keys[0]},
        }
        OVERALL_FMT = (
            u'\rgames:{games: 4}| sec.:{seconds: 5}s| sec./game:{pace}s| '
            u'win/loses: {won: 3} /{lost: 4}|  '
        )
        try:
            while True:
                types = type_base[game_counter % 2]
                show_and_save = not (game_counter + 1) % show_save_cycle
                display_game = show_and_save and display_games
                qlnn_win = self.train_game(players, types, display_game)
                qlnn_wins += int(qlnn_win)
                game_counter += 1
                delta = datetime.datetime.now() - start
                seconds = int(delta.total_seconds())
                message = OVERALL_FMT.format(
                    seconds=seconds,
                    games=game_counter,
                    pace=int(0.5 + (float(seconds) / game_counter)),
                    won=qlnn_wins,
                    lost=game_counter - qlnn_wins,
                )
                sys.stdout.write(message)
                sys.stdout.flush()
                if show_and_save:
                    sys.stdout.write('saving weights into database... ')
                    sys.stdout.flush()
                    players['qlnn'].update_in_db(db_session)
                    sys.stdout.write('saved\n')
        except KeyboardInterrupt:
            pass
        db_session.close()
        return 'quit'

    def train_path(self, state, context):
        players = {
            'qlnn': QlearningNetworkPlayer(self),
            # 'heuristic': HeuristicPlayer(self),
            'path': PathPlayer(self),
        }
        self.handle_training(players, show_save_cycle=1000)
        return 'quit'

    def train_heuristic(self, state, context):
        players = {
            'qlnn': QlearningNetworkPlayer(self),
            'heuristic': HeuristicPlayer(self),
        }
        self.handle_training(players, display_games=True)
        return 'quit'

    def run(self):
        game_mode = 'menu'
        handle_mode = {
            'menu': self.handle_menu,
            'game': self.handle_game,
            'train_vs_path': self.train_path,
            'train_vs_heuristic': self.train_heuristic,
        }
        state = self.initial_state()
        context = self.make_context(state)

        while game_mode != 'quit':
            game_mode = handle_mode[game_mode](state, context)
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

        return MENU_CHOICE[number]['mode']

    def handle_menu(self, state, context):

        while True:
            self.print_menu()
            mode = self.get_menu_input()
            if mode == 'unknown':
                print self.messages['unknown_choice']
                continue
            elif mode == 'quit':
                return 'quit'
            elif mode == 'train_vs_path':
                return 'train_vs_path'
            elif mode == 'train_vs_heuristic':
                return 'train_vs_heuristic'

            # new game or watch, or later TODO: load game
            for key, value in self.make_context(self.initial_state()).items():
                context[key] = value

            if mode.startswith('human'):
                context[YELLOW]['type'] = 'human'
                context[YELLOW]['player'] = None
            elif mode.startswith('path'):
                context[YELLOW]['type'] = 'path'
                context[YELLOW]['player'] = PathPlayer(self)
            elif mode.startswith('heuristic'):
                context[YELLOW]['type'] = 'heuristic'
                context[YELLOW]['player'] = HeuristicPlayer(self)
            elif mode.startswith('qlnn'):
                context[YELLOW]['type'] = 'qlnn'
                context[YELLOW]['player'] = QlearningNetworkPlayer(self)
            else:
                raise NotImplementedError('unknown mode %s' % mode)

            if mode.endswith('human'):
                context[GREEN]['type'] = 'human'
                context[GREEN]['player'] = None
            elif mode.endswith('path'):
                context[GREEN]['type'] = 'path'
                context[GREEN]['player'] = PathPlayer(self)
            elif mode.endswith('heuristic'):
                context[GREEN]['type'] = 'heuristic'
                context[GREEN]['player'] = HeuristicPlayer(self)
            elif mode.endswith('qlnn'):
                context[GREEN]['type'] = 'qlnn'
                context[GREEN]['player'] = QlearningNetworkPlayer(self)
            else:
                raise NotImplementedError('unknown mode %' % mode)

            return 'game'

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
# def pawn_distance_from_goal(state, color):
#     starting_position = state['pawns'][color]
#     goal_row = GOAL_ROW[color]
#     walls = state['placed_walls']
#
#     to_visit = collections.deque([(starting_position, 0)])
#     visited = set()
#
#     while to_visit:
#         position, distance = to_visit.popleft()
#         if position in visited:
#             continue
#         if position.row == goal_row:
#             return distance
#         visited.add(position)
#
#         right_distance = distance % 2 == int(color == state['on_move'])
#         for possible in adjacent_spaces_not_blocked(state, position):
#             jumps = right_distance and possible in state['pawns'].values()
#             if jumps:
#                 to_visit.append((possible, distance))
#             else:
#                 to_visit.append((possible, distance + 1))
#
#     error_msg_fmt = u'{color_name} player can not reach goal row!'
#     color_name = PLAYER_COLOR_NAME[color].upper()
#     raise Exception(error_msg_fmt.format(color_name=color_name))
#
#
# def player_status_to_base(state, base):
#     # TODO: WINNER info
#     for n, color in enumerate(state['pawns']):
#         row = n * 5 + 2
#         color_name = PLAYER_COLOR_NAME[color].upper()
#
#         line = color_name + u' player'
#         if color == state['on_move']:
#             line += ' - now playing'
#         status_line_to_base(row, line, base)
#
#         status_line_to_base(row + 1, PLAYER_GOAL_INFO[color], base)
#
#         walls = unicode(state['walls'][color])
#         status_line_to_base(row + 2, u' Walls: ' + walls, base)
#
#         line = u' Dist: ' + unicode(pawn_distance_from_goal(state, color))
#         status_line_to_base(row + 3, line, base)
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
# def status_to_base(state, history, base):
#     moves_made = len(history)
#     line = u'Moves made: ' + unicode(moves_made)
#     status_line_to_base(0, line, base)
#
#     player_status_to_base(state, base)
#
#     history_to_base(base, history)
#
#     # info: Invalid move, etc...
#     # menu possibilities
#     # input
#
#
# def display_on_console(state, colors_on, history=None, message=None,
#                        with_clear=True):
#     if history is None:
#         history = []
#     if with_clear:
#         clear_console()
#     base = make_base()
#     for direction, walls in state['placed_walls'].items():
#         for wall in walls:
#             wall_to_base(direction, wall, base, colors_on=colors_on)
#     for color, pawn in state['pawns'].items():
#         pawn_to_base(pawn, color, base, colors_on=colors_on)
#
#     status_to_base(state, history, base)
#
#     print_base(base)
#
#     if message is not None:
#         print message
#
#
# class InputError(Exception):
#     pass
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
# def parse_input():
#     try:
#         user_input = raw_input('Enter choice:')
#     except (EOFError, KeyboardInterrupt, SystemExit):
#         return ACTION_END, None
#
#     match = UNDO_INPUT_RE.match(user_input)
#     if match is not None:
#         return ACTION_UNDO, None
#
#     match = WALL_INPUT_RE.match(user_input)
#     if match is not None:
#         direction, row, col = match.groups(0)
#         return ACTION_MOVE, {
#             'type': 'wall',
#             'direction': INPUT_DIRECTIONS[direction],
#             'position': Vector(
#                 row=int(row),
#                 col=COLUMN_LETTERS.find(col.lower())
#             ),
#         }
#
#     match = MOVE_INPUT_RE.match(user_input)
#     if match is not None:
#         row, col = match.groups(0)
#         return ACTION_MOVE, {
#             'type': 'pawn',
#             'position': Vector(
#                 row=int(row),
#                 col=COLUMN_LETTERS.find(col.lower())
#             ),
#         }
#
#     match = QUIT_INPUT_RE.match(user_input)
#     if match is not None:
#         return ACTION_END, None
#
#     return ACTION_UNKNOWN, None
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
#     colors_on = options.colors_on
#     if os.getenv('ANSI_COLORS_DISABLED') is not None:
#         colors_on = False
#
#     game = Quoridor2()
#     state = game.initial_state()
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
#         if traceback.format_exc() != 'None\n':
#             traceback.print_exc()
#
#     if options.example:
#         random_pawn_positions(game, state)
#         random_walls(game, state)
#         display_on_console(state, colors_on, with_clear=options.with_clear)
#         return
#
#     message = None
#     history = []
#     while not game.is_terminal(state):
#         display_on_console(
#             state,
#             colors_on,
#             history=history,
#             message=message,
#             with_clear=options.with_clear,
#         )
#         message = None
#         action_type, action_info = parse_input()
#         if action_type == ACTION_END:
#             break
#         elif action_type == ACTION_UNDO:
#             # print history
#             if history:
#                 game.undo(state, history.pop())
#             else:
#                 message = 'No history to undo.'
#         elif action_type == ACTION_MOVE:
#             try:
#                 action = (
#                     action_info.get('direction'),
#                     action_info['position']
#                 )
#                 if action_info['type'] == 'wall':
#                     game.execute_action(state, action)
#                     history.append(action)
#                 else:
#                     history_position = current_pawn_position(state)
#                     game.execute_action(state, action)
#                     history.append((None, history_position))
#             except InvalidMove as e:
#                 message = e.message
#         else:
#             # assert action_info['action'] == ACTION_UNKNOWN
#             message = 'Wrong input. (Examples: wh1e, wv1e, p1e, 1e, quit, q)'
#
#     if game.is_terminal(state):
#         display_on_console(state, colors_on, with_clear=options.with_clear)
#         print PLAYER_COLOR_NAME[FOLLOWING_PLAYER[state['on_move']]] + ' wins!'
#
#
# def main():
#     parser = OptionParser()
#     parser.add_option(
#         '-c', '--colors', dest='colors_on', default=False, action='store_true',
#         help='Enable color output in console mode. Disabled by default.'
#     )
#
#     parser.add_option(
#         '-e', '--example', dest='example', default=False, action='store_true',
#         help=(
#             'In console mode, create random board position display it and end.'
#             ' Serves for debugging.'
#         )
#     )
#
#     parser.add_option(
#         '-r', '--random', dest='random', default=False, action='store_true',
#         help=(
#             'In console mode, play with random playes.'
#         )
#     )
#
#     parser.add_option(
#         '-w', '--withot-clear-console', dest='with_clear', default=True, action='store_false',
#         help=(
#             'Do not clear console on each move.'
#         )
#     )
#
#     parser.add_option(
#         '-q', '--qlearn', dest='qlearn', default=False, action='store_true',
#         help=(
#             'Train QPlayer.'
#         )
#     )
#
#     options, args = parser.parse_args()
#     console_run(options)


def manual_test():
    game = ConsoleGame(console_colors=True)
    state = game.initial_state()
    # state = (GREEN, 30, 9, 3, 3, frozenset([3, 6]), frozenset([18, 27]))
    game.display_on_console(state)


def main():
    # manual_test()
    # return
    game = ConsoleGame(console_colors=True)
    game.run()
