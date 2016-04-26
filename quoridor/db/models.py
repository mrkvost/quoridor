from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, MetaData,
    Boolean,
)
from sqlalchemy.orm import relationship
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
    exploration_probability = Column(Float, default=0, nullable=False)

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
