/* Connect-4 search engine: minimax, alpha-beta, move ordering, iterative deepening.
   Team AIChampions. Mirrors connect4_ai.py. Works in the browser and in Node. */
(function (root) {
  const ROWS = 6, COLS = 7, EMPTY = 0, RED = 1, YEL = 2;
  const WIN = 10000000;
  const CENTRE_ORDER = [3, 2, 4, 1, 5, 0, 6];
  const WEIGHTS = {
    tuned:   { four: 100, three: 7, two: 2, opp: -4, centre: 3 },
    default: { four: 100, three: 5, two: 2, opp: -4, centre: 3 },
  };

  // all 69 windows of four cells, as board indices (index = row * 7 + col, row 0 = top)
  const WINDOWS = [];
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++)
    for (const [dr, dc] of [[0, 1], [1, 0], [1, 1], [1, -1]]) {
      const er = r + 3 * dr, ec = c + 3 * dc;
      if (er < 0 || er >= ROWS || ec < 0 || ec >= COLS) continue;
      WINDOWS.push([0, 1, 2, 3].map(i => (r + i * dr) * COLS + c + i * dc));
    }

  class Game {
    constructor() { this.reset(); }
    reset() {
      this.cells = new Int8Array(ROWS * COLS);
      this.height = new Int8Array(COLS);
      this.count = 0;
      this.history = [];
    }
    canPlay(c) { return c >= 0 && c < COLS && this.height[c] < ROWS; }
    moves() { const m = []; for (let c = 0; c < COLS; c++) if (this.height[c] < ROWS) m.push(c); return m; }
    play(c, p) {
      const r = ROWS - 1 - this.height[c], i = r * COLS + c;
      this.cells[i] = p; this.height[c]++; this.count++; this.history.push(c);
      return i;
    }
    undo() {
      const c = this.history.pop(); this.height[c]--; this.count--;
      this.cells[(ROWS - 1 - this.height[c]) * COLS + c] = EMPTY;
      return c;
    }
    full() { return this.count === ROWS * COLS; }
    // does the disc at index i complete four in a row?
    winAt(i) {
      const p = this.cells[i], r = (i / COLS) | 0, c = i % COLS;
      for (const [dr, dc] of [[0, 1], [1, 0], [1, 1], [1, -1]]) {
        let n = 1;
        for (const s of [1, -1]) {
          let rr = r + s * dr, cc = c + s * dc;
          while (rr >= 0 && rr < ROWS && cc >= 0 && cc < COLS && this.cells[rr * COLS + cc] === p) { n++; rr += s * dr; cc += s * dc; }
        }
        if (n >= 4) return true;
      }
      return false;
    }
    winLine(i) {
      const p = this.cells[i];
      return WINDOWS.find(w => w.includes(i) && w.every(k => this.cells[k] === p)) || [];
    }
  }

  function evaluate(g, me, w) {
    const opp = 3 - me;
    let s = 0;
    for (let r = 0; r < ROWS; r++) if (g.cells[r * COLS + 3] === me) s += w.centre;
    for (const win of WINDOWS) {
      let m = 0, e = 0, o = 0;
      for (const k of win) { const v = g.cells[k]; if (v === me) m++; else if (v === EMPTY) e++; else o++; }
      if (m === 4) s += w.four;
      else if (m === 3 && e === 1) s += w.three;
      else if (m === 2 && e === 2) s += w.two;
      else if (o === 3 && e === 1) s += w.opp;
    }
    return s;
  }

  const ABORT = { abort: true };

  // One search. mode: "minimax" | "alphabeta" | "ordered"
  function makeSearch(g, me, opts) {
    const w = WEIGHTS[opts.weights || "tuned"];
    const prune = opts.mode !== "minimax", ordered = opts.mode === "ordered";
    const deadline = opts.deadline || 0;
    const st = { nodes: 0 };
    function node(depth, alpha, beta, maxing, last, first) {
      st.nodes++;
      if (deadline && (st.nodes & 1023) === 0 && performance.now() > deadline) throw ABORT;
      if (last >= 0 && g.winAt(last)) return g.cells[last] === me ? WIN + depth : -(WIN + depth);
      if (g.full()) return 0;
      if (depth === 0) return evaluate(g, me, w);
      let list = ordered ? CENTRE_ORDER : [0, 1, 2, 3, 4, 5, 6];
      if (ordered && first != null) list = [first, ...CENTRE_ORDER.filter(c => c !== first)];
      let best = maxing ? -Infinity : Infinity;
      for (const c of list) {
        if (!g.canPlay(c)) continue;
        const i = g.play(c, maxing ? me : 3 - me);
        let v;
        try { v = node(depth - 1, alpha, beta, !maxing, i, null); } finally { g.undo(); }
        if (maxing) { if (v > best) best = v; if (best > alpha) alpha = best; }
        else { if (v < best) best = v; if (best < beta) beta = best; }
        if (prune && alpha >= beta) break;
      }
      return best;
    }
    function root(depth, first) {
      const t0 = performance.now();
      st.nodes = 1;
      let alpha = -Infinity, best = -Infinity, col = null;
      let list = (prune && ordered) ? CENTRE_ORDER : [0, 1, 2, 3, 4, 5, 6];
      if (ordered && first != null) list = [first, ...CENTRE_ORDER.filter(c => c !== first)];
      for (const c of list) {
        if (!g.canPlay(c)) continue;
        const i = g.play(c, me);
        let v;
        try { v = node(depth - 1, prune ? alpha : -Infinity, Infinity, false, i, null); } finally { g.undo(); }
        if (v > best || col === null) { best = v; col = c; }
        if (best > alpha) alpha = best;
      }
      return { col, val: best, nodes: st.nodes, ms: performance.now() - t0, depth };
    }
    return { root, node, st };
  }

  // fixed-depth search
  function bestMove(g, me, depth, mode = "ordered", weights = "tuned") {
    return makeSearch(g, me, { mode, weights }).root(depth, null);
  }

  // iterative deepening: depth 1, 2, 3 ... until the time limit; keeps the last finished depth
  function iterative(g, me, timeMs, weights = "tuned", maxDepth = 20) {
    const t0 = performance.now();
    const s = makeSearch(g, me, { mode: "ordered", weights, deadline: t0 + timeMs });
    let res = null, total = 0;
    const log = [];
    for (let d = 1; d <= Math.min(maxDepth, 42 - g.count); d++) {
      try {
        const r = s.root(d, res ? res.col : null);
        total += r.nodes; res = r; log.push({ depth: d, nodes: r.nodes, ms: r.ms, col: r.col });
        if (Math.abs(r.val) >= WIN) break;     // forced win or loss already found
      } catch (e) {
        if (e !== ABORT) throw e;
        total += s.st.nodes; break;            // unfinished depth: discarded
      }
    }
    return { ...res, nodes: total, ms: performance.now() - t0, log };
  }

  // the AI's score for every column, each searched on its own (for display)
  function columnScores(g, me, depth, weights = "tuned") {
    const s = makeSearch(g, me, { mode: "ordered", weights });
    const out = [];
    for (let c = 0; c < COLS; c++) {
      if (!g.canPlay(c)) { out.push(null); continue; }
      const i = g.play(c, me);
      try { out.push(s.node(Math.max(depth - 1, 0), -Infinity, Infinity, false, i, null)); } finally { g.undo(); }
    }
    return out;
  }

  const api = { Game, bestMove, iterative, columnScores, evaluate, WEIGHTS, WINDOWS, WIN, ROWS, COLS, RED, YEL, EMPTY };
  if (typeof module !== "undefined") module.exports = api; else root.C4 = api;
})(typeof window !== "undefined" ? window : globalThis);
