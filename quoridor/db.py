import numpy

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, ForeignKey, MetaData,
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


def make_db_session(db_path):
    engine = create_engine(
        'sqlite:///{relative_db_path}'.format(relative_db_path=db_path)
    )
    Session = sessionmaker(bind=engine)
    return Session()
    # with closing(make_db_session(db_path)) as db_session:
    # connection = engine.raw_connection()
    # return connection


def save_weights(db_session, network_name, alpha, momentum, weights):
    new_network = Network(
        name=network_name,
        alpha=alpha,
        momentum=momentum,
    )
    db_session.add(new_network)
    db_session.commit()

    for i in range(len(weights)):
        for j in range(len(weights[i])):
            for k, weight in enumerate(weights[i][j]):
                new_weight = Weight(
                    network_id=new_network.id,
                    layer=i,
                    input=k,
                    output=j,
                    weight=weight,
                )
                db_session.add(new_weight)
    db_session.commit()


def load_weights(db_session, network_name):
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
                maximums[weight.layer + 1] < weight.output):
            maximums[weight.layer + 1] = weight.output

    weights = []
    for i in range(1, len(maximums) - 1):
        weights.append(numpy.array([
            [storage[(i, j, k)] for k in range(maximums[i - 1] + 1)]
            for j in range(maximums[i])
        ]))
    weights.append(numpy.array([
        [storage[(i, j, k)] for k in range(maximums[i] + 1)]
        for j in range(maximums[i + 1] + 1)
    ]))
    return weights


# LIST_TABLES = """ SELECT name FROM sqlite_master WHERE type='table'"""
def build_db(db_path):
    engine = create_engine(
        'sqlite:///{relative_db_path}'.format(relative_db_path=db_path)
    )
    Base.metadata.create_all(engine)
