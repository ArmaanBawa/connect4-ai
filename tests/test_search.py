import math

import pytest

from connect4 import (AI, HUMAN, Stats, alphabeta, best_move, drop, minimax,
                      new_board)


def play(moves):
    """moves: list of (column, piece)."""
    b = new_board()
    for col, piece in moves:
        b = drop(b, col, piece)
    return b


POSITIONS = {
    "opening": play([(3, HUMAN)]),
    "early": play([(3, HUMAN), (3, AI), (2, HUMAN), (4, AI)]),
    "midgame": play([(3, HUMAN), (3, AI), (2, HUMAN), (4, AI), (4, HUMAN),
                     (2, AI), (1, HUMAN), (5, AI)]),
    "stacked": play([(0, HUMAN), (0, AI), (6, HUMAN), (6, AI), (3, HUMAN),
                     (3, AI), (3, HUMAN), (2, AI)]),
}
METHODS = ["minimax", "alphabeta", "alphabeta_ordered", "iterative"]


@pytest.mark.parametrize("method", METHODS)
def test_ai_takes_an_immediate_win(method):
    # AI has three in the bottom row (cols 0-2); column 3 wins.
    b = play([(0, AI), (6, HUMAN), (1, AI), (6, HUMAN), (2, AI)])
    depth = 0.3 if method == "iterative" else 3
    assert best_move(b, depth, method) == 3


@pytest.mark.parametrize("method", METHODS)
def test_ai_blocks_an_immediate_loss(method):
    # Human threatens four in the bottom row at column 3; AI cannot win first.
    b = play([(0, HUMAN), (6, AI), (1, HUMAN), (6, AI), (2, HUMAN)])
    depth = 0.3 if method == "iterative" else 3
    assert best_move(b, depth, method) == 3


def run_value(kind, board, depth):
    if kind == "minimax":
        return minimax(board, depth, True)[1]
    if kind == "alphabeta":
        return alphabeta(board, depth, -math.inf, math.inf, True)[1]
    return alphabeta(board, depth, -math.inf, math.inf, True, ordered=True)[1]


@pytest.mark.parametrize("name", POSITIONS)
@pytest.mark.parametrize("depth", [2, 3, 4])
def test_all_algorithms_agree_on_best_score(name, depth):
    b = POSITIONS[name]
    values = {k: run_value(k, b, depth) for k in ("minimax", "alphabeta", "ordered")}
    assert len(set(values.values())) == 1, values


def test_alphabeta_searches_fewer_nodes_than_minimax():
    b = POSITIONS["midgame"]
    Stats.nodes = 0
    minimax(b, 4, True)
    mm_nodes = Stats.nodes
    Stats.nodes = 0
    alphabeta(b, 4, -math.inf, math.inf, True)
    ab_nodes = Stats.nodes
    Stats.nodes = 0
    alphabeta(b, 4, -math.inf, math.inf, True, ordered=True)
    ordered_nodes = Stats.nodes
    assert ab_nodes < mm_nodes
    assert ordered_nodes < mm_nodes
