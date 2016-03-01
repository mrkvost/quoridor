import random


class Perceptron(object):
    WEIGHT_DELTA = 0.001
    DOUBLE_WEIGHT_DELTA = 2 * WEIGHT_DELTA
    BIAS_INPUT = -1

    def __init__(self, input_size, init_weights=True):
        # assert input_size > 0
        self.input_size = input_size
        self.weights = []
        if init_weights:
            self.init_weights()

    def generate_weight(self):
        while True:
            weight = (
                random.random() * self.DOUBLE_WEIGHT_DELTA - self.WEIGHT_DELTA
            )
            if weight:
                break
        return weight

    def init_weights(self):
        # +1 for bias input
        for i in range(self.input_size + 1):
            weight = self.generate_weight()
            self.weights.append(weight)

    def calculate(self, input_data):
        # assert self.weights
        result_value = 0
        for i, value in enumerate(input_data):
            result_value += value * self.weights[i]
        result_value += self.BIAS_INPUT * self.weights[-1]
        return result_value
