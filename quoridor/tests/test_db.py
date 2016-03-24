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

import time


@nottest
def with_temp_db_and_session(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        with tempfile.NamedTemporaryFile(suffix='.test.db') as db_file:
            with closing(make_db_session(db_file.name)) as db_session:
                return function(db_file, db_session, *args, **kwargs)
    return wrapper


@nottest
def get_all_table_names(db_session):
    return sorted(
        [row[0] for row in db_session.execute(LIST_TABLES_SQL)]
    )


@attr('db', 'build_db')
@with_temp_db_and_session
def test_build_db(db_file, db_session):
    build_db(db_file.name)
    assert_equal(get_all_table_names(db_session), ['network', 'weight'])
    assert_equal(len(db_session.query(Network).all()), 0)
    assert_equal(len(db_session.query(Weight).all()), 0)


@attr('db', 'save')
@with_temp_db_and_session
def test_save_weights(db_file, db_session):
    perceptron = MLMCPerceptron([2, 2, 2])
    build_db(db_file.name)
    db_save_network(db_session, perceptron, name='2_2_2')
    # TODO: assert .. db_session.query(Weight).count() ... etc.


@attr('db', 'load')
def test_load_weights():
    DB_PATH = 'quoridor/tests/data/saved.db'
    with closing(make_db_session(DB_PATH)) as db_session:
        network_attributes = db_load_network(db_session, '2_3_4')
    perceptron = MLMCPerceptron(**network_attributes)

    assert_equal(perceptron.alpha, 0.1)
    assert_equal(perceptron.momentum, 0.8)
    assert_true(perceptron.out_sigmoided)

    assert_equal(len(perceptron.weights), 2)
    expected_weights = [
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
    ]
    for i, layer in enumerate(expected_weights):
        assert_true(numpy.array_equal(perceptron.weights[i], layer))
