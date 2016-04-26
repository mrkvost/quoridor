import numpy

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from quoridor.commonsettings import DB_PATH
from quoridor.db.models import Base, Network, Weight, Game, Move


def make_db_session(db_path):
    engine = create_engine(
        'sqlite:///{relative_db_path}'.format(relative_db_path=db_path)
    )
    Session = sessionmaker(bind=engine)
    return Session()
    # with closing(make_db_session(db_path)) as db_session:
    # connection = engine.raw_connection()
    # return connection


def db_update_network(db_session, name, perceptron):
    network = db_session.query(Network).filter_by(name=name).one()
    network.alpha = perceptron.alpha
    network.momentum = perceptron.momentum
    network.out_sigmoided = perceptron.out_sigmoided

    weights = db_session.query(Weight).filter_by(network_id=network.id)
    for weight in weights:
        weight.weight = (
            perceptron.weights[weight.layer][weight.output][weight.input]
        )
    db_session.commit()


def db_save_network(db_session, perceptron, name):
    query = db_session.query(Network).filter_by(name=name)
    assert query.count() == 0, 'Network name already present in the db.'

    network = Network(
        name=name,
        alpha=perceptron.alpha,
        momentum=perceptron.momentum,
        out_sigmoided=perceptron.out_sigmoided,
        exploration_probability=perceptron.exploration_probability,
    )
    db_session.add(network)
    db_session.commit()

    for i, layer_weights in enumerate(perceptron.weights):
        for j, neuron_weights in enumerate(layer_weights):
            for k, weight in enumerate(neuron_weights):
                new_weight = Weight(
                    network_id=network.id,
                    layer=i,
                    input=k,
                    output=j,
                    weight=weight,
                )
                db_session.add(new_weight)
    db_session.commit()


def db_load_network(db_session, network_name):
    storage = {}
    maximums = {}
    network = db_session.query(Network).filter_by(name=network_name).one()
    assert network.weights
    for weight in network.weights:
        storage[(weight.layer, weight.output, weight.input)] = weight.weight
        if (weight.layer not in maximums) or (
                maximums[weight.layer] < weight.input):
            maximums[weight.layer] = weight.input
        if (weight.layer + 1 not in maximums) or (
                maximums[weight.layer + 1] < weight.output + 1):
            maximums[weight.layer + 1] = weight.output + 1

    weights = []
    for i in range(1, len(maximums)):
        weights.append(numpy.array([
            [storage[(i - 1, j, k)] for k in range(maximums[i - 1] + 1)]
            for j in range(maximums[i])
        ]))

    network_attribues = dict(
        alpha=network.alpha,
        out_sigmoided=network.out_sigmoided,
        momentum=network.momentum,
        weights=weights,
        exploration_probability=network.exploration_probability,
    )
    return network_attribues


# LIST_TABLES = """ SELECT name FROM sqlite_master WHERE type='table'"""
def build_db(db_path):
    engine = create_engine(
        'sqlite:///{relative_db_path}'.format(relative_db_path=db_path)
    )
    Base.metadata.create_all(engine)


def run():
    build_db(DB_PATH)
