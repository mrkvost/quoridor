import random
import numpy

from nose.tools import assert_equal, assert_true, assert_false, nottest
from nose.plugins.attrib import attr

from quoridor.ai.perceptron import (
    MLMCPerceptron
)


@attr('perceptron', 'weight_sizes')
def test_MLMCPerceptron_sizes():
    for sizes in ([1, 2, 2], [3, 6, 9, 3, 7, 2], [300, 500, 500, 1500, 300]):
        p = MLMCPerceptron(sizes)
        assert_equal(len(p.weights), len(sizes) - 1)
        for i, size in enumerate(sizes):
            if i:
                assert_equal(len(p.weights[i - 1]), size)
                assert_equal(len(p.weights[i - 1][0]), sizes[i - 1] + 1)


@nottest
def training_data_from_base(base, repeat):
    training_data = []
    for data in base:
        training_data += [data] * repeat
    random.shuffle(training_data)
    return training_data


@nottest
def assert_mlmc_perceptron_learns_logic(p, training_data, base):
    for i, (input_data, desired_output) in enumerate(training_data):
        p.learn(input_data, desired_output)

    for input_data, desired_output in base:
        output_vector = [r for r in p.calculate(input_data)]
        result = [int(round(r, 0)) for r in output_vector]
        print 'input={in_!r}, result={result!r}, out={out!r}'.format(
            in_=input_data, result=result, out=output_vector
        )
        assert_equal(result, desired_output)


def tryxept(function, repeat=3, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except:
        if repeat > 0:
            tryxept(function, repeat=repeat - 1, *args, **kwargs)
        else:
            raise


@attr('mlmc', 'xor')
def test_MLMCP_learns_XOR():
    REPEAT = 3500
    BASE = [
        [[0, 0], [0]],
        [[1, 0], [1]],
        [[0, 1], [1]],
        [[1, 1], [0]],
    ]

    def learn_XOR():
        p = MLMCPerceptron([2, 20, 1])
        training_data = training_data_from_base(BASE, REPEAT)
        assert_mlmc_perceptron_learns_logic(p, training_data, BASE)

    tryxept(learn_XOR)


@attr('mlmc', 'nand')
def test_MLMCP_learns_NAND():
    REPEAT = 1500
    BASE = [
        [[0, 0], [1]],
        [[1, 0], [1]],
        [[0, 1], [1]],
        [[1, 1], [0]],
    ]

    p = MLMCPerceptron([2, 2, 1])
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)


@attr('mlmc', 'or')
def test_MLMCP_learns_OR():
    REPEAT = 1500
    BASE = [
        [[0, 0], [0]],
        [[1, 0], [1]],
        [[0, 1], [1]],
        [[1, 1], [1]],
    ]

    p = MLMCPerceptron([2, 2, 1])
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)


@attr('mlmc', 'and')
def test_MLMCP_learns_AND():
    REPEAT = 1500
    BASE = [
        [[0, 0], [0]],
        [[1, 0], [0]],
        [[0, 1], [0]],
        [[1, 1], [1]],
    ]

    p = MLMCPerceptron([2, 2, 1])
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)


def assert_2d_equal(activations, expected_activations):
    assert_equal(len(expected_activations), len(activations))
    for i, expected_vector in enumerate(expected_activations):
        assert_equal(len(expected_vector), len(activations[i]))
        for j, expected_value in enumerate(expected_vector):
            assert_equal(expected_value, activations[i][j])


@attr('mlmc', 'computing')
def test_MLMCP_comptuting_1():
    weights = [
        numpy.array([
            [+0.0, +0.5, -0.5],
            [+0.2, +0.1, +0.0],
        ]),
        numpy.array([
            [+1.0, -0.5, +0.0],
            [+0.3, +0.0, -0.3],
        ]),
    ]

    input_vector = numpy.array([1, 0])
    expected_activations = [
        numpy.array([1.0000000000000000, 0.000000000000000]),
        numpy.array([0.6224593312018546, 0.549833997312478]),
        numpy.array([0.3475423325456156, 0.4867377993605564]),
    ]
    desired_output_vector = numpy.array([100, -100])
    expected_deltas = [
        numpy.array([16.334270558900624, -12.332817392081008]),
        numpy.array([99.6524576674543844, -100.4867377993605564]),
    ]

    p = MLMCPerceptron(
        weights=weights,
        alpha=0.1,
        momentum=0.5,
        out_sigmoided=False,
    )

    activations = list(p.propagate_forward(input_vector))
    assert_2d_equal(activations, expected_activations)

    deltas = p.deltas(desired_output_vector, activations)
    assert_2d_equal(deltas, expected_deltas)

    # TODO: test propagate_backwards
    # p.propagate_backward(activations, desired_output_vector)
    # print 'deltas:', p.delta_weights
