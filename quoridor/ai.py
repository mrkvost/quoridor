import random

from math import exp
from copy import deepcopy

DEBUG = True
BIAS_INPUT = -1
LEARNING_RATE = 0.5


def nice_print_data(data):
    if DEBUG:
        print 'deltas:', data['deltas']
        print 'values: desired:', data['values']['desired_output']
        print '        activation: ', data['values']['activation']
        print '        output: ', data['values']['output']
        print 'old_weights: hidden:', data['old_weights']['hidden']
        print '             output:', data['old_weights']['output']
        print 'new_weights: hidden:', data['new_weights']['hidden']
        print '             output:', data['new_weights']['output']


def make_data(input_vector, desired_output, hidden_weights,
              output_weights):
    return {
        'values': {
            'input': deepcopy(input_vector),
            'activation': [],
            'output': [],
            'desired_output': deepcopy(desired_output),
        },
        'old_weights': {
            'hidden': deepcopy(hidden_weights),
            'output': deepcopy(output_weights),
        },
        'new_weights': {
            'hidden': [],
            'output': [],
        },
        'deltas': [],
    }


def sigmoid(z):
    return 1.0 / (1.0 + exp(-z))


def calculate_single(input_data, weights):
    return sigmoid(sum([
        value * weights[i]
        for i, value in enumerate(input_data)
    ]))


def calculate_layer(input_data, layer_weights):
    output_vector = []
    for weights in layer_weights:
        output_vector.append(calculate_single(input_data, weights))
    return output_vector


def calculate_activations_and_output(data):
    data['values']['activation'].append(data['values']['input'] + [BIAS_INPUT])
    for layer_weights in data['old_weights']['hidden']:
        data['values']['activation'].append(
            calculate_layer(data['values']['activation'][-1], layer_weights)
        )
        data['values']['activation'][-1].append(BIAS_INPUT)

    data['values']['activation'].append(
        calculate_layer(
            data['values']['activation'][-1],
            data['old_weights']['output'],
        )
    )
    data['values']['output'] = data['values']['activation'][-1]


def calculate_output_delta(desired_output, output):
    return (desired_output - output) * output * (1.0 - output)


def calculate_new_weights(weights, input_vector, faster):
    """
    weights = current weights to be updated
    input_vector = input activations or input data
    faster = learning_rate * delta
    """
    new_weights = []
    for i, weight in enumerate(weights):
        new_weights.append(weight + input_vector[i] * faster)
    # print 'input_vector:', input_vector
    # print 'new_weights:', new_weights
    return new_weights


def calculate_output_layer(data):
    deltas = []
    for neuron_number, output_value in enumerate(data['values']['output']):
        desired_output_value = data['values']['desired_output'][neuron_number]
        delta = calculate_output_delta(desired_output_value, output_value)
        deltas.append(delta)
        faster = LEARNING_RATE * delta
        data['new_weights']['output'].append(
            calculate_new_weights(
                data['old_weights']['output'][neuron_number],
                data['values']['activation'][-2],
                faster,
            )
        )
    data['deltas'].append(deltas)


def calculate_hidden_delta(output, next_layer_deltas, outgoing_weights):
    return output * (1.0 - output) * sum([
        outgoing_weights[i] * delta
        for i, delta in enumerate(next_layer_deltas)
    ])


def calculate_hidden_layer(data):
    hidden_layers_count = len(data['old_weights']['hidden'])
    all_weights = (
        data['old_weights']['hidden'] + [data['old_weights']['output']]
    )
    for i in range(hidden_layers_count):
        layer_index = -i - 1
        current_layer_activations = (
            data['values']['activation'][layer_index - 1]
        )
        next_layer_weights = all_weights[layer_index]

        new_deltas = []
        new_layer_weights = []
        # last activation is BIAS, so we dont calculate delta for it...
        for neuron_number, activation in enumerate(current_layer_activations[:-1]):
            outgoing_weights = [weights[neuron_number] for weights in next_layer_weights]
            delta = calculate_hidden_delta(
                activation,
                data['deltas'][-1], # last added deltas are from next layer
                outgoing_weights
            )
            new_deltas.append(delta)
            faster = LEARNING_RATE * delta
            # print 'delta, faster:', delta, faster
            # print "data['old_weights']['hidden'][layer_index][neuron_number]:", data['old_weights']['hidden'][layer_index][neuron_number]
            # print 'j'*30
            new_layer_weights.append(
                calculate_new_weights(
                    data['old_weights']['hidden'][layer_index][neuron_number],
                    data['values']['activation'][layer_index - 2],
                    faster
                )
            )
            # print 'new_layer_weights[-1]:', new_layer_weights[-1]
        data['new_weights']['hidden'].append(new_layer_weights)
        data['deltas'].append(new_deltas)
    data['new_weights']['hidden'] = data['new_weights']['hidden'][::-1]
    data['deltas'] = data['deltas'][::-1]


def update_weights(input_vector, desired_output, hidden_weights,
                   output_weights):
    data = make_data(
        input_vector,
        desired_output,
        hidden_weights,
        output_weights,
    )
    calculate_activations_and_output(data)
    # print '-'*140
    # nice_print_data(data)
    calculate_output_layer(data)
    # print '-'*140
    # nice_print_data(data)
    calculate_hidden_layer(data)
    # print '-'*140
    nice_print_data(data)
    return data


class MLMCPerceptron(object):
    """Multi-layer multi-class perceptron."""

    WEIGHT_DELTA = 0.01
    DOUBLE_WEIGHT_DELTA = 2 * WEIGHT_DELTA

    def __init__(self, sizes):
        assert len(sizes) > 1
        self.sizes = sizes
        self.init_weights(sizes)

    def generate_weight(self):
        # return 0.5
        return random.random() * self.DOUBLE_WEIGHT_DELTA - self.WEIGHT_DELTA

    def generate_weights_for_neuron(self, previous_layer_size):
        weights = []
        for k in range(previous_layer_size + 1):
            weight = self.generate_weight()
            weights.append(weight)
        return weights

    def generate_layer_weights(self, previous_layer_size, current_layer_size):
        return [
            self.generate_weights_for_neuron(previous_layer_size)
            for j in range(current_layer_size)
        ]

    def init_weights(self, sizes):
        hidden_weights = []
        for i, previous_layer_size in enumerate(sizes[:-2]):
            hidden_weights.append(
                self.generate_layer_weights(previous_layer_size, sizes[i + 1])
            )
        output_weights = self.generate_layer_weights(
            sizes[-2],
            sizes[-1]
        )

        hidden_weights = [
            [
                [1, -0.5, 0],
                [-1, -0, 0.3],
                # [0, 0.5, -0.3],
            ],
        ]
        output_weights = [[0.3, 0.6, -1]]

        self.weights = {'hidden': hidden_weights, 'output': output_weights}
        self.data = make_data([], [], [], [])
        self.data['new_weights'] = {
            'hidden': self.weights['hidden'],
            'output': self.weights['output'],
        }

    def calculate(self, input_data):
        # print
        data = input_data
        for layer_weights in self.weights['hidden']:
            # print 'data:', data
            # print 'layer_weights:', layer_weights
            data = calculate_layer(data + [BIAS_INPUT], layer_weights)
        data = calculate_layer(data + [BIAS_INPUT], self.weights['output'])
        return data

    def update_weights(self, input_data, desired_output_data):
        self.data = update_weights(
            input_data,
            desired_output_data,
            self.weights['hidden'],
            self.weights['output'],
        )
