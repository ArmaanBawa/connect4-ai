"""Search agents: random, greedy, minimax, alpha-beta, move ordering, iterative deepening."""
import math
import random
import time

from .board import AI, CENTRE_ORDER, HUMAN, drop, is_terminal, is_win, valid_moves
from .heuristic import evaluate


class Stats:
    nodes = 0


def terminal_value(board, depth):
    if is_win(board, AI):
        return 10_000_000 + depth      # prefer faster wins
    if is_win(board, HUMAN):
        return -10_000_000 - depth
    return 0                           # draw


def minimax(board, depth, maximising):
    Stats.nodes += 1
    if depth == 0 or is_terminal(board):
        return (None, terminal_value(board, depth)) if is_terminal(board) \
            else (None, evaluate(board, AI))
    moves = valid_moves(board)
    best_col = moves[0]
    if maximising:
        best = -math.inf
        for c in moves:
            _, v = minimax(drop(board, c, AI), depth - 1, False)
            if v > best:
                best, best_col = v, c
    else:
        best = math.inf
        for c in moves:
            _, v = minimax(drop(board, c, HUMAN), depth - 1, True)
            if v < best:
                best, best_col = v, c
    return best_col, best


def alphabeta(board, depth, alpha, beta, maximising, ordered=False, first=None):
    Stats.nodes += 1
    if depth == 0 or is_terminal(board):
        return (None, terminal_value(board, depth)) if is_terminal(board) \
            else (None, evaluate(board, AI))
    moves = valid_moves(board)
    if ordered:
        moves = [c for c in CENTRE_ORDER if c in moves]
        if first in moves:                     # best move from the previous iteration
            moves.remove(first)
            moves.insert(0, first)
    best_col = moves[0]
    if maximising:
        value = -math.inf
        for c in moves:
            _, v = alphabeta(drop(board, c, AI), depth - 1, alpha, beta, False, ordered)
            if v > value:
                value, best_col = v, c
            alpha = max(alpha, value)
            if alpha >= beta:
                break                  # beta cut-off
    else:
        value = math.inf
        for c in moves:
            _, v = alphabeta(drop(board, c, HUMAN), depth - 1, alpha, beta, True, ordered)
            if v < value:
                value, best_col = v, c
            beta = min(beta, value)
            if alpha >= beta:
                break                  # alpha cut-off
    return best_col, value


def iterative_deepening(board, time_limit=1.0, max_depth=12):
    """Search depth 1, 2, 3 ... until the time budget is used up (Deadline 2).
    Each finished depth gives a complete answer; its best move is searched first
    at the next depth, which makes alpha-beta prune even more."""
    start, best, done, total = time.perf_counter(), None, 0, 0
    last_iter = 0.0
    for depth in range(1, max_depth + 1):
        elapsed = time.perf_counter() - start
        # next depth costs roughly 4x the last one: don't start what can't finish
        if depth > 1 and elapsed + 4 * last_iter > time_limit:
            break
        Stats.nodes = 0
        t = time.perf_counter()
        col, val = alphabeta(board, depth, -math.inf, math.inf, True, ordered=True, first=best)
        last_iter = time.perf_counter() - t
        total += Stats.nodes
        best, done = col, depth
        if abs(val) >= 10_000_000:            # forced win or loss found: stop early
            break
    Stats.nodes = total
    return best, done


def greedy_move(board, piece=AI):
    return max(valid_moves(board), key=lambda c: evaluate(drop(board, c, piece), piece))


def best_move(board, depth, method="alphabeta_ordered"):
    Stats.nodes = 0
    if method == "random":
        return random.choice(valid_moves(board))
    if method == "greedy":
        return greedy_move(board)
    if method == "minimax":
        return minimax(board, depth, True)[0]
    if method == "alphabeta":
        return alphabeta(board, depth, -math.inf, math.inf, True)[0]
    if method == "iterative":                  # here `depth` is a time limit in seconds
        return iterative_deepening(board, time_limit=depth)[0]
    return alphabeta(board, depth, -math.inf, math.inf, True, ordered=True)[0]
