import math
import numpy


BIAS_INPUT = -1
LEARNING_RATE_DEFAULT = 0.1
WEIGHT_RANGE_DEFAULT = 0.5
MOMENTUM_DEFAULT = 0.8


def sigmoid(z):
    """ Sigmoid function.

    >>> sigmoid(1)
    0.7310585786300049
    >>> sigmoid(3)
    0.9525741268224334
    >>> sigmoid(0.1)
    0.52497918747894
    >>> sigmoid(500)
    1.0
    >>> sigmoid(-500)
    0.0
    """

    if z < -50:
        return 0.0
    elif z > 50:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def generate_weights_for_neuron(size, weight_range=WEIGHT_RANGE_DEFAULT):
    """ Creates numpy array of lenght size and contains random numbers between
    -weight_range and +weight_range.

    >>> len(generate_weights_for_neuron(5))
    5
    >>> [
    ...     -0.2 <= weight <= 0.2
    ...     for weight in generate_weights_for_neuron(3, 0.2)
    ... ]
    [True, True, True]
    """

    randoms = numpy.array(numpy.random.random_sample(size))
    return weight_range * (2 * randoms - 1)


def generate_layer_weights(neuron_count, weight_count,
                           weight_range=WEIGHT_RANGE_DEFAULT):
    """ Creates two dimensional numpy array (neuron_count, weight_count) where
    each row contains random numbers between -weight_range and +weight_range.

    >>> len(generate_layer_weights(5, 3))
    5
    >>> len(generate_layer_weights(5, 3)[0])
    3
    >>> [
    ...     [-0.3 <= weight <= 0.3 for weight in weights]
    ...     for weights in generate_layer_weights(3, 2, 0.3)
    ... ]
    [[True, True], [True, True], [True, True]]
    """

    return numpy.array([
        generate_weights_for_neuron(weight_count, weight_range)
        for i in range(neuron_count)
    ])


def generate_weights(sizes, weight_range=WEIGHT_RANGE_DEFAULT):
    """ Creates random weights for neural network. Result is list of 2D numpy
    arrays. Numbers are from range -weight_range to +weight_range.

    >>> len(generate_weights([3, 2, 1]))
    2
    >>> len(generate_weights([3, 2, 1])[0])
    2
    >>> len(generate_weights([3, 2, 1])[0][0])
    4
    >>> [
    ...     [
    ...         [-0.1 <= weight <= 0.1 for weight in weights]
    ...         for weights in layer
    ...     ]
    ...     for layer in generate_weights([2, 2, 1], 0.1)
    ... ]
    [[[True, True, True], [True, True, True]], [[True, True, True]]]
    """

    assert len(sizes) > 1, (
        "At least sizes of input and output layer must be defined."
    )

    return [
        generate_layer_weights(
            sizes[i + 1],
            previous_layer_size + 1,
            weight_range=weight_range,
        )
        for i, previous_layer_size in enumerate(sizes[:-1])
    ]


class MLMCPerceptron(object):
    """Multi-layer multi-class perceptron."""

    def __init__(self, sizes=None, weights=None, momentum=MOMENTUM_DEFAULT,
                 learning_rate=LEARNING_RATE_DEFAULT):
        if sizes is not None:
            assert len(sizes) > 1, (
                "At least sizes of input and output layer should be defined."
            )
            self.weights = generate_weights(sizes)
        else:
            self.weights = weights
        self.delta_weights = [
            numpy.zeros([len(layer), len(layer[0])])
            for layer in self.weights
        ]
        self.learning_rate = learning_rate
        self.momentum = momentum

    def calculate(self, input_vector):
        return list(self.propagate_forward(input_vector))[-1]

    def propagate_forward(self, input_vector):
        """ Generator returning input_vector, activations and output. """

        activations = numpy.array(input_vector)
        yield activations
        for weights in self.weights:
            products = numpy.dot(
                weights,
                numpy.concatenate((activations, [BIAS_INPUT]), axis=0),
             )
            activations = numpy.array([
                sigmoid(product) for product in products
            ])
            yield activations

    def learn(self, input_vector, desired_output_vector):
        activation_vectors = list(self.propagate_forward(input_vector))
        self.propagate_backward(activation_vectors, desired_output_vector)

    def propagate_backward(self, activation_vectors, desired_output_vector):
        deltas = self.deltas(desired_output_vector, activation_vectors)
        for i, layer_weights in enumerate(self.weights):
            for j, weights in enumerate(layer_weights):
                faster = self.learning_rate * deltas[i][j]
                for k, weight in enumerate(weights):
                    input_value = BIAS_INPUT
                    if k + 1 < len(weights):
                        input_value = activation_vectors[i][k]
                    delta_weight = faster * input_value
                    self.weights[i][j][k] += delta_weight + (
                        self.delta_weights[i][j][k] * self.momentum
                    )
                    self.delta_weights[i][j][k] = delta_weight
        # self.last_error = (deltas[-1] ** 2).sum()

    def outgoing_layer_weights(self, layer_index):
        return numpy.array([
            [weights[i] for weights in self.weights[layer_index]]
            for i in range(len(self.weights[layer_index - 1]))
        ])

    def deltas(self, desired_output_vector, activation_vectors):
        output_vector = activation_vectors[-1]
        error = numpy.array(desired_output_vector) - output_vector
        deltas = [error * output_vector * (1.0 - output_vector)]
        for i in range(len(self.weights) - 1, 0, -1):
            activations = activation_vectors[i]
            outgoing_weights = self.outgoing_layer_weights(i)
            products = numpy.dot(outgoing_weights, deltas[-1])
            deltas.append(products * activations * (1.0 - activations))
        return deltas[::-1]
