"""Heuristic evaluation function and its weights."""
from .board import AI, COLS, EMPTY, HUMAN, ROWS


# Weights of the evaluation function. DEFAULT_WEIGHTS are the hand-picked values
# from Deadline 1; WEIGHTS can be replaced by the values found by tune.py.
DEFAULT_WEIGHTS = {"four": 100, "three": 5, "two": 2, "opp_three": -4, "centre": 3}
# Found by tune.py (hill climbing over self-play): open three raised from 5 to 7.
TUNED_WEIGHTS = {"four": 100, "three": 7, "two": 2, "opp_three": -4, "centre": 3}
WEIGHTS = dict(TUNED_WEIGHTS)


def score_window(window, p):
    opp = HUMAN if p == AI else AI
    mine, empty, theirs = window.count(p), window.count(EMPTY), window.count(opp)
    if mine == 4:
        return WEIGHTS["four"]
    if mine == 3 and empty == 1:
        return WEIGHTS["three"]
    if mine == 2 and empty == 2:
        return WEIGHTS["two"]
    if theirs == 3 and empty == 1:
        return WEIGHTS["opp_three"]   # block opponent's open three
    return 0


def evaluate(board, p):
    """Static evaluation: centre control + every 4-cell window on the board."""
    score = WEIGHTS["centre"] * [board[r][COLS // 2] for r in range(ROWS)].count(p)
    for r in range(ROWS):
        for c in range(COLS - 3):
            score += score_window([board[r][c + i] for i in range(4)], p)
    for c in range(COLS):
        for r in range(ROWS - 3):
            score += score_window([board[r + i][c] for i in range(4)], p)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            score += score_window([board[r + i][c + i] for i in range(4)], p)
            score += score_window([board[r + 3 - i][c + i] for i in range(4)], p)
    return score
