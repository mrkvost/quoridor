import math
import random


class Perceptron(object):
    WEIGHT_DELTA = 0.01
    DOUBLE_WEIGHT_DELTA = 2 * WEIGHT_DELTA
    BIAS_INPUT = -1
    LEARNING_RATE = 0.2

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
