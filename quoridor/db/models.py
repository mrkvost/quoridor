from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, MetaData,
    Boolean, Index, DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


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
    network = relationship('Network', backref='weights')

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


class GameState(Base):
    __tablename__ = 'game_state'
    __table_args__ = (
        Index(
            'game_state_hash_idx',
            'on_move',
            'yellow_position',
            'yellow_walls',
            'green_position',
            'green_walls',
            'placed_walls',
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True)

    on_move = Column(Integer, nullable=False, index=True)
    placed_walls = Column(String, nullable=False)

    yellow_position = Column(Integer, nullable=False)
    yellow_walls = Column(Integer, nullable=False)

    green_position = Column(Integer, nullable=False)
    green_walls = Column(Integer, nullable=False)

    slug = Column(String(50), index=True)
    description = Column(String)


class Game(Base):
    __tablename__ = 'game'

    id = Column(Integer, primary_key=True)

    start_state_id = Column(Integer, ForeignKey('game_state.id'))
    start_state = relationship('GameState', backref='games')

    yellow_played = Column(String, index=True)
    green_played = Column(String, index=True)
    winner = Column(Integer, index=True)

    description = Column(String)
    moves_made = Column(Integer)
    created = Column(DateTime, server_default=func.current_timestamp())


class Move(Base):
    __tablename__ = 'move'

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), nullable=False)
    game = relationship('Game', backref='moves')
    number = Column(Integer, nullable=False)
    action = Column(Integer, nullable=False)
