"""
Deadline 2: tune the heuristic weights by SELF-PLAY using HILL CLIMBING (Unit 2).

State      = a weight vector {three, two, opp_three, centre}
Neighbours = change one weight by +/- one step
Objective  = score of the candidate in a self-play match against the current best
             (win = 1, draw = 0.5), same openings for every candidate
Stop       = no neighbour scores above 55%  (local maximum), or max iterations

Run:  python experiments/tune.py        (from the repo root; takes a few minutes)
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import connect4 as c4  # noqa: E402
from connect4 import AI, HUMAN  # noqa: E402
from connect4 import heuristic  # noqa: E402

DEPTH = 3
GAMES = 24           # per match; colours alternate
STEPS = {"three": 2, "two": 1, "opp_three": 2, "centre": 1}


def flip(b):
    return [[{0: 0, 1: 2, 2: 1}[v] for v in row] for row in b]


def move_with(weights, board, piece):
    heuristic.WEIGHTS = weights
    view = board if piece == AI else flip(board)
    return c4.best_move(view, DEPTH, "alphabeta_ordered")


def play(wa, wb, game_no):
    """One game: A uses weights wa, B uses wb. Returns A's score."""
    rng = random.Random(1000 + game_no // 2)        # both colour orders share an opening
    a_first = game_no % 2 == 0
    piece = {"a": AI if a_first else HUMAN, "b": HUMAN if a_first else AI}
    order = ["a", "b"] if a_first else ["b", "a"]
    board, turn = c4.new_board(), 0
    for _ in range(2):                                # 2 random opening moves
        board = c4.drop(board, rng.choice(c4.valid_moves(board)), piece[order[turn % 2]])
        turn += 1
    while True:
        who = order[turn % 2]
        col = move_with(wa if who == "a" else wb, board, piece[who])
        board = c4.drop(board, col, piece[who])
        if c4.is_win(board, piece[who]):
            return 1.0 if who == "a" else 0.0
        if not c4.valid_moves(board):
            return 0.5
        turn += 1


def match(wa, wb, games=GAMES):
    return sum(play(wa, wb, g) for g in range(games)) / games


def hill_climb(start, max_iter=8):
    best, history = dict(start), []
    for it in range(max_iter):
        improved = False
        neighbours = []
        for k, step in STEPS.items():
            for d in (+step, -step):
                cand = dict(best)
                cand[k] += d
                if k == "opp_three" and cand[k] > -1:
                    continue
                if k != "opp_three" and cand[k] < 0:
                    continue
                neighbours.append(cand)
        scored = [(match(n, best), n) for n in neighbours]
        top_score, top = max(scored, key=lambda x: x[0])
        history.append({"iter": it + 1, "best_neighbour": top, "score_vs_current": top_score})
        print(f"iter {it + 1}: best neighbour {top}  scored {top_score:.0%} vs current")
        if top_score > 0.55:
            best, improved = top, True
        if not improved:
            print("local maximum reached")
            break
    return best, history


if __name__ == "__main__":
    tuned, hist = hill_climb(c4.DEFAULT_WEIGHTS)
    print("tuned weights:", tuned)
    # validate at a deeper search with fresh openings
    DEPTH = 4
    final = match(tuned, c4.DEFAULT_WEIGHTS, games=40)
    print(f"validation, depth 4, 40 games: tuned scores {final:.0%} vs default")
    json.dump({"tuned": tuned, "default": c4.DEFAULT_WEIGHTS, "history": hist,
               "validation_depth4_40_games": final}, open(ROOT / "results" / "tuning_results.json", "w"), indent=1)
