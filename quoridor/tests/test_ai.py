import random

from nose.tools import assert_equal

from quoridor.ai import Perceptron


def training_data_from_base(base, repeat):
    training_data = []
    for data in base:
        training_data += [data] * repeat
    random.shuffle(training_data)
    return training_data


def assert_learns_logic(training_data, base):
    p = Perceptron(2)
    for input_data, desired_output in training_data:
        p.update_weights(input_data, desired_output)

    print
    for input_data, desired_output in base:
        result = int(round(p.calculate(input_data), 0))
        print 'input={in_!r}, result={result!r}'.format(
            in_=input_data, result=result
        )
        assert_equal(result, desired_output)


def test_single_perceptron_learns_AND():
    REPEAT = 150
    BASE = [
        [[0, 0], 0],
        [[1, 0], 0],
        [[0, 1], 0],
        [[1, 1], 1],
    ]
    training_data = training_data_from_base(BASE, REPEAT)
    assert_learns_logic(training_data, BASE)


def test_single_perceptron_learns_OR():
    REPEAT = 150
    BASE = [
        [[0, 0], 0],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 1],
    ]
    training_data = training_data_from_base(BASE, REPEAT)
    assert_learns_logic(training_data, BASE)


def test_single_perceptron_learns_NAND():
    REPEAT = 150
    BASE = [
        [[0, 0], 1],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 0],
    ]
    training_data = training_data_from_base(BASE, REPEAT)
    assert_learns_logic(training_data, BASE)
