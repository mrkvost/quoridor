import random

from core.game import YELLOW, GREEN, Quoridor2, InvalidMove
from core.context import QuoridorContext
from ai.players import HeuristicPlayer, QlearningNetworkPlayer


def run():
    game = Quoridor2()
    context = QuoridorContext(game)
    players = {
        YELLOW: {'name': 'qlnn', 'player': QlearningNetworkPlayer(game)},
        GREEN: {'name': 'heuristic', 'player': HeuristicPlayer(game)},
    }
    context.reset(players=players)
    print context
    while not context.is_terminal:
        if context.state[0] == YELLOW:
            actions = tuple(game.all_actions)
            for action in random.sample(actions, len(actions)):
                try:
                    context.update(action)
                    break
                except InvalidMove:
                    continue
        else:
            players[GREEN]['player'](context)
        print context
