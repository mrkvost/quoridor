import random
import numpy

from nose.tools import assert_equal, assert_true, assert_false, nottest
from nose.plugins.attrib import attr

from quoridor.ai import (
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
