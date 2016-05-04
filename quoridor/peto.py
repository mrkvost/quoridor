from time import clock
start = clock()

from core.game import YELLOW, GREEN, Quoridor2
from core.context import QuoridorContext
from ai.players import HeuristicPlayer


OUTPUT_FMT = """\
      YELLOW     GREEN
{yellow:>12} vs. {green}
{yw:>7} wins     {gw} wins

            TOTAL
         games: {game_count}
    avg. moves: {avg_moves:.3f}
  init seconds: {init_seconds:.4f}
  play seconds: {seconds:.4f}

            RATE
  seconds/game: {sg:.4f}
  games/second: {gs:.2f}\
"""


def run():
    game = Quoridor2()
    context = QuoridorContext(game)
    heuristic = HeuristicPlayer(game)
    players = {
        YELLOW: {'name': 'heuristic', 'player': heuristic},
        GREEN: {'name': 'heuristic', 'player': heuristic},
    }
    game_count = 500
    yellow_wins = 0
    green_wins = 0
    avg_moves = 0.0

    play_start = clock()

    for n in xrange(1, game_count + 1):
        context.reset(players=players)
        while not context.is_terminal:
            heuristic.play(context)
        if context.state[0] == YELLOW:
            green_wins += 1
        else:
            yellow_wins += 1
        avg_moves += (len(context.history) - avg_moves) / n

    end = clock()

    play_seconds = end - play_start
    init_seconds = play_start - start
    print OUTPUT_FMT.format(
        yellow=players[YELLOW]['name'],
        green=players[GREEN]['name'],
        game_count=game_count,
        avg_moves=avg_moves,
        init_seconds=init_seconds,
        seconds=play_seconds,
        sg=float(play_seconds) / game_count,
        gs=float(game_count) / play_seconds,
        yw=yellow_wins,
        gw=green_wins,
    )
