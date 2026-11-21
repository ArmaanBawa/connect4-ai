# Algorithms

How the Connect-4 AI works, with pointers to the code. The Python implementation is in `src/connect4/`; the browser version in `web/js/engine.js` follows the same design.

## 1. State-space formulation (Unit 1)

Connect-4 is modelled as a deterministic, two-player, zero-sum game with perfect information.

| Element | Definition | Code |
|---|---|---|
| State | 6 × 7 grid, each cell empty, human or AI | `board.py`: `new_board` |
| Initial state | the empty board, human to move | `new_board()` |
| Actions | the columns whose top cell is empty (at most 7) | `valid_moves` |
| Transition | the disc falls to the lowest empty cell of the column (gravity); the result is a **new** board | `drop` |
| Terminal test | four in a row (horizontal, vertical or either diagonal) or a full board | `is_win`, `is_terminal` |
| Utility | win for the AI `+10,000,000 + depth`, loss `-10,000,000 - depth`, draw `0`; the depth term makes the AI prefer quicker wins and slower losses | `search.py`: `terminal_value` |

The full game tree is far too large to search (the web page quotes about 4.5 trillion reachable positions), so every search is **depth-limited** and uses a heuristic at the horizon.

## 2. Minimax (Unit 4)

`search.minimax(board, depth, maximising)` explores every column to the depth limit. The AI is the MAX player and picks the child with the highest value; the opponent is MIN and is assumed to pick the child with the lowest value. At depth 0, or at a terminal position, the value comes from `terminal_value` or the heuristic. Cost is O(b^d) nodes for branching factor b (up to 7) and depth d.

## 3. Alpha-beta pruning

`search.alphabeta` returns the same value as minimax but carries two bounds: **alpha**, the best value MAX is already guaranteed, and **beta**, the best value MIN is already guaranteed. When `alpha >= beta` the rest of that node's children cannot affect the result and are skipped. Pruning never changes the root value, only the number of nodes (Knuth & Moore, 1975). The tests check both facts: all variants return the same best score, and alpha-beta searches fewer nodes.

## 4. Move ordering

Alpha-beta prunes most when the best move is tried first. With `ordered=True` the columns are tried centre-first (`CENTRE_ORDER = [3, 2, 4, 1, 5, 0, 6]`), because central discs take part in more fours. If a `first` move is given (the best move of the previous iteration), it is searched before everything else at the root.

## 5. Iterative deepening

`search.iterative_deepening(board, time_limit)` searches depth 1, 2, 3, ... with ordered alpha-beta and keeps the result of the deepest **completed** search. The best move of each depth is searched first at the next depth. The Python version skips a depth if the time already used plus four times the last iteration's time would exceed the limit (each extra ply costs roughly a factor of 4 here); it also stops as soon as a forced win or loss is found. The web version instead aborts a running search when the deadline passes and discards that unfinished depth. This is the Expert level (1 second).

## 6. Heuristic evaluation

At the depth limit `heuristic.evaluate(board, player)` adds the centre-column bonus and scores every window of four cells (69 windows: 24 horizontal, 21 vertical, 24 diagonal). `score_window` gives:

| Pattern in a window of four | Deadline 1 weights | Tuned weights |
|---|---:|---:|
| 4 own discs | +100 | +100 |
| 3 own discs + 1 empty | +5 | **+7** |
| 2 own discs + 2 empty | +2 | +2 |
| 3 opponent discs + 1 empty | -4 | -4 |
| Own disc in the centre column (per disc) | +3 | +3 |

`DEFAULT_WEIGHTS` holds the Deadline 1 values and `TUNED_WEIGHTS` the tuned ones; the module-level `WEIGHTS` (a copy of the tuned set) is the one in use.

## 7. Weight tuning by hill climbing (Unit 2)

`experiments/tune.py` treats a weight vector as a **state** in a local search:

- **Neighbours:** change one of `three`, `two`, `opp_three`, `centre` by one step (2, 1, 2, 1), keeping the weights in a valid range.
- **Objective:** the score of a candidate in a self-play match against the current best (win = 1, draw = 0.5), 24 games at depth 3, colours alternating, the same openings for every candidate.
- **Move:** take the best neighbour if it scores above 55%; otherwise stop at a local maximum.
- **Validation:** tuned vs original weights, 40 games at depth 4.

The run in `results/tuning_results.json` accepted one step (open three 5 → 7, 58.3%), rejected the next (7 → 9, 54.2%) and scored 52.5% in validation. The improvement is small and the result is a local maximum, not a proven optimum. See the README for the table.

## 8. Syllabus mapping (ITITC503)

| Unit | Topic | Where it appears |
|---|---|---|
| Unit 1 | State-space search: problem formulation | Section 1; `board.py` |
| Unit 2 | Local search: hill climbing | Section 7; `experiments/tune.py` |
| Unit 4 | Game playing: minimax, alpha-beta cut-offs, evaluation functions | Sections 2 to 6; `search.py`, `heuristic.py` |

## References

- Russell & Norvig, *Artificial Intelligence: A Modern Approach*, 4th ed., 2020 (adversarial search, local search).
- Knuth & Moore, "An analysis of alpha-beta pruning", *Artificial Intelligence* 6(4), 1975.
- Shannon, "Programming a computer for playing chess", *Philosophical Magazine*, 1950.
- Allis, *A Knowledge-based Approach of Connect-Four*, M.Sc. thesis, VU Amsterdam, 1988.
- Rich & Knight, *Artificial Intelligence*, 1991; Pearl, *Heuristics*, 1984.
