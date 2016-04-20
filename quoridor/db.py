import numpy

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, ForeignKey, MetaData,
    Boolean,
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Network(Base):
    __tablename__ = 'network'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    alpha = Column(Float, nullable=False)
    momentum = Column(Float, nullable=False)
    out_sigmoided = Column(Boolean, nullable=False)
    games_played = Column(Integer, default=0, nullable=False)

    def __str__(self):
        name = self.name
        if len(name) > 7:
            name = name[:4] + '...'

        return (
            u'N({id}, {name!r}, {alpha}, {momentum}, {layers!r})'
        ).format(
            id=self.id,
            name=name,
            alpha=self.alpha,
            momentum=self.momentum,
            layers=[],
        )


class Weight(Base):
    __tablename__ = 'weight'

    id = Column(Integer, primary_key=True)
    network_id = Column(Integer, ForeignKey('network.id'))
    layer = Column(Integer, nullable=False)
    input = Column(Integer, nullable=False)
    output = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    network = relationship("Network", backref="weights")

    def __str__(self):
        return (
            u'W(n={nid}, {layer}, {input}, {output}, {weight:5.3f})'
        ).format(
            nid=self.network_id,
            layer=self.layer,
            input=self.input,
            output=self.output,
            weight=self.weight,
        )


class Game(Base):
    __tablename__ = 'game'

    id = Column(Integer, primary_key=True)
    yellow_played = Column(String)
    green_played = Column(String)
    description = Column(String)


class Move(Base):
    __tablename__ = 'move'

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), nullable=False)
    number = Column(Integer, nullable=False)
    action = Column(Integer, nullable=False)


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
    )
    return network_attribues


# LIST_TABLES = """ SELECT name FROM sqlite_master WHERE type='table'"""
def build_db(db_path):
    engine = create_engine(
        'sqlite:///{relative_db_path}'.format(relative_db_path=db_path)
    )
    Base.metadata.create_all(engine)


def run():
    build_db('data.db')
