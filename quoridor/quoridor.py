# -*- coding: utf-8 -*-

import os
import re
import copy
# import time
import random
import collections
# import traceback

# from optparse import OptionParser

from core import (
    YELLOW,
    GREEN,
    PLAYER_COLOR_NAME,
    FOLLOWING_PLAYER,
    BOARD_SIZE_DEFAULT,

    horizontal_crossers,
    vertical_crossers,
    crossing_actions,
    InvalidMove,
    Quoridor2,

)

from players import Player
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
PAWN_MOVE = {
    'u': 0, 'up': 0,
    'r': 1, 'right': 1,
    'd': 2, 'down': 2,
    'l': 3, 'left': 3,
    'uu': 4, 'rr': 5, 'dd': 6, 'll': 7,
    'ur': 8, 'ru': 8,
    'ul': 9, 'lu': 9,
    'dr': 10, 'rd': 10,
    'dl': 11, 'ld': 11,
}

MENU_CHOICE = (
    {'text': 'New Game Human only', 'mode': 'human_human'},

    {'text': 'New Game vs Neural Network (Human First)', 'mode': 'human_network'},
    {'text': 'New Game vs Neural Network (Human Second)', 'mode': 'network_human'},
    {'text': 'New Game vs Heuristic (Human First)', 'mode': 'human_heuristic'},
    {'text': 'New Game vs Heuristic (Human Second)', 'mode': 'heuristic_human'},

    {'text': 'Watch Game Heuristic vs Heuristic', 'mode': 'heuristic_heuristic'},
    {'text': 'Watch Game Neural Network vs Heuristic', 'mode': 'network_heuristic'},
    {'text': 'Watch Game Neural Network vs Neural Network ', 'mode': 'network_network'},

    {'text': 'Save Last Game', 'mode': 'save'},
    {'text': 'Load Game', 'mode': 'load'},
    {'text': 'Quit', 'mode': 'quit'},
)

MODE = {
    0: 'human_human',

    1: 'human_network',
    2: 'network_human',
    3: 'human_heuristic',
    4: 'heuristic_human',

    5: 'heuristic_heuristic',
    6: 'network_heuristic',
    7: 'network_network',

    8: 'save',
    9: 'load',
    10: 'quit',

    # 11: 'menu',
    # 12: 'back_to_menu...',
}


class HumanPlayer(Player):
    def play(self, state):
        return


