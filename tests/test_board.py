import pytest

from connect4 import (AI, COLS, EMPTY, HUMAN, ROWS, drop, is_terminal, is_win,
                      new_board, valid_moves)


def board_with(cells, piece):
    b = new_board()
    for r, c in cells:
        b[r][c] = piece
    return b


def test_new_board_is_empty():
    b = new_board()
    assert len(b) == ROWS and all(len(row) == COLS for row in b)
    assert all(v == EMPTY for row in b for v in row)
    assert valid_moves(b) == list(range(COLS))


def test_gravity_stacks_from_the_bottom():
    b = drop(new_board(), 3, HUMAN)
    assert b[ROWS - 1][3] == HUMAN
    b = drop(b, 3, AI)
    assert b[ROWS - 2][3] == AI
    assert b[0][3] == EMPTY


def test_drop_does_not_mutate_the_original():
    b = new_board()
    drop(b, 0, HUMAN)
    assert all(v == EMPTY for row in b for v in row)


def test_full_column_is_rejected_and_not_a_valid_move():
    b = new_board()
    for i in range(ROWS):
        b = drop(b, 2, HUMAN if i % 2 == 0 else AI)
    assert 2 not in valid_moves(b)
    with pytest.raises(ValueError):
        drop(b, 2, HUMAN)


def test_horizontal_win():
    assert is_win(board_with([(5, c) for c in range(2, 6)], HUMAN), HUMAN)


def test_vertical_win():
    assert is_win(board_with([(r, 4) for r in range(2, 6)], AI), AI)


def test_diagonal_down_right_win():
    assert is_win(board_with([(r, r) for r in range(0, 4)], HUMAN), HUMAN)


def test_diagonal_up_right_win():
    assert is_win(board_with([(5 - i, i) for i in range(4)], AI), AI)


def test_three_in_a_row_is_not_a_win():
    assert not is_win(board_with([(5, c) for c in range(3)], HUMAN), HUMAN)


def test_win_is_player_specific():
    b = board_with([(5, c) for c in range(4)], HUMAN)
    assert is_win(b, HUMAN) and not is_win(b, AI)


def test_full_board_is_terminal_draw():
    # column pattern chosen so that no four in a row exists anywhere
    pattern = ["XXOOXXO", "OOXXOOX", "XXOOXXO", "OOXXOOX", "XXOOXXO", "OOXXOOX"]
    b = [[HUMAN if ch == "X" else AI for ch in row] for row in pattern]
    assert valid_moves(b) == []
    assert not is_win(b, HUMAN) and not is_win(b, AI)
    assert is_terminal(b)


def test_win_makes_board_terminal():
    assert is_terminal(board_with([(5, c) for c in range(4)], HUMAN))
