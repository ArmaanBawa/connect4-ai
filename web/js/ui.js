{
const {Game, bestMove, iterative, columnScores, WIN, ROWS, COLS, RED, YEL} = C4;
const LEVELS = [
  {id:"easy", name:"Easy", depth:2, hint:"Looks 2 moves ahead."},
  {id:"medium", name:"Medium", depth:4, hint:"Looks 4 moves ahead."},
  {id:"hard", name:"Hard", depth:6, hint:"Looks 6 moves ahead."},
  {id:"expert", name:"Expert", time:1000, hint:"Iterative deepening: searches deeper and deeper for 1 second."},
];
const $ = id => document.getElementById(id);
const st = {level:LEVELS[1], human:RED, weights:"tuned", watching:false, busy:false, over:false, turn:RED,
            last:-1, scores:null, cmpDepth:4, timer:null, starter:"human"};
let g = new Game();
const fmt = n => n.toLocaleString("en-IN");
const fmtScore = v => v == null ? "" : v >= WIN ? "Wins" : v <= -WIN ? "Loses" : (v > 0 ? "+" : "") + v;
const name = p => p === RED ? "Red" : "Yellow";

// ---------- controls
function seg(el, items, current, onPick){
  el.innerHTML = items.map(i => `<button type="button" data-k="${i.k}" aria-pressed="${i.k===current}">${i.t}</button>`).join("");
  el.onclick = e => { const b = e.target.closest("button"); if (!b) return; onPick(b.dataset.k); };
}
function drawControls(){
  seg($("levels"), LEVELS.map(l=>({k:l.id,t:l.name})), st.level.id, k=>{ st.level = LEVELS.find(l=>l.id===k); try{localStorage.setItem("c4level",k)}catch(e){}; drawControls(); });
  $("levelhint").textContent = st.level.hint;
  seg($("starts"), [{k:"human",t:"You"},{k:"ai",t:"AI"}], st.starter, k=>{ st.starter = k; drawControls(); newGame(); });
  seg($("weights"), [{k:"tuned",t:"Tuned"},{k:"default",t:"Deadline 1"}], st.weights, k=>{ st.weights = k; drawControls(); });
  seg($("cmpdepths"), [2,3,4,5,6].map(d=>({k:String(d),t:"Depth "+d})), String(st.cmpDepth), k=>{ st.cmpDepth = +k; drawControls(); });
  $("watch").textContent = st.watching ? "Stop watching" : "Watch AI vs AI";
  $("undo").disabled = st.busy || st.watching || !g.history.length;
  $("cmp").disabled = st.busy || st.over;
}

// ---------- board
function drawBoard(animIdx){
  const winSet = new Set(st.over && st.last >= 0 && g.winAt(st.last) ? g.winLine(st.last) : []);
  let html = "";
  for (let c = 0; c < COLS; c++){
    html += `<button class="col" type="button" data-c="${c}" aria-label="Drop a disc in column ${c+1}">`;
    for (let r = 0; r < ROWS; r++){
      const i = r*COLS + c, v = g.cells[i];
      const cls = v ? `disc ${v===RED?"r":"y"}${winSet.has(i)?" win":""}${i===st.last?" last":""}` : "";
      const fall = i === animIdx ? `style="--f:-${(r+1)*120}%"` : `style="animation:none"`;
      html += `<div class="cell"><div class="hole">${v ? `<div class="${cls}" ${fall}></div>` : ""}</div></div>`;
    }
    html += `</button>`;
  }
  $("board").innerHTML = html;
  $("scores").innerHTML = Array.from({length:COLS}, (_,c) => {
    const v = st.scores ? st.scores[c] : null;
    if (v == null) return `<div class="sc" aria-hidden="true">&nbsp;</div>`;
    const best = Math.max(...st.scores.filter(x=>x!=null));
    const cls = v >= WIN ? "win" : v <= -WIN ? "lose" : v === best ? "best" : "";
    return `<div class="sc ${cls}" title="Column ${c+1}">${fmtScore(v)}</div>`;
  }).join("");
}
function setStatus(){
  const s = $("status");
  let dot = st.turn === RED ? "var(--red)" : "var(--yel)", txt;
  if (st.over === "draw") txt = "Draw: the board is full.";
  else if (st.over) { dot = st.over === RED ? "var(--red)" : "var(--yel)";
    txt = st.watching ? `${name(st.over)} wins.` : st.over === st.human ? "You win! Well played." : "The AI wins."; }
  else if (st.busy) txt = st.watching ? `${name(st.turn)} AI is thinking…` : "AI is thinking…";
  else if (st.watching) txt = `${name(st.turn)} to move`;
  else txt = st.turn === st.human ? "Your move: click a column (or press 1–7)" : "AI to move";
  s.innerHTML = `<span class="dot" style="background:${dot}"></span><span>${txt}</span>`;
}
function render(animIdx){ drawBoard(animIdx); setStatus(); drawControls(); }

// ---------- game flow
function place(c){
  const p = st.turn, i = g.play(c, p);
  st.last = i;
  if (g.winAt(i)) st.over = p; else if (g.full()) st.over = "draw"; else st.turn = 3 - p;
  return i;
}
function humanMove(c){
  if (st.busy || st.over || st.watching || st.turn !== st.human || !g.canPlay(c)) return;
  st.scores = null;
  const i = place(c); render(i);
  if (!st.over) setTimeout(aiMove, 420);
}
function think(me){
  const L = st.level;
  return L.time ? iterative(g, me, L.time, st.weights) : bestMove(g, me, L.depth, "ordered", st.weights);
}
function aiMove(){
  if (st.over) return;
  st.busy = true; setStatus(); drawControls();
  setTimeout(() => {
    const me = st.turn, r = think(me);
    st.scores = columnScores(g, me, Math.min(r.depth, 7), st.weights);
    $("s-col").textContent = r.col + 1;
    $("s-depth").textContent = r.depth;
    $("s-nodes").textContent = fmt(r.nodes);
    $("s-ms").textContent = r.ms < 10 ? r.ms.toFixed(1) + " ms" : Math.round(r.ms) + " ms";
    $("s-log").textContent = r.log ? "Depths finished: " + r.log.map(x => `${x.depth} (${fmt(x.nodes)})`).join(" → ") : `${name(me)} searched a fixed depth of ${r.depth} with alpha-beta and centre-first ordering.`;
    st.busy = false;
    const i = place(r.col); render(i);
    if (st.watching && !st.over) st.timer = setTimeout(aiMove, 650);
  }, 40);
}
function newGame(){
  clearTimeout(st.timer);
  g = new Game(); st.over = false; st.busy = false; st.turn = RED; st.last = -1; st.scores = null;
  st.human = st.starter === "human" ? RED : YEL;
  ["s-col","s-depth","s-nodes","s-ms"].forEach(id => $(id).textContent = "–"); $("s-log").textContent = "";
  $("cmpout").innerHTML = "";
  render();
  if (st.watching || st.turn !== st.human) st.timer = setTimeout(aiMove, 500);
}
function undo(){
  if (st.busy || st.watching || !g.history.length) return;
  do { g.undo(); } while (g.history.length && (g.history.length % 2 === 0) !== (st.human === RED));
  st.over = false; st.scores = null; st.turn = g.history.length % 2 === 0 ? RED : YEL;
  st.last = g.history.length ? (ROWS - g.height[g.history.at(-1)]) * COLS + g.history.at(-1) : -1;
  render();
  if (st.turn !== st.human) st.timer = setTimeout(aiMove, 400);
}

// ---------- comparison tool
function compare(){
  if (st.busy || st.over) return;
  const d = st.cmpDepth, me = st.turn;
  $("cmpout").innerHTML = `<p class="hint">Searching…</p>`;
  setTimeout(() => {
    const rows = [["Minimax","minimax","mm"],["Alpha-Beta","alphabeta","ab"],["Alpha-Beta + ordering","ordered",""]]
      .map(([label, mode, cls]) => ({label, cls, ...bestMove(g, me, d, mode, st.weights)}));
    const max = rows[0].nodes;
    const same = rows.every(r => r.val === rows[0].val);
    $("cmpout").innerHTML = `<table><tr><th>Algorithm</th><th class="n">Positions</th><th class="n">Time</th><th>Move</th><th style="width:28%"></th></tr>` +
      rows.map(r => `<tr><td>${r.label}</td><td class="n">${fmt(r.nodes)}</td><td class="n">${r.ms.toFixed(1)} ms</td><td>col ${r.col+1}</td><td><div class="bar ${r.cls}" style="width:${Math.max(1,100*r.nodes/max)}%"></div></td></tr>`).join("") +
      `</table><p class="hint">${name(me)} to move, depth ${d}. Alpha-beta with ordering searched ${Math.round(100 - 100*rows[2].nodes/max)}% fewer positions than minimax${same ? ", and every method found the same best score" : ""}.</p>`;
  }, 30);
}

// ---------- benchmark table (Python results, depth 6)
const BENCH = [["Minimax",125002,"4.16 s","mm"],["Alpha-Beta",10732,"0.31 s","ab"],["Alpha-Beta + ordering",2571,"0.068 s",""]];
$("bench").innerHTML = `<tr><th>Algorithm</th><th class="n">Positions</th><th class="n">Time (Python)</th><th style="width:30%"></th></tr>` +
  BENCH.map(([n,v,t,c]) => `<tr><td>${n}</td><td class="n">${fmt(v)}</td><td class="n">${t}</td><td><div class="bar ${c}" style="width:${100*v/125002}%"></div></td></tr>`).join("");

// ---------- events
$("board").addEventListener("click", e => { const b = e.target.closest(".col"); if (b) humanMove(+b.dataset.c); });
document.addEventListener("keydown", e => { if (e.key >= "1" && e.key <= "7" && !e.target.closest("input")) humanMove(+e.key - 1); });
$("newgame").onclick = () => { st.watching = false; newGame(); };
$("undo").onclick = undo;
$("watch").onclick = () => { st.watching = !st.watching; if (st.watching) newGame(); else { clearTimeout(st.timer); st.busy = false; render(); } };
$("cmp").onclick = compare;
try { const k = localStorage.getItem("c4level"); const L = LEVELS.find(l => l.id === k); if (L) st.level = L; } catch(e) {}
newGame();
}
