import numpy

from contextlib import closing

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from quoridor.commonsettings import DB_PATH
from quoridor.db.models import Base, Network, Weight, GameState, Game, Move


GAME_STATE_DEFAULT = (0, 4, 76, 10, 10, tuple())
GAME_STATE_SLUG_DEFAULT = 'default'
GAME_STATE_DESC_DEFAULT = 'Standard starting state for 2 player version in 9x9'


def _make_engine(db_path):
    db_url = 'sqlite:///{relative_db_path}'.format(relative_db_path=db_path)
    engine = create_engine(db_url)
    return engine


def make_db_session(db_path):
    engine = _make_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()
    # with closing(make_db_session(db_path)) as db_session:
    # connection = engine.raw_connection()
    # return connection


def db_update_network(db_session, perceptron, name):
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
                network.weights.append(new_weight)
    return network


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


def db_save_game_state(db_session, state, slug=None, description=None):
    game_state = GameState()
    game_state.on_move = state[0]
    game_state.yellow_position = state[1]
    game_state.yellow_walls = state[3]
    game_state.green_position = state[2]
    game_state.green_walls = state[4]
    game_state.placed_walls = ','.join([
        str(wall) for wall in sorted(state[5])
    ])

    game_state.slug = slug
    game_state.description = description

    db_session.add(game_state)
    return game_state


def db_save_game(db_session, state_slug=None, start_state=None, yellow=None,
                 green=None, winner=None, actions=None, moves_made=None,
                 description=None, is_training=False):
    game_state = None
    if state_slug:
        query = db_session.query(GameState).filter_by(slug=state_slug)
        game_state = query.one()   # slug provided, game state has to exist!
    elif start_state:
        query = db_session.query(GameState).filter_by(
            on_move=start_state[0],
            yellow_position=start_state[1],
            yellow_walls=start_state[3],
            green_position=start_state[2],
            green_walls=start_state[4],
            placed_walls=','.join([
                str(wall) for wall in sorted(start_state[5])
            ]),
        )
        game_state = query.first()
        if game_state is None:
            game_state = db_save_game_state(db_session, start_state)

    if actions:
        moves_made = len(actions)

    game = Game()
    game.yellow_played = yellow
    game.green_played = green
    game.winner = winner
    game.moves_made = moves_made
    game.description = description
    game.is_training = is_training

    if game_state is not None:
        if actions:
            moves_made = len(actions)
            for number, action in enumerate(actions, start=1):
                move = Move()
                move.number = number
                move.action = action
                move.game_id = game.id
                game.moves.append(move)
        game_state.games.append(game)
    else:
        db_session.add(game)


# LIST_TABLES = """ SELECT name FROM sqlite_master WHERE type='table'"""
def build_db(db_path):
    engine = _make_engine(db_path)
    Base.metadata.create_all(engine)

    with closing(make_db_session(DB_PATH)) as db_session:
        query = db_session.query(GameState)
        query = query.filter_by(slug=GAME_STATE_SLUG_DEFAULT)
        default_game_state = query.first()
        if default_game_state is None:
            default_game_state = db_save_game_state(
                db_session,
                GAME_STATE_DEFAULT,
                GAME_STATE_SLUG_DEFAULT,
                GAME_STATE_DESC_DEFAULT,
            )
            db_session.commit()


def run():
    build_db(DB_PATH)
