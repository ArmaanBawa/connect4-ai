// Run with:  node --test tests/
const test = require("node:test");
const assert = require("node:assert/strict");
const C4 = require("../web/js/engine.js");

const { Game, bestMove, iterative, ROWS, COLS, RED, YEL, WIN } = C4;

function play(moves) {
  const g = new Game();
  for (const [c, p] of moves) g.play(c, p);
  return g;
}
const idx = (r, c) => r * COLS + c;

test("gravity: discs stack from the bottom", () => {
  const g = new Game();
  assert.equal(g.play(3, RED), idx(ROWS - 1, 3));
  assert.equal(g.play(3, YEL), idx(ROWS - 2, 3));
  assert.equal(g.cells[idx(0, 3)], 0);
});

test("a full column is not playable", () => {
  const g = new Game();
  for (let i = 0; i < ROWS; i++) g.play(2, i % 2 ? YEL : RED);
  assert.equal(g.canPlay(2), false);
  assert.ok(!g.moves().includes(2));
});

test("undo restores the previous state", () => {
  const g = new Game();
  g.play(4, RED);
  g.undo();
  assert.equal(g.count, 0);
  assert.equal(g.cells[idx(ROWS - 1, 4)], 0);
});

test("horizontal win", () => {
  const g = play([[0, RED], [0, YEL], [1, RED], [1, YEL], [2, RED], [2, YEL]]);
  const i = g.play(3, RED);
  assert.ok(g.winAt(i));
});

test("vertical win", () => {
  const g = play([[0, RED], [1, YEL], [0, RED], [1, YEL], [0, RED], [1, YEL]]);
  const i = g.play(0, RED);
  assert.ok(g.winAt(i));
});

test("diagonal win (up-right)", () => {
  const g = play([[0, RED], [1, YEL], [1, RED], [2, YEL], [3, RED], [2, YEL],
                  [2, RED], [3, YEL], [6, RED], [3, YEL]]);
  const i = g.play(3, RED);
  assert.ok(g.winAt(i));
});

test("diagonal win (down-right)", () => {
  const g = play([[3, RED], [2, YEL], [2, RED], [1, YEL], [0, RED], [1, YEL],
                  [1, RED], [0, YEL], [0, RED], [6, YEL]]);
  const i = g.play(0, RED);
  assert.ok(g.winAt(i));
});

test("three in a row is not a win", () => {
  const g = play([[0, RED], [0, YEL], [1, RED], [1, YEL]]);
  const i = g.play(2, RED);
  assert.equal(g.winAt(i), false);
});

test("full board", () => {
  const g = new Game();
  for (let c = 0; c < COLS; c++) for (let r = 0; r < ROWS; r++) g.play(c, (r + c) % 2 ? YEL : RED);
  assert.ok(g.full());
  assert.deepEqual(g.moves(), []);
});

const MODES = ["minimax", "alphabeta", "ordered"];

test("AI takes an immediate win", () => {
  const g = play([[0, YEL], [6, RED], [1, YEL], [6, RED], [2, YEL]]);
  for (const mode of MODES) assert.equal(bestMove(g, YEL, 3, mode).col, 3, mode);
  assert.equal(iterative(g, YEL, 200).col, 3);
});

test("AI blocks an immediate loss", () => {
  const g = play([[0, RED], [6, YEL], [1, RED], [6, YEL], [2, RED]]);
  for (const mode of MODES) assert.equal(bestMove(g, YEL, 3, mode).col, 3, mode);
  assert.equal(iterative(g, YEL, 200).col, 3);
});

const POSITIONS = [
  [[3, RED]],
  [[3, RED], [3, YEL], [2, RED], [4, YEL]],
  [[3, RED], [3, YEL], [2, RED], [4, YEL], [4, RED], [2, YEL], [1, RED], [5, YEL]],
  [[0, RED], [0, YEL], [6, RED], [6, YEL], [3, RED], [3, YEL], [3, RED], [2, YEL]],
];

test("minimax, alpha-beta and ordered alpha-beta return the same best score", () => {
  for (const moves of POSITIONS) {
    for (const depth of [2, 3, 4]) {
      const g = play(moves);
      const me = g.count % 2 === 0 ? RED : YEL;
      const vals = MODES.map(m => bestMove(g, me, depth, m).val);
      assert.equal(new Set(vals).size, 1, `depth ${depth}: ${vals}`);
    }
  }
});

test("alpha-beta searches fewer nodes than minimax", () => {
  const g = play(POSITIONS[2]);
  const me = g.count % 2 === 0 ? RED : YEL;
  const mm = bestMove(g, me, 4, "minimax").nodes;
  const ab = bestMove(g, me, 4, "alphabeta").nodes;
  const ord = bestMove(g, me, 4, "ordered").nodes;
  assert.ok(ab < mm, `${ab} < ${mm}`);
  assert.ok(ord < mm, `${ord} < ${mm}`);
});

test("win scores are recognised", () => {
  const g = play([[0, YEL], [6, RED], [1, YEL], [6, RED], [2, YEL]]);
  assert.ok(bestMove(g, YEL, 2, "ordered").val >= WIN);
});
