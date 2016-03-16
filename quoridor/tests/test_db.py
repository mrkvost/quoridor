import tempfile

from contextlib import closing

from nose.tools import assert_equal, assert_true, assert_false, nottest
from nose.plugins.attrib import attr

from quoridor.db import (
    save_weights,
    load_weights,
    build_db,
    make_db_session,
)

from quoridor.ai import MLMCPerceptron


@attr('db', 'build_db')
def test_build_db():
    build_db('a.db')


@attr('db', 'save')
def test_save_weights():
    p = MLMCPerceptron([2, 2, 2])

    with tempfile.NamedTemporaryFile() as db_file:
        build_db(db_file.name)
        with closing(make_db_session(db_file.name)) as db_session:
            save_weights(db_session, '2_2_2', p.learning_rate, p.momentum, p.weights)
            # TODO: assert .. db_session.query(Weight).count() ... etc.

@attr('db', 'load')
def test_load_weights():
    with closing(make_db_session('a.db')) as db_session:
        weights = load_weights(db_session, '2_2_2')
        # TODO: assert .. len(weights) ... etc.
