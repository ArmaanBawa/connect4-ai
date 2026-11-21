"""Board representation, legal moves, gravity and win detection."""

ROWS, COLS = 6, 7
EMPTY, HUMAN, AI = 0, 1, 2
WIN_LEN = 4
CENTRE_ORDER = [3, 2, 4, 1, 5, 0, 6]   # columns sorted centre-first


def new_board():
    return [[EMPTY] * COLS for _ in range(ROWS)]


def valid_moves(board):
    return [c for c in range(COLS) if board[0][c] == EMPTY]


def drop(board, col, piece):
    """Return a new board with `piece` dropped in `col` (gravity)."""
    nb = [row[:] for row in board]
    for r in range(ROWS - 1, -1, -1):
        if nb[r][col] == EMPTY:
            nb[r][col] = piece
            return nb
    raise ValueError("column full")


def is_win(board, p):
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != p:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                rr, cc = r + 3 * dr, c + 3 * dc
                if 0 <= rr < ROWS and 0 <= cc < COLS and all(
                        board[r + i * dr][c + i * dc] == p for i in range(4)):
                    return True
    return False


def is_terminal(board):
    return is_win(board, HUMAN) or is_win(board, AI) or not valid_moves(board)