class HeuristicPlayer(Player):
    def __init__(self, game, pawn_moves=0.6, **kwargs):
        super(HeuristicPlayer, self).__init__(game)
        self.pawn_moves = pawn_moves

    def shortest_path(self, state, player):
        current_position = state[1 + player]
        to_visit = collections.deque((current_position, ))
        visited = set()
        previous_positions = {}

        while to_visit:
            position = to_visit.popleft()
            if position in visited:
                continue

            if position in self.game.goal_positions[player]:
                path = [position]
                while True:
                    previous_position = previous_positions.get(path[-1])
                    path.append(previous_position)
                    if previous_position == current_position:
                        return path

            visited.add(position)
            for move in self.game.blocker_positions[position]:
                placed_walls = state[5 + (move % 2)]
                intercepting_walls = (
                    self.game.blocker_positions[position][move]
                )
                if placed_walls is None or not (intercepting_walls & placed_walls):
                    new_position = position + self.game.move_deltas[move]
                    if new_position not in visited:
                        to_visit.append(new_position)
                    if new_position not in previous_positions:
                        previous_positions[new_position] = position

    def blockers(self, path, crossers, avoid=None):
        if avoid is None:
            avoid = set()
        blocking_wall_actions = set()
        for i in range(len(path) - 1):
            move = self.game.delta_moves[path[i + 1] - path[i]]
            direction = move % 2
            for wall in self.game.blocker_positions[path[i]][move]:
                wall_action = wall + direction * self.game.wall_board_positions
                if wall_action not in crossers or wall_action not in avoid:
                    blocking_wall_actions.add(wall_action)
        return blocking_wall_actions

    def make_context(self, state):
        crossers = crossing_actions(state, self.game.wall_board_size)

        yellow_shortest_path = self.shortest_path(state, YELLOW)
        assert yellow_shortest_path is not None, "no path to goal for yellow"
        yellow_blockers = self.blockers(yellow_shortest_path, crossers)

        green_shortest_path = self.shortest_path(state, GREEN)
        assert green_shortest_path is not None, "no path to goal for green"
        green_blockers = self.blockers(green_shortest_path, crossers)

        return {
            'last_action': None,
            'crossers': crossers,
            YELLOW: {
                'path': yellow_shortest_path,
                'blockers': yellow_blockers,
                'goal_cut': set(),
            },
            GREEN: {
                'path': green_shortest_path,
                'blockers': green_blockers,
                'goal_cut': set(),
            },
        }

    def good_blockers(self, context, player, next_):
        for action in context[next_]['blockers']:
            if action not in context[player]['blockers']:
                if action not in context['crossers']:
                    if action not in context[next_]['goal_cut']:
                        yield action

    def should_move(self, state, context):
        player = state[0]
        next_ = FOLLOWING_PLAYER[player]
        if not state[3 + player]:
            return True     # no walls left
        elif len(context[player]['path']) == 2:
            return True     # last winning move
        elif state[1 + player] in self.game.goal_positions[next_]:
            return True     # on the first line is probably the beginning
        elif len(context[next_]['blockers']) > 2:
            # has enough time to block at least once in the future
            return random.random() < self.pawn_moves
        else:
            # probably one of the last changes to block
            return False

    def _try_good_wall_action(self, new_state, temp_state, context, player,
                             next_, action):
        direction = int(action >= self.game.wall_board_positions)
        wall = action - direction * self.game.wall_board_positions
        temp_state[5 + direction].add(wall)
        new_opponent_path = self.shortest_path(temp_state, next_)
        if new_opponent_path is None:
            temp_state[5 + direction].remove(wall)
            context[next_]['goal_cut'].add(action)
            return False
        new_state[5 + direction] = frozenset(temp_state[5 + direction])
        new_state[3 + player] -= 1
        context[next_]['path'] = new_opponent_path
        args = (
            state,
            self.game.wall_board_size,
            self.game.wall_board_positions,
            wall
        )
        crossers_getters = {0: vertical_crossers, 1: horizontal_crossers}
        new_crossers = crossers_getters[direction](*args)
        for crosser in new_crossers:
            context['crossers'].add(crosser)
        context[next_]['blockers'] = self.blockers(
            path,
            context['crossers'],
            context[next_]['goal_cut']
        )
        new_state[0] = next_
        return True

    def move_pawn(self, new_state, context, player, next_):
        current_position = context[player]['path'].pop()
        new_position = context[player]['path'][-1]
        if new_position == new_state[1 + next_]:     # occupied, will jump
            semi = context[player]['path'].pop()
            # TODO: if opponent occupies last move, this will fail, but this
            #       does not happen often...
            new_position = context[player]['path'][-1]
        move = self.game.delta_moves[new_position - current_position]

        context['last_action'] = self.game.wall_moves + move
        context[player]['goal_cut'].clear()
        context[player]['blockers'] = self.blockers(
            context[player]['path'],
            context['crossers'],
            context[player]['goal_cut']
        )
        new_state[1 + player] = new_position
        new_state[0] = next_

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
            temp_state = new_state[:5] + [set(new_state[5]), set(new_state[6])]
            for action in self.good_blockers(context, player, next_):
                success = self._try_good_wall_action(
                    new_state,
                    temp_state,
                    context,
                    player,
                    next_,
                    action,
                )
                if success:
                    return tuple(new_state)
            # TODO: is there something more to try?

        self.move_pawn(new_state, context, player, next_)
        return tuple(new_state)

    def update_context(self, state, context, last_action):
        if self.game.is_terminal(state):
            return

        context['last_action'] = last_action
        player = state[0]
        next_ = FOLLOWING_PLAYER[player]

        if 0 <= last_action < self.game.wall_moves:   # wall
            if last_action < self.game.wall_board_positions:
                context['crossers'] = context['crossers'].union(
                    horizontal_crossers(
                        state,
                        self.game.wall_board_size,
                        self.game.wall_board_positions,
                        last_action
                    )
                )
            else:
                context['crossers'] = context['crossers'].union(
                    vertical_crossers(
                        state,
                        self.game.wall_board_size,
                        self.game.wall_board_positions,
                        last_action - self.game.wall_board_positions
                    )
                )
            for color in (YELLOW, GREEN):
                if last_action in context[color]['blockers']:
                    context[color]['path'] = self.shortest_path(state, color)
                    context[color]['blockers'] = self.blockers(
                        context[color]['path'],
                        context['crossers'],
                        context[color]['goal_cut']
                    )
            return

        last_path = context[next_]['path']
        if last_path[-2] == state[1 + next_]:
            context[next_]['path'].pop()
        elif len(last_path) > 2 and last_path[-3] == state[1 + next_]:
            context[next_]['path'].pop()
            context[next_]['path'].pop()
        else:
            context[next_]['path'] = self.shortest_path(state, next_)

        context[next_]['goal_cut'].clear()
        context[next_]['blockers'] = self.blockers(
            context[next_]['path'],
            context['crossers'],
            context[next_]['goal_cut']
        )


def clear_console():
    os.system(CONSOLE_CLEAR[os.name])


