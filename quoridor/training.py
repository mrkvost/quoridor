#!/usr/bin/env python2

import re
import random
import copy
import numpy
import sys

from sqlalchemy.orm.exc import NoResultFound

from ai import MLMCPerceptron

from db import (
    Network,
    make_db_session,
    db_update_network,
    db_save_network,
    db_load_network,
    build_db,
)

from core import (
    Quoridor2,
    state_from_key,
    key_from_state,
    int_to_position,
    HORIZONTAL,
    VERTICAL,
    Vector,
    current_pawn_position,
    YELLOW,
    GREEN,
    InvalidMove,
    PLAYER_UTILITIES,
)


SIZES_PATTERN = r'\d+(_\d+)+'
SIZES_NAME_RE = re.compile(SIZES_PATTERN)

REWARD = 100
MAXINT = sys.maxint


def input_vector_from_game_state(state):
    # TODO: what color is mine? or will I expect it to be 0 allways me?
    """
    1: kto je na tahu, ja alebo super (0 or 1), moze znamenat aj smer hry, teda
       ze ktory panak kam ide
    2: pozicia mojho panaka (0, 1, ..., 80)
    3: pozicia superovho panaka (0, ..., 80)
    4: pocet mojich murikov (0, ..., 10)
    5: pocet superovych murikov (0, ..., 10)
    6...69: vertikalne muriky (0 or 1)
    70...133: horizontalne muriky (0 or 1)
    """
    key = key_from_state(state)
    input_vector = key[:5]
    input_vector += tuple([int(i in key[5]) for i in range(64)])
    input_vector += tuple([int(i in key[6]) for i in range(64)])
    return input_vector


def create_or_load_network(db_session, network_name):
    assert SIZES_NAME_RE.match(network_name)
    perceptron = None
    network = db_session.query(Network).filter_by(name=network_name).first()
    if network is None:
        sizes = [int(size) for size in network_name.split('_')]
        perceptron = MLMCPerceptron(sizes)
        db_save_network(db_session, perceptron, name=network_name)
        network = db_session.query(Network).filter_by(name=network_name).one()

    if perceptron is None:
        network_attributes = db_load_network(db_session, network_name)
        perceptron = MLMCPerceptron(**network_attributes)

    return perceptron


MOVE_DELTA = {
    0: Vector(row=-2, col=+0),  # upup
    1: Vector(row=-1, col=-1),  # upleft
    2: Vector(row=-1, col=+0),  # up
    3: Vector(row=-1, col=+1),  # upright
    4: Vector(row=+0, col=-2),  # leftleft
    5: Vector(row=+0, col=-1),  # left
    6: Vector(row=+0, col=+1),  # right
    7: Vector(row=+0, col=+2),  # rightright
    8: Vector(row=+1, col=-1),  # downleft
    9: Vector(row=+1, col=+0),  # down
    10: Vector(row=1, col=+1),  # downright
    11: Vector(row=2, col=+0),  # downdown
}


def number_to_action(number):
    assert 0 <= number <= 143
    if number < 64:     # HORIZONTAL
        return (HORIZONTAL, int_to_position(number, 9))
    elif number < 128:  # VERTICAL
        return (HORIZONTAL, int_to_position(number - 64, 9))
    else:
        return (None, MOVE_DELTA[number - 128])


def mkaction(game, state):
    while True:
        try:
            action_number = random.randint(0, 139)
            action = number_to_action(action_number)
            action_type, position = action
            if action_type is None:
                current_position = current_pawn_position(state)
                position = Vector(
                    row=position.row + current_position.row,
                    col=position.col + current_position.col,
                )
                action = (action_type, position)
            game.execute_action(state, action)
            return action_number, action
        except InvalidMove:
            pass


def find_min(sequence):
    assert len(sequence)
    min_i = 0
    min_element = +MAXINT
    for i, element in enumerate(sequence):
        if min_element > element:
            min_element = element
            min_i = i
    return min_i, min_element


def find_max(sequence):
    assert len(sequence)
    max_i = 0
    max_element = -MAXINT
    for i, element in enumerate(sequence):
        if max_element < element:
            max_element = element
            max_i = i
    return max_i, max_element


def train_MLMC_estimate_Q_value(cycles=100, save_every=1):
    """
    akcie:
        128 = 64 horizontalne + 64 vertikalne moznne pozicie murikov
         12 = 4 obycajne kroky, 8 moznych miest na skok cez supera
        140 spolu
    """
    # TODO: trestat siet za nemozne tahy? napr. nemozny skok, alebo murik?
    # TODO: db_save_network
    # build_db('data.db')
    network_name = '133_266_140'
    db_session = make_db_session('data.db')
    perceptron = create_or_load_network(db_session, network_name)

    game = Quoridor2()
    for cycle_number in range(1, 1 + cycles):
        print 'starting new_game'
        state = game.initial_state()

        old_input_vector = input_vector_from_game_state(state)
        old_activations = list(perceptron.propagate_forward(old_input_vector))

        # print 'old_activations[-1]:', old_activations[-1]

        while not game.is_terminal(state):
            action_number, action = mkaction(game, state)
            new_input_vector = input_vector_from_game_state(state)
            new_activations = list(perceptron.propagate_forward(new_input_vector))
            desired_output_vector = copy.deepcopy(old_activations[-1])
            # print 'new_activations[-1]:', new_activations[-1]

            if state['on_move'] == YELLOW:
                best_action_number, best_value = find_min(new_activations[-1])
            else:
                best_action_number, best_value = find_max(new_activations[-1])

            if game.is_terminal(state):
                best_value += PLAYER_UTILITIES[state['on_move']] * REWARD

            # best_value = PLAYER_UTILITIES[state['on_move']] * min(abs(best_value), REWARD)

            desired_output_vector[action_number] = best_value
            # desired_output_vector = numpy.array([
            #     REWARD if value > REWARD else (
            #         -REWARD if value < -REWARD else value
            #     )
            #     for value in desired_output_vector
            # ])
            perceptron.propagate_backward(old_activations, desired_output_vector)

            # print perceptron.weights
            # print 'x'*80

            old_input_vector = new_input_vector
            old_activations = new_activations

        print 'games played:', cycle_number

        if (cycle_number + 1) % save_every == 0:
            print 'updating in db...'
            db_update_network(db_session, network_name, perceptron)

    db_update_network(db_session, network_name, perceptron)

def run():
    train_MLMC_estimate_Q_value()
