import random

from nose.tools import assert_equal
from nose.plugins.attrib import attr

from quoridor.ai import (
    make_weight_fmt,
    print_weights,
    print_layer_weights,
    nice_print_data,
    SimplePerceptron,
    MLMCPerceptron
)


def training_data_from_base(base, repeat):
    training_data = []
    for data in base:
        training_data += [data] * repeat
    random.shuffle(training_data)
    return training_data


def assert_simple_perceptron_learns_logic(training_data, base):
    p = SimplePerceptron(2)
    for input_data, desired_output in training_data:
        p.update_weights(input_data, desired_output)

    print
    for input_data, desired_output in base:
        result = int(round(p.calculate(input_data), 0))
        print 'input={in_!r}, result={result!r}'.format(
            in_=input_data, result=result
        )
        assert_equal(result, desired_output)


@attr('simple')
def test_single_perceptron_learns_AND():
    REPEAT = 150
    BASE = [
        [[0, 0], 0],
        [[1, 0], 0],
        [[0, 1], 0],
        [[1, 1], 1],
    ]
    training_data = training_data_from_base(BASE, REPEAT)
    assert_simple_perceptron_learns_logic(training_data, BASE)


@attr('simple')
def test_single_perceptron_learns_OR():
    REPEAT = 150
    BASE = [
        [[0, 0], 0],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 1],
    ]
    training_data = training_data_from_base(BASE, REPEAT)
    assert_simple_perceptron_learns_logic(training_data, BASE)


@attr('simple')
def test_single_perceptron_learns_NAND():
    REPEAT = 150
    BASE = [
        [[0, 0], 1],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 0],
    ]
    training_data = training_data_from_base(BASE, REPEAT)
    assert_simple_perceptron_learns_logic(training_data, BASE)


def assert_mlmc_perceptron_learns_logic(p, training_data, base):
    ds = []
    for i, (input_data, desired_output) in enumerate(training_data):
        data = p.update_weights(input_data, [desired_output])
        if i > len(training_data) - 5:
            ds.append(data)

    # print
    # for data in ds:
    #     print 'x'*100
    #     nice_print_data(data)

    for input_data, desired_output in base:
        # print p.calculate(input_data)
        result = [int(round(r, 0)) for r in p.calculate(input_data)]
        # result = [r for r in p.calculate(input_data)]
        # print 'input={in_!r}, result={result!r}'.format(
        #     in_=input_data, result=result
        # )
        assert_equal(result, [desired_output])


@attr('mlmc')
def test_MLMCPerceptron():
    p = MLMCPerceptron([1, 2, 2])

    # print '\n'
    # fmt = make_weight_fmt(4)
    # print_weights(p.weights, fmt)
    # print_layer_weights(p.output_layer_weights, fmt)
    # print

    assert_equal(len(p.weights[0]), 2)
    assert_equal(len(p.weights[0][0]), 2)
    assert_equal(len(p.output_layer_weights), 2)
    assert_equal(len(p.output_layer_weights[0]), 3)

    # print
    # print p.calculate([1.0])


@attr('mlmc')
def test_MLMCP_learns_AND():
    REPEAT = 1500
    BASE = [
        [[0, 0], 0],
        [[1, 0], 0],
        [[0, 1], 0],
        [[1, 1], 1],
    ]

    p = MLMCPerceptron([2, 2, 1])
    # print '\n'
    # fmt = make_weight_fmt(10)
    # print_weights(p.weights, fmt)
    # print_layer_weights(p.output_layer_weights, fmt, preceeding='output_layer:')
    # print
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)
    # print '\n'
    # print_weights(p.weights, fmt)
    # print_layer_weights(p.output_layer_weights, fmt, preceeding='output_layer:')
    # print


@attr('mlmc')
def test_MLMCP_learns_NAND():
    REPEAT = 1500
    BASE = [
        [[0, 0], 1],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 0],
    ]

    p = MLMCPerceptron([2, 2, 1])
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)


@attr('mlmc')
def test_MLMCP_learns_OR():
    REPEAT = 1500
    BASE = [
        [[0, 0], 0],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 1],
    ]

    p = MLMCPerceptron([2, 2, 1])
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)


@attr('mlmc', 'now')
def test_MLMCP_learns_XOR():
    REPEAT = 10
    BASE = [
        [[0, 0], 0],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 0],
    ]

    p = MLMCPerceptron([2, 2, 1])
    training_data = training_data_from_base(BASE, REPEAT)
    assert_mlmc_perceptron_learns_logic(p, training_data, BASE)


@attr('mlmc', 'now')
def test_MLMCP_learns_whatewer():
    BASE = [
        [[0, 0], 0],
        [[1, 0], 1],
        [[0, 1], 1],
        [[1, 1], 0],
    ]

    p = MLMCPerceptron([2, 2, 1])
    # print
    # print
    # print '-'*140
    # nice_print_data(p.data)
    i = 1
    p.update_weights(BASE[i][0], [BASE[i][1]])
    # print '-'*140
    # nice_print_data(p.data)
    # print '-'*140
    # print
