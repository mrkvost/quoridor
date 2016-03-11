import math
import random


def make_weight_fmt(precision):
    return '{{0:+{size}.{precision}f}}'.format(
        size=precision+2,
        precision=precision,
    )

def print_layer_weights(layer, fmt, preceeding=''):
    print preceeding + ' || '.join([
        ', '.join([fmt.format(w) for w in neuron])
        for neuron in layer
    ])


def print_weights(weights, fmt):
    for layer in weights:
        print_layer_weights(layer, fmt)


class SimplePerceptron(object):
    WEIGHT_DELTA = 0.01
    DOUBLE_WEIGHT_DELTA = 2 * WEIGHT_DELTA
    BIAS_INPUT = -1
    LEARNING_RATE = 0.1

    def __init__(self, input_size=None, weights=None):
        assert (input_size is not None) or weights
        assert (input_size is None) or not weights

        if input_size is not None:
            self.weights = self.initial_weights(input_size)
        elif weights:
            self.weights = weights

    def generate_weight(self):
        return random.random() * self.DOUBLE_WEIGHT_DELTA - self.WEIGHT_DELTA
        # while True:
        #     weight = (
        #         random.random() * self.DOUBLE_WEIGHT_DELTA - self.WEIGHT_DELTA
        #     )
        #     if weight:
        #         break
        # return weight

    def initial_weights(self, input_size):
        weights = []
        # +1 for bias input
        for i in range(input_size + 1):
            weight = self.generate_weight()
            weights.append(weight)
        return weights

    def calculate(self, input_data):
        # assert self.weights
        z = 0
        for i, value in enumerate(input_data):
            z += value * self.weights[i]
        z += self.BIAS_INPUT * self.weights[-1]
        return self.sigmoid(z)

    def sigmoid(self, z):
        return 1.0 / (1.0 + math.exp(-z))

    def update_weight(self, i, x, d, y):
        """
        i = index
        x = input value
        d = desired output
        y = output
        """
        # TODO: faster if L_R * (d-y) * y * (1.0 - y) would be stored
        self.weights[i] += self.LEARNING_RATE * x * (d - y) * y * (1.0 - y)

    def update_weights(self, input_data, desired_output):
        y = self.calculate(input_data)
        for i, x in enumerate(input_data):
            self.update_weight(i, x, desired_output, y)
        self.update_weight(-1, self.BIAS_INPUT, desired_output, y)


class MLMCPerceptron(object):
    """Multi-layer multi-class perceptron."""

    WEIGHT_DELTA = 0.01
    DOUBLE_WEIGHT_DELTA = 2 * WEIGHT_DELTA
    BIAS_INPUT = -1
    LEARNING_RATE = 0.2

    def __init__(self, sizes):
        assert len(sizes) > 1
        self.sizes = sizes
        self.init_weights(sizes)

    def generate_weight(self):
        return 0.5
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
        self.weights = []
        for i, previous_layer_size in enumerate(sizes[:-2]):
            self.weights.append(
                self.generate_layer_weights(previous_layer_size, sizes[i + 1])
            )
        self.output_layer_weights = self.generate_layer_weights(
            sizes[-2],
            sizes[-1]
        )

    def sigmoid(self, z):
        return 1.0 / (1.0 + math.exp(-z))

    def calculate_single(self, input_data, weights):
        # assert self.weights
        z = 0
        for i, value in enumerate(input_data):
            z += value * weights[i]
        z += self.BIAS_INPUT * weights[-1]
        return self.sigmoid(z)

    def calculate_layer(self, input_data, layer_weights):
        output_vector = []
        for j, weights in enumerate(layer_weights):
            output_vector.append(
                self.calculate_single(input_data, weights)
            )
        return output_vector

    def calculate(self, input_data):
        data = input_data
        for layer_weights in self.weights:
            data = self.calculate_layer(data, layer_weights)
        data = self.calculate_layer(data, self.output_layer_weights)
        return data

    def output_delta_and_weights(self, data, weights, d):
        """
        x = input value
        d = desired output
        y = output
        """
        ws = []
        y = self.calculate_single(data, weights)
        delta = (d - y) * y * (1.0 - y)
        h = self.LEARNING_RATE * delta
        for i, x in enumerate(data):
            w = weights[i]
            ws.append(w + x * h)
        ws.append(weights[-1] + self.BIAS_INPUT * h)
        return delta, ws

    def output_deltas_and_weights(self, data, desired_output_data):
        new_weights = []
        deltas = []
        output_vector = self.calculate_layer(data, self.output_layer_weights)
        for i, weights in enumerate(self.output_layer_weights):
            d = desired_output_data[i]
            delta, weights = self.output_delta_and_weights(data, weights, d)
            new_weights.append(weights)
            deltas.append(delta)
        return deltas, new_weights

    def input_hidden_delta(self, output, outgoing_weights, outgoing_deltas):
        return output * (1 - output) * sum([
            outgoing_weights[i] * outgoing_deltas[i]
            for i in range(len(outgoing_weights))
        ])

    def input_hidden_weights(self, h, weights, inputs):
        new_weights = []
        for i, value in enumerate(inputs):
            new_weights.append(weights[i] + h * value)
        new_weights.append(weights[-1] + h * self.BIAS_INPUT)
        return new_weights

    def input_hidden_layer(self, inputs, outputs, next_layer_weights,
                           next_layer_deltas, layer_weights):
        new_weights = []
        deltas = []
        for i, weights in enumerate(layer_weights):
            delta = self.input_hidden_delta(
                outputs[i],
                [w[i] for w in next_layer_weights],
                next_layer_deltas
            )
            h = self.LEARNING_RATE * delta
            deltas.append(delta)
            new_weights.append(self.input_hidden_weights(h, weights, outputs))
        return deltas, new_weights

    def update_weights(self, input_data, desired_output_data):
        results = [input_data]
        for layer_weights in self.weights:
            results.append(self.calculate_layer(results[-1], layer_weights))

        deltas, weights = self.output_deltas_and_weights(
            results[-1],
            desired_output_data
        )
        self.output_layer_weights = weights

        new_weights = []
        weights_length = len(self.weights)
        for i in range(1, weights_length + 1):
            deltas, weights = self.input_hidden_layer(
                results[-i-1],
                results[-i],
                weights,
                deltas,
                self.weights[-i],
            )
            new_weights.append(weights)
        self.weights = new_weights
