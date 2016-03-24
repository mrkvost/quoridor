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
def with_db_session(file_path=None):
    def decorator(function):
        @functools.wraps(function)
        @with_path_or_tempfile(file_path=file_path, suffix='.test.db')
        def wrapper(db_file_path, *args, **kwargs):
            with closing(make_db_session(db_file_path)) as db_session:
                setattr(db_session, '__dbfilename__', db_file_path)
                return function(db_session, *args, **kwargs)
        return wrapper
    return decorator


@nottest
def get_all_table_names(db_session):
    return sorted(
        [row[0] for row in db_session.execute(LIST_TABLES_SQL)]
    )


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


@attr('db', 'build_db')
@with_db_session()
def test_build_db(db_session):
    build_db(db_session.__dbfilename__)
    assert_equal(get_all_table_names(db_session), ['network', 'weight'])
    assert_equal(len(db_session.query(Network).all()), 0)
    assert_equal(len(db_session.query(Weight).all()), 0)


@attr('db', 'save')
@with_db_session()
def test_save_network(db_session):
    attributes = {
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

    perceptron = MLMCPerceptron(**attributes)
    build_db(db_session.__dbfilename__)
    db_save_network(db_session, perceptron, name='2_2_1')

    network = db_session.query(Network).filter_by(name='2_2_1').one()
    assert_equal(network.alpha, attributes['alpha'])
    assert_equal(network.momentum, attributes['momentum'])
    assert_equal(network.out_sigmoided, attributes['out_sigmoided'])

    db_weights = db_session.query(Weight)\
        .filter_by(network_id=network.id).all()
    expected_weights_count = sum([l.size for l in attributes['weights']])
    assert_equal(len(db_weights), expected_weights_count)

    for weight in db_weights:
        assert_equal(
            weight.weight,
            attributes['weights'][weight.layer][weight.output][weight.input]
        )


@attr('db', 'load')
@with_db_session('quoridor/tests/data/saved.db')
def test_load_network_1(db_session):
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