class ConsoleGame(Quoridor2):
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

        self.output_base = self._make_output_base()

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
        self.messages = self._make_output_messages()

        self.history = []

    def _make_output_base(self):
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

    def _walls_to_base(self, state, base):
        new_base = copy.deepcopy(base)

        for wall in state[5]:
            row, col = divmod(wall, self.board_size - 1)
            row_offset = (row + 1) * self.field_height
            col_offset = col * self.field_width + 1
            for col_delta in range(self.wall_length_horizontal):
                position = Vector(row=row_offset, col=col_offset + col_delta)
                new_base[position] = u'\u2550'

        for wall in state[6]:
            row, col = divmod(wall, self.board_size - 1)
            row_offset = row * self.field_height + 1
            col_offset = (col + 1) * self.field_width
            for row_delta in range(self.wall_length_vertical):
                position = Vector(row=row_offset + row_delta, col=col_offset)
                new_base[position] = u'\u2551'

        row_offset = self.field_height
        col_offset = self.field_width
        for row in range(self.wall_board_size):
            for col in range(self.wall_board_size):
                num = row * self.wall_board_size + col
                if num in state[5] or num in state[6]:
                    continue

                num = str(num)
                for i in range(len(num)):
                    position = Vector(
                        row=row_offset + row * self.field_height,
                        col=col_offset + col * self.field_width - i,
                    )
                    new_base[position] = num[-i - 1]

        return new_base

    def _pawns_to_base(self, state, base):
        new_base = copy.deepcopy(base)

        for player in (YELLOW, GREEN):
            color_start = self.pawn_colors[player]

            row, col = divmod(state[1 + player], self.board_size)
            leftmost = col * self.field_width + BOARD_BORDER_THICKNESS
            rightmost = leftmost + self.field_inner_width - 2
            top = row * self.field_height + BOARD_BORDER_THICKNESS
            bottom = top + self.field_inner_height - 1

            # top and bottom sides:
            for column in range(leftmost, rightmost + 1):
                new_base[Vector(row=top, col=column)] = u'\u203e'
                new_base[Vector(row=bottom, col=column)] = u'_'

            # left and right sides:
            for row in range(top, bottom + 1):
                new_base[Vector(row=row, col=leftmost)] = (
                    color_start + u'\u23b8'
                )
                new_base[Vector(row=row, col=rightmost)] = (
                    u'\u23b9' + self.color_end
                )

            # corners:
            new_base.update({
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
                    new_base[position] = name[offset - 1]

        return new_base

    def display_on_console(self, state, history=None):
        if history is None:
            history = []
        base = self._walls_to_base(state, self.output_base)
        base = self._pawns_to_base(state, base)

        print '\n'.join([
            ''.join([
                base[Vector(row=row, col=col)]
                for col in range(self.board_width + 100)
                if Vector(row=row, col=col) in base
            ])
            for row in range(self.board_height)
        ])

        print u''.join([
            '{moves_made:03d} '.format(moves_made=len(history)),
            u'| ',
            self.yellow,
            u'YELLOW walls:{walls:2} {moves}'.format(
                walls=state[3],
                moves='moves' if state[0] == YELLOW else '     ',
            ),
            self.color_end,
            u' | ',
            self.green,
            u'GREEN walls:{walls:2} {moves}'.format(
                walls=state[4],
                moves='moves' if state[0] == GREEN else '     ',
            ),
            self.color_end,
            u' |',
        ])

    def _make_output_messages(self):
        return {
            'yellow_enter_choice': ''.join([
                self.yellow,
                'Enter choice: ',
                self.color_end
            ]),
            'green_enter_choice': ''.join([
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

    def _prompt(self, message):
        try:
            user_input = raw_input(message)
            return user_input.strip()
        except (EOFError, KeyboardInterrupt, SystemExit):
            return None

    def _unknown(self, game_mode):
        print self.messages['unknown_choice']
        return game_mode

    def _play(self, action):
        try:
            self._state = self.execute_action(self._state, action)
            self.history.append(action)
            if self.is_terminal(self._state):
                self.display_on_console(self._state, history=self.history)
                print self.cyan + ' - GAME ENDED -' + self.color_end
                return 'end'
            return 'success'
        except InvalidMove as e:
            print self.red + str(e) + self.color_end
            return 'fail'

    def _handle_human_human(self):
        assert not self.is_terminal(self._state)
        move_result = {
            'end': 'menu',
            'success': 'human_human',
            'fail': 'human_human',
        }

        self.display_on_console(self._state, history=self.history)

        user_input = self._prompt(self.messages['yellow_enter_choice'])
        if not user_input:
            if user_input is None:
                return 'quit'
            return self._unknown('human_human')

        match = re.match(
            (
                r'(?i)'
                r'(?P<type>'
                    r'undo|quit|exit|[hv]|[urdl]{1,2}|up|right|down|left'
                r')?'
                r'(?P<column>[a-h])?'       # TODO: what with variable size?
                r'(?P<number>[-+]?\d+)?'
                r'$'
            ),
            user_input
        )
        if match is None:
            return self._unknown('human_human')

        data = match.groupdict()
        if not any([data.values()]):
            return self._unknown('human_human')

        if data['type'] is None:
            if data['number'] is None or data['column'] is not None:
                return self._unknown('human_human')
            action = int(data['number'])
            if action < 0:
                if action == -1:
                    return 'quit'
                pass    # TODO: undo, new, save, load, switch_opponent
            elif action not in self.possible_game_actions:
                return self._unknown('human_human')
            return move_result[self._play(action)]

        data['type'] = data['type'].lower()
        if data['type'] == 'undo':
            if data['number'] is not None or data['column'] is not None:
                return self._unknown('human_human')
            # TODO: undo
            return 'human_human'
        elif data['type'] in ('quit', 'exit'):
            if data['number'] is not None or data['column'] is not None:
                return self._unknown('human_human')
            return 'quit'

        if data['type'] in ('h', 'v'):
            shift = {'h': 0, 'v': 64}
            if data['column'] is None:
                action = int(data['number']) + shift[data['type']]
            else:
                row = int(data['number'])
                column = ord(data['column'].lower()) - 97
                action = (self.board_size - 1) * row + column + shift[data['type']]
            return move_result[self._play(action)]

        if data['number'] is not None or data['column'] is not None:
            return self._unknown('human_human')
        if data['type'] not in PAWN_MOVE:
            return self._unknown('human_human')

        action = PAWN_MOVE[data['type']] + 128
        return move_result[self._play(action)]

    def _handle_human_heuristic(self):
        assert not self.is_terminal(self._state)

        # print 'context last_action:', self.context['last_action']
        # print 'context crossers:', self.context['crossers']
        # print 'context yellow:', self.context[YELLOW]
        # print 'context green:', self.context[GREEN]
        # print 'state:', self._state

        if self._state[0] == YELLOW:
            move_count = len(self.history)
            result = self._handle_human_human()
            if result == 'human_human':
                result = 'human_heuristic'
            if move_count < len(self.history):
                self.player2.update_context(
                    self._state,
                    self.context,
                    self.history[-1]
                )
            return result


        self.display_on_console(self._state, history=self.history)
        self._state = self.player2.play(self._state, self.context)
        self.history.append(self.context['last_action'])
        if self.is_terminal(self._state):
            self.display_on_console(self._state, history=self.history)
            return 'menu'
        return 'human_heuristic'

    def run(self):
        game_mode = 'menu'
        handle_mode = {
            'menu': self._handle_menu,
            'human_human': self._handle_human_human,
            'human_heuristic': self._handle_human_heuristic,
        }

        while game_mode != 'quit':
            game_mode = handle_mode[game_mode]()
        print

    def _handle_menu(self):
        self._print_menu()
        user_input = self._prompt(self.messages['yellow_enter_choice'])
        if not user_input:
            if user_input is None:
                return 'quit'
            return self._unknown('menu')

        match = re.match(r'(?P<number>\d+)\s*(?P<path>.+)?', user_input)
        if match is None:
            return self._unknown('menu')

        number = int(match.group('number'))
        if number not in MODE:
            return self._unknown('menu')

        if match.group('path'):
            if number == 8:
                pass    # TODO: save
            elif number == 9:
                pass    # TODO: load
            else:
                return self._unknown('menu')

        mode = MODE[number]
        if mode in ('human_human', 'human_heuristic'):
            self._state = self.initial_state()
            self.history = []

        if mode == 'human_heuristic':
            self.history = []
            self.player2 = HeuristicPlayer(self)
            self.context = self.player2.make_context(self._state)

        return mode

    def _print_menu(self):
        print self.messages['menu_choose']
        for number, choice in enumerate([c['text'] for c in MENU_CHOICE]):
            print '{number:2} - {choice}'.format(
                number=number, choice=choice,
            )
        print


# ACTION_TYPE = {
#     None: Pawn,
#     HORIZONTAL: HorizontalWall,
#     VERTICAL: VerticalWall,
# }
#
#
# def print_base(base):
#     print '\n'.join([
#         ''.join([
#             base[Vector(row=row, col=col)] for col in range(BOARD_WIDTH + 100)
#             if base.get(Vector(row=row, col=col)) is not None
#         ]) for row in range(BOARD_HEIGHT)
#     ])
#
#
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
    # for i in range(10):
    #     color = i + 30
    #     print (
    #         str(color) + u'  \x1b[1m\x1b[' + str(color) + 'm' + ' - GAME ENDED -' + COLOR_END_CONSOLE
    #     )
