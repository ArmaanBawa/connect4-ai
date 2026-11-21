"""Experiments for the report: search cost per algorithm and win-rates between agents."""
import json
import math
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import connect4 as c4  # noqa: E402
from connect4 import AI, HUMAN, Stats  # noqa: E402


def random_position(n_moves, rng):
    b, p = c4.new_board(), HUMAN
    for _ in range(n_moves):
        while True:
            col = rng.choice(c4.valid_moves(b))
            nb = c4.drop(b, col, p)
            if not c4.is_terminal(nb):
                break
        b, p = nb, (AI if p == HUMAN else HUMAN)
    return b


def search_cost(positions, depths, methods):
    out = {}
    for m in methods:
        for d in depths:
            if m == "minimax" and d > 5:
                continue
            nodes, secs = 0, 0.0
            for b in positions:
                t = time.perf_counter()
                c4.best_move(b, d, m)
                secs += time.perf_counter() - t
                nodes += Stats.nodes
            out[f"{m}|{d}"] = {"nodes": nodes / len(positions), "ms": 1000 * secs / len(positions)}
            print(m, d, round(nodes / len(positions)), f"{1000 * secs / len(positions):.0f} ms")
    return out


def flip(b):
    return [[{0: 0, 1: 2, 2: 1}[v] for v in row] for row in b]


def agent_move(board, piece, spec):
    kind, depth = spec
    view = board if piece == AI else flip(board)
    if kind == "random":
        return random.choice(c4.valid_moves(board))
    if kind == "greedy":
        return c4.greedy_move(view, AI)
    return c4.best_move(view, depth, "alphabeta_ordered")


def match(a, b, games):
    res = {"a": 0, "b": 0, "draw": 0}
    for g in range(games):
        board = c4.new_board()
        first_a = g % 2 == 0                      # alternate who starts
        pieces = {"a": AI if first_a else HUMAN, "b": HUMAN if first_a else AI}
        order = ["a", "b"] if first_a else ["b", "a"]
        # 2 random opening moves so games differ
        turn = 0
        for _ in range(2):
            who = order[turn % 2]
            board = c4.drop(board, random.choice(c4.valid_moves(board)), pieces[who])
            turn += 1
        while True:
            who = order[turn % 2]
            spec = a if who == "a" else b
            board = c4.drop(board, agent_move(board, pieces[who], spec), pieces[who])
            if c4.is_win(board, pieces[who]):
                res[who] += 1
                break
            if not c4.valid_moves(board):
                res["draw"] += 1
                break
            turn += 1
    return res


def main():
    random.seed(7)
    rng = random.Random(42)
    positions = [random_position(rng.choice([4, 6, 8]), rng) for _ in range(8)]
    cost = search_cost(positions, [2, 3, 4, 5, 6],
                       ["minimax", "alphabeta", "alphabeta_ordered"])
    matches = {}
    for label, a, b, n in [
        ("AB-d4 vs Random", ("ab", 4), ("random", 0), 20),
        ("AB-d4 vs Greedy", ("ab", 4), ("greedy", 0), 20),
        ("AB-d2 vs Greedy", ("ab", 2), ("greedy", 0), 20),
        ("AB-d5 vs AB-d2", ("ab", 5), ("ab", 2), 20),
    ]:
        matches[label] = match(a, b, n)
        print(label, matches[label])
    with open(ROOT / "results" / "results.json", "w") as f:
        json.dump({"cost": cost, "matches": matches}, f, indent=1)


if __name__ == "__main__":
    main()
