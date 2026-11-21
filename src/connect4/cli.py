"""Terminal play.  Run from the repo root:  PYTHONPATH=src python -m connect4"""
import sys
import time
from pathlib import Path

from .board import AI, COLS, EMPTY, HUMAN, drop, is_win, new_board, valid_moves
from .search import Stats, best_move


SYMBOL = {EMPTY: ".", HUMAN: "X", AI: "O"}


def show(board):
    print()
    for row in board:
        print(" | " + " ".join(SYMBOL[v] for v in row) + " |")
    print("   " + " ".join(str(c + 1) for c in range(COLS)))


def play():
    levels = {"1": ("Easy", 2), "2": ("Medium", 4), "3": ("Hard", 6)}
    lvl = input("Difficulty  1) Easy  2) Medium  3) Hard : ").strip() or "2"
    name, depth = levels.get(lvl, levels["2"])
    print(f"\n{name} mode  (alpha-beta search depth {depth}).  You are X.")
    board, turn = new_board(), HUMAN
    while True:
        show(board)
        if turn == HUMAN:
            try:
                col = int(input("Your column (1-7): ")) - 1
            except ValueError:
                continue
            if col not in valid_moves(board):
                print("Invalid column.")
                continue
            board = drop(board, col, HUMAN)
        else:
            t = time.perf_counter()
            col = best_move(board, depth)
            print(f"AI plays column {col + 1}  "
                  f"({Stats.nodes} nodes searched in {time.perf_counter() - t:.2f}s)")
            board = drop(board, col, AI)
        if is_win(board, turn):
            show(board)
            print("You win!" if turn == HUMAN else "AI wins!")
            return
        if not valid_moves(board):
            show(board)
            print("Draw.")
            return
        turn = AI if turn == HUMAN else HUMAN



def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "benchmark":
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments"))
        import benchmark
        benchmark.main()
    else:
        play()


if __name__ == "__main__":
    main()
