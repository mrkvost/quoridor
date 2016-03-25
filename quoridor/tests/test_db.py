import tempfile
import functools
import numpy

from contextlib import closing

from nose.tools import assert_equal, assert_true, assert_false, nottest
from nose.plugins.attrib import attr

from quoridor.db import (
    Network,
    Weight,
    db_save_network,
    db_load_network,
    build_db,
    make_db_session,
)

from quoridor.ai import MLMCPerceptron


LIST_TABLES_SQL = "SELECT name FROM sqlite_master WHERE type='table'"


@nottest
def with_path_or_tempfile(file_path=None, **temfile_kwargs):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            if file_path is None:
                with tempfile.NamedTemporaryFile(**temfile_kwargs) as db_file:
                    return function(db_file.name, *args, **kwargs)
            else:
                return function(file_path, *args, **kwargs)
        return wrapper
    return decorator


@nottest
def with_db_session(file_path=None, with_build_db=False):
    def decorator(function):
        @functools.wraps(function)
        @with_path_or_tempfile(file_path=file_path, suffix='.test.db')
        def wrapper(db_file_path, *args, **kwargs):
            with closing(make_db_session(db_file_path)) as db_session:
                setattr(db_session, '__dbfilename__', db_file_path)
                if with_build_db:
                    build_db(db_session.__dbfilename__)
                return function(db_session, *args, **kwargs)
        return wrapper
    return decorator


@nottest
def get_all_table_names(db_session):
    return sorted(
        [row[0] for row in db_session.execute(LIST_TABLES_SQL)]
    )


@attr('db', 'build_db')
@with_db_session(with_build_db=True)
def test_build_db(db_session):
    assert_equal(get_all_table_names(db_session), ['network', 'weight'])
    assert_equal(len(db_session.query(Network).all()), 0)
    assert_equal(len(db_session.query(Weight).all()), 0)


@nottest
def assert_network_equal(network, expected_attributes):
    assert_equal(network.alpha, expected_attributes['alpha'])
    assert_equal(network.momentum, expected_attributes['momentum'])
    assert_equal(network.out_sigmoided, expected_attributes['out_sigmoided'])

    expected_weights_count = sum([
        layer.size for layer in expected_attributes['weights']
    ])
    assert_equal(len(network.weights), expected_weights_count)

    expected_weights = expected_attributes['weights']
    for weight in network.weights:
        assert_equal(
            weight.weight,
            expected_weights[weight.layer][weight.output][weight.input]
        )


@attr('db', 'save')
@with_db_session(with_build_db=True)
def test_save_network_2_2_1(db_session):
    expected_attributes = {
        'alpha': 0.1,
        'momentum': 0.8,
        'out_sigmoided': True,
        'weights': [
            numpy.array([
                [1, 2, 3],
                [4, 5, 6],
            ]),
            numpy.array([
                [7, 8, 9],
            ]),
        ],
    }

    network_name = '2_2_1'
    perceptron = MLMCPerceptron(**expected_attributes)
    db_save_network(db_session, perceptron, name=network_name)
    network = db_session.query(Network).filter_by(name=network_name).one()
    assert_network_equal(network, expected_attributes)


@attr('db', 'save')
@with_db_session(with_build_db=True)
def test_save_network_5_4_3_2_1(db_session):
    expected_attributes = {
        'alpha': 0.25,
        'momentum': 0.5,
        'out_sigmoided': False,
        'weights': [
            numpy.array([
                [11, 12, 13, 14, 15, 16],
                [17, 18, 19, 20, 21, 22],
                [23, 24, 25, 26, 27, 28],
                [29, 30, 31, 32, 33, 34],
            ]),
            numpy.array([
                [-35, 36, -37, 38, -39],
                [-40, 41, -42, 43, -44],
                [-45, 46, -47, 48, -49],
            ]),
            numpy.array([
                [50.0, -50.1, 50.2, -50.3],
                [50.4, -50.5, 50.6, -50.7],
            ]),
            numpy.array([
                [50.8, 50.9, 51.0],
            ]),
        ],
    }

    network_name = '5_4_3_2_1'
    perceptron = MLMCPerceptron(**expected_attributes)
    db_save_network(db_session, perceptron, name=network_name)
    network = db_session.query(Network).filter_by(name=network_name).one()
    assert_network_equal(network, expected_attributes)


@nottest
def assert_perceptron_equal(perceptron, expected_attributes):
    assert_equal(perceptron.alpha, expected_attributes['alpha'])
    assert_equal(perceptron.momentum, expected_attributes['momentum'])
    assert_equal(
        perceptron.out_sigmoided,
        expected_attributes['out_sigmoided']
    )

    assert_equal(
        len(perceptron.weights),
        len(expected_attributes['weights'])
    )
    for i, layer in enumerate(expected_attributes['weights']):
        assert_true(numpy.array_equal(perceptron.weights[i], layer))


@attr('db', 'load')
@with_db_session('quoridor/tests/data/saved.db')
def test_load_network_2_3_4(db_session):
    network_attributes = db_load_network(db_session, '2_3_4')
    perceptron = MLMCPerceptron(**network_attributes)
    assert_perceptron_equal(
        perceptron,
        {
            'alpha': 0.1,
            'momentum': 0.8,
            'out_sigmoided': True,
            'weights': [
                numpy.array([
                    [0.1, 0.2, 0.3],
                    [0.4, 0.5, 0.6],
                    [0.7, 0.8, 0.9],
                ]),
                numpy.array([
                    [ 0.0, -0.1, -0.2, -0.3],
                    [-0.4, -0.5, -0.6, -0.7],
                    [-0.8, -0.9, -1.0, -1.1],
                    [-1.2, -1.3, -1.4, -1.5],
                ]),
            ],
        }
    )


@attr('db', 'load')
@with_db_session('quoridor/tests/data/saved.db')
def test_load_network_2_4_4_2(db_session):
    network_attributes = db_load_network(db_session, '2_4_4_2')
    perceptron = MLMCPerceptron(**network_attributes)
    assert_perceptron_equal(
        perceptron,
        {
            'alpha': 0.5,
            'momentum': 0.7,
            'out_sigmoided': False,
            'weights': [
                numpy.array([
                    [100.1, -100.2, 100.3],
                    [100.4, -100.5, 100.6],
                    [100.7, -100.8, 100.9],
                    [101.0, -101.1, 101.2],
                ]),
                numpy.array([
                    [-200.0, 200.1, -200.2, 200.3, -200.4],
                    [-200.5, 200.6, -200.7, 200.8, -200.9],
                    [-201.0, 201.1, -201.2, 201.3, -201.4],
                    [-201.5, 201.6, -201.7, 201.8, -201.9],
                ]),
                numpy.array([
                    [300.0, -300.1, 300.2, -300.3, 300.4],
                    [300.5, -300.6, 300.7, -300.8, 300.9],
                ]),
            ],
        }
    )
