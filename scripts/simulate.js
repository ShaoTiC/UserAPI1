/**
 * Local self-play harness for js/strategy.js
 * Mirrors the exam rules: simultaneous moves, permanent trails, head-on = double crash.
 */
const chooseMove = require('../js/strategy.js');

const DIRS = ['up', 'right', 'down', 'left'];
const DR = [-1, 0, 1, 0];
const DC = [0, 1, 0, -1];
const ACTION_TURN = { left: -1, straight: 0, right: 1 };
const ACTIONS = ['left', 'straight', 'right'];

function dirIndex(dir) {
  const i = DIRS.indexOf(dir);
  return i < 0 ? 0 : i;
}

function applyAction(player, action) {
  const idx = dirIndex(player.direction);
  const turn = ACTION_TURN[action] || 0;
  const ni = (idx + turn + 4) % 4;
  return {
    row: player.row + DR[ni],
    col: player.col + DC[ni],
    direction: DIRS[ni]
  };
}

function cloneGrid(grid) {
  return grid.map((row) => row.split(''));
}

function gridStrings(cells) {
  return cells.map((row) => row.join(''));
}

function inBounds(r, c, rows, cols) {
  return r >= 0 && c >= 0 && r < rows && c < cols;
}

function isWall(cells, r, c, rows, cols) {
  if (!inBounds(r, c, rows, cols)) return true;
  return cells[r][c] !== '.';
}

function liberty(cells, r, c, rows, cols) {
  let n = 0;
  for (let k = 0; k < 4; k++) {
    if (!isWall(cells, r + DR[k], c + DC[k], rows, cols)) n++;
  }
  return n;
}

function flood(cells, r, c, rows, cols) {
  const seen = new Set();
  const q = [];
  const tryPush = (rr, cc) => {
    if (isWall(cells, rr, cc, rows, cols)) return;
    const key = rr + ',' + cc;
    if (seen.has(key)) return;
    seen.add(key);
    q.push([rr, cc]);
  };
  tryPush(r - 1, c);
  tryPush(r + 1, c);
  tryPush(r, c - 1);
  tryPush(r, c + 1);
  let i = 0;
  while (i < q.length) {
    const [cr, cc] = q[i++];
    tryPush(cr - 1, cc);
    tryPush(cr + 1, cc);
    tryPush(cr, cc - 1);
    tryPush(cr, cc + 1);
  }
  return seen.size;
}

function voronoi(cells, a, b, rows, cols) {
  const n = rows * cols;
  const distA = new Int16Array(n).fill(32767);
  const distB = new Int16Array(n).fill(32767);
  function bfs(sr, sc, dist) {
    const q = [];
    const push = (r, c, d) => {
      if (isWall(cells, r, c, rows, cols)) return;
      const idx = r * cols + c;
      if (d >= dist[idx]) return;
      dist[idx] = d;
      q.push([r, c]);
    };
    push(sr - 1, sc, 1);
    push(sr + 1, sc, 1);
    push(sr, sc - 1, 1);
    push(sr, sc + 1, 1);
    for (let i = 0; i < q.length; i++) {
      const [r, c] = q[i];
      const d = dist[r * cols + c] + 1;
      push(r - 1, c, d);
      push(r + 1, c, d);
      push(r, c - 1, d);
      push(r, c + 1, d);
    }
  }
  bfs(a.row, a.col, distA);
  bfs(b.row, b.col, distB);
  let mine = 0;
  let opp = 0;
  for (let i = 0; i < n; i++) {
    if (distA[i] === 32767 && distB[i] === 32767) continue;
    if (distA[i] < distB[i]) mine++;
    else if (distB[i] < distA[i]) opp++;
    else {
      mine += 0.5;
      opp += 0.5;
    }
  }
  return { mine, opp };
}

function safeMoves(player, cells, rows, cols) {
  const out = [];
  for (const action of ACTIONS) {
    const nxt = applyAction(player, action);
    if (!isWall(cells, nxt.row, nxt.col, rows, cols)) out.push({ action, next: nxt });
  }
  return out;
}

function makeState(turn, cells, you, opponent) {
  const rows = cells.length;
  const cols = cells[0].length;
  return {
    turn,
    rows,
    cols,
    grid: gridStrings(cells),
    you: { row: you.row, col: you.col, direction: you.direction },
    opponent: { row: opponent.row, col: opponent.col, direction: opponent.direction },
    legalActions: ACTIONS.slice(),
    history: []
  };
}

function callBot(fn, state) {
  let action;
  try {
    action = fn(state);
  } catch (e) {
    action = 'straight';
  }
  if (action !== 'left' && action !== 'straight' && action !== 'right') return 'straight';
  return action;
}

function play(youBot, oppBot, scenario, swapSides) {
  const rows = scenario.grid.length;
  const cols = scenario.grid[0].length;
  const cells = cloneGrid(scenario.grid);
  let a = { ...scenario.you };
  let b = { ...scenario.opponent };
  if (swapSides) {
    const tmp = a;
    a = b;
    b = tmp;
  }
  cells[a.row][a.col] = '#';
  cells[b.row][b.col] = '#';
  const maxTurn = rows * cols;
  for (let turn = 1; turn <= maxTurn; turn++) {
    const stateA = makeState(turn, cells, a, b);
    const stateB = makeState(turn, cells, b, a);
    const actA = callBot(youBot, stateA);
    const actB = callBot(oppBot, stateB);
    const nextA = applyAction(a, actA);
    const nextB = applyAction(b, actB);
    const crashA = isWall(cells, nextA.row, nextA.col, rows, cols);
    const crashB = isWall(cells, nextB.row, nextB.col, rows, cols);
    const same = nextA.row === nextB.row && nextA.col === nextB.col;
    if (same && !crashA && !crashB) {
      return { result: 'draw', reason: `head-on t${turn} (${nextA.row},${nextA.col}) a=${actA} b=${actB}` };
    }
    if (crashA && crashB) {
      return { result: 'draw', reason: `both-crash t${turn} a=${actA} ${nextA.row},${nextA.col} b=${actB} ${nextB.row},${nextB.col}` };
    }
    if (crashA) {
      return { result: 'loss', reason: `we-crash t${turn} a=${actA} -> ${nextA.row},${nextA.col} opp=${b.row},${b.col},${b.direction} b=${actB}` };
    }
    if (crashB) {
      return { result: 'win', reason: `opp-crash t${turn}` };
    }
    cells[nextA.row][nextA.col] = '#';
    cells[nextB.row][nextB.col] = '#';
    a = nextA;
    b = nextB;
  }
  return { result: 'draw', reason: 'timeout' };
}

function emptyGrid(rows, cols) {
  return Array.from({ length: rows }, () => '.'.repeat(cols));
}

function withWalls(base, walls) {
  const cells = cloneGrid(base);
  for (const [r, c] of walls) cells[r][c] = '#';
  return gridStrings(cells);
}

function scenarios() {
  const g15 = emptyGrid(15, 15);
  const g12 = emptyGrid(12, 12);
  const g18 = emptyGrid(18, 18);
  const centerWall = [];
  for (let c = 4; c <= 10; c++) centerWall.push([7, c]);
  const pillars = [
    [3, 3], [3, 4], [4, 3],
    [3, 11], [3, 10], [4, 11],
    [11, 3], [10, 3], [11, 4],
    [11, 11], [11, 10], [10, 11]
  ];
  const maze = [];
  for (let r = 2; r < 13; r += 2) {
    for (let c = 1; c < 14; c++) {
      if (c === 3 || c === 11) continue;
      maze.push([r, c]);
    }
  }
  const rooms = [];
  for (let r = 0; r < 15; r++) {
    if (r === 4 || r === 10) continue;
    rooms.push([r, 7]);
  }
  return [
    { name: 'face-h', grid: g15, you: { row: 7, col: 1, direction: 'right' }, opponent: { row: 7, col: 13, direction: 'left' } },
    { name: 'face-v', grid: g15, you: { row: 1, col: 7, direction: 'down' }, opponent: { row: 13, col: 7, direction: 'up' } },
    { name: 'corners', grid: g15, you: { row: 1, col: 1, direction: 'right' }, opponent: { row: 13, col: 13, direction: 'left' } },
    { name: 'offset', grid: g15, you: { row: 3, col: 2, direction: 'down' }, opponent: { row: 11, col: 12, direction: 'up' } },
    { name: 'center-wall', grid: withWalls(g15, centerWall), you: { row: 2, col: 2, direction: 'right' }, opponent: { row: 12, col: 12, direction: 'left' } },
    { name: 'pillars', grid: withWalls(g15, pillars), you: { row: 7, col: 1, direction: 'right' }, opponent: { row: 7, col: 13, direction: 'left' } },
    { name: 'small', grid: g12, you: { row: 5, col: 1, direction: 'right' }, opponent: { row: 5, col: 10, direction: 'left' } },
    { name: 'large', grid: g18, you: { row: 9, col: 1, direction: 'right' }, opponent: { row: 9, col: 16, direction: 'left' } },
    { name: 'maze', grid: withWalls(g15, maze), you: { row: 1, col: 1, direction: 'right' }, opponent: { row: 13, col: 13, direction: 'left' } },
    { name: 'rooms', grid: withWalls(g15, rooms), you: { row: 2, col: 2, direction: 'down' }, opponent: { row: 12, col: 12, direction: 'up' } }
  ];
}

function pickBest(cands, scoreFn) {
  let best = cands[0];
  let bestScore = -Infinity;
  for (const cand of cands) {
    const s = scoreFn(cand);
    if (s > bestScore) {
      bestScore = s;
      best = cand;
    }
  }
  return best.action;
}

function botExit(state) {
  const cells = cloneGrid(state.grid);
  const rows = state.rows;
  const cols = state.cols;
  const safe = safeMoves(state.you, cells, rows, cols);
  if (!safe.length) return 'straight';
  return pickBest(safe, (cand) => {
    let exits = liberty(cells, cand.next.row, cand.next.col, rows, cols);
    cells[cand.next.row][cand.next.col] = '#';
    let extra = 0;
    for (let k = 0; k < 4; k++) {
      extra += liberty(cells, cand.next.row + DR[k], cand.next.col + DC[k], rows, cols);
    }
    cells[cand.next.row][cand.next.col] = '.';
    if (cand.action === 'straight') extra += 0.2;
    return exits * 10 + extra;
  });
}

function botSpace(state) {
  const cells = cloneGrid(state.grid);
  const rows = state.rows;
  const cols = state.cols;
  const safe = safeMoves(state.you, cells, rows, cols);
  if (!safe.length) return 'straight';
  return pickBest(safe, (cand) => {
    cells[cand.next.row][cand.next.col] = '#';
    const space = flood(cells, cand.next.row, cand.next.col, rows, cols);
    cells[cand.next.row][cand.next.col] = '.';
    return space * 10 + (cand.action === 'straight' ? 1 : 0);
  });
}

function botTerritory(state) {
  const cells = cloneGrid(state.grid);
  const rows = state.rows;
  const cols = state.cols;
  const safe = safeMoves(state.you, cells, rows, cols);
  const oppSafe = safeMoves(state.opponent, cells, rows, cols);
  if (!safe.length) return 'straight';
  if (!oppSafe.length) return safe[0].action;
  return pickBest(safe, (cand) => {
    let worst = Infinity;
    for (const opp of oppSafe) {
      if (cand.next.row === opp.next.row && cand.next.col === opp.next.col) {
        worst = Math.min(worst, -50);
        continue;
      }
      cells[cand.next.row][cand.next.col] = '#';
      cells[opp.next.row][opp.next.col] = '#';
      const v = voronoi(cells, cand.next, opp.next, rows, cols);
      const s = v.mine - v.opp;
      cells[cand.next.row][cand.next.col] = '.';
      cells[opp.next.row][opp.next.col] = '.';
      if (s < worst) worst = s;
    }
    return worst * 10 + (cand.action === 'straight' ? 0.2 : 0);
  });
}

function botSteady(state) {
  const cells = cloneGrid(state.grid);
  const rows = state.rows;
  const cols = state.cols;
  const safe = safeMoves(state.you, cells, rows, cols);
  const oppSafe = safeMoves(state.opponent, cells, rows, cols);
  if (!safe.length) return 'straight';
  if (!oppSafe.length) return safe[0].action;
  return pickBest(safe, (cand) => {
    let worst = Infinity;
    for (const opp of oppSafe) {
      if (cand.next.row === opp.next.row && cand.next.col === opp.next.col) {
        worst = Math.min(worst, -1000);
        continue;
      }
      cells[cand.next.row][cand.next.col] = '#';
      cells[opp.next.row][opp.next.col] = '#';
      const mySpace = flood(cells, cand.next.row, cand.next.col, rows, cols);
      const oppSpace = flood(cells, opp.next.row, opp.next.col, rows, cols);
      const myLib = liberty(cells, cand.next.row, cand.next.col, rows, cols);
      const s = (mySpace - oppSpace) * 5 + myLib;
      cells[cand.next.row][cand.next.col] = '.';
      cells[opp.next.row][opp.next.col] = '.';
      if (s < worst) worst = s;
    }
    return worst;
  });
}

function botPredict(state) {
  const cells = cloneGrid(state.grid);
  const rows = state.rows;
  const cols = state.cols;
  const safe = safeMoves(state.you, cells, rows, cols);
  const oppSafe = safeMoves(state.opponent, cells, rows, cols);
  if (!safe.length) return 'straight';
  if (!oppSafe.length) return safe[0].action;

  function leaf(me, opp) {
    const myLib = liberty(cells, me.row, me.col, rows, cols);
    const oppLib = liberty(cells, opp.row, opp.col, rows, cols);
    if (!myLib && !oppLib) return 0;
    if (!myLib) return -10000;
    if (!oppLib) return 10000;
    const v = voronoi(cells, me, opp, rows, cols);
    return (v.mine - v.opp) * 10 + myLib * 2 - oppLib;
  }

  return pickBest(safe, (cand) => {
    let worst = Infinity;
    for (const opp of oppSafe) {
      if (cand.next.row === opp.next.row && cand.next.col === opp.next.col) {
        worst = Math.min(worst, 0);
        continue;
      }
      cells[cand.next.row][cand.next.col] = '#';
      cells[opp.next.row][opp.next.col] = '#';
      const myNext = safeMoves(cand.next, cells, rows, cols);
      const oppNext = safeMoves(opp.next, cells, rows, cols);
      let innerBest = -Infinity;
      if (!myNext.length) innerBest = oppNext.length ? -10000 : 0;
      else if (!oppNext.length) innerBest = 10000;
      else {
        for (const m2 of myNext) {
          let innerWorst = Infinity;
          for (const o2 of oppNext) {
            let s;
            if (m2.next.row === o2.next.row && m2.next.col === o2.next.col) s = 0;
            else {
              cells[m2.next.row][m2.next.col] = '#';
              cells[o2.next.row][o2.next.col] = '#';
              s = leaf(m2.next, o2.next);
              cells[m2.next.row][m2.next.col] = '.';
              cells[o2.next.row][o2.next.col] = '.';
            }
            if (s < innerWorst) innerWorst = s;
          }
          if (innerWorst > innerBest) innerBest = innerWorst;
        }
      }
      cells[cand.next.row][cand.next.col] = '.';
      cells[opp.next.row][opp.next.col] = '.';
      if (innerBest < worst) worst = innerBest;
    }
    return worst;
  });
}

const opponents = [
  { name: 'exit', fn: botExit },
  { name: 'space', fn: botSpace },
  { name: 'territory', fn: botTerritory },
  { name: 'steady', fn: botSteady },
  { name: 'predict', fn: botPredict }
];

function dumpGame(youBot, oppBot, scenario, swapSides, maxTurns) {
  const rows = scenario.grid.length;
  const cols = scenario.grid[0].length;
  const cells = cloneGrid(scenario.grid);
  let a = { ...scenario.you };
  let b = { ...scenario.opponent };
  if (swapSides) {
    const tmp = a;
    a = b;
    b = tmp;
  }
  cells[a.row][a.col] = '#';
  cells[b.row][b.col] = '#';
  const marks = cloneGrid(gridStrings(cells));
  marks[a.row][a.col] = 'A';
  marks[b.row][b.col] = 'B';
  for (let turn = 1; turn <= (maxTurns || rows * cols); turn++) {
    const actA = callBot(youBot, makeState(turn, cells, a, b));
    const actB = callBot(oppBot, makeState(turn, cells, b, a));
    const nextA = applyAction(a, actA);
    const nextB = applyAction(b, actB);
    const crashA = isWall(cells, nextA.row, nextA.col, rows, cols);
    const crashB = isWall(cells, nextB.row, nextB.col, rows, cols);
    if (crashA || crashB || (nextA.row === nextB.row && nextA.col === nextB.col)) {
      console.log('end turn', turn, 'A', actA, nextA, 'crash', crashA, 'B', actB, nextB, 'crash', crashB);
      break;
    }
    cells[nextA.row][nextA.col] = '#';
    cells[nextB.row][nextB.col] = '#';
    marks[nextA.row][nextA.col] = 'a';
    marks[nextB.row][nextB.col] = 'b';
    a = nextA;
    b = nextB;
    marks[a.row][a.col] = 'A';
    marks[b.row][b.col] = 'B';
  }
  console.log(marks.map((r) => r.join('')).join('\n'));
}

function main() {
  const maps = scenarios();
  const ourBot = typeof chooseMove === 'function' ? chooseMove : chooseMove.chooseMove;
  if (process.argv[2] === 'dump') {
    const sc = maps.find((m) => m.name === (process.argv[3] || 'face-h'));
    const opp = opponents.find((o) => o.name === (process.argv[4] || 'predict'));
    dumpGame(ourBot, opp.fn, sc, process.argv[5] === 'swap');
    return;
  }
  let total = 0;
  let points = 0;
  const perOpp = {};
  const t0 = Date.now();
  for (const opp of opponents) {
    perOpp[opp.name] = { win: 0, draw: 0, loss: 0, pts: 0 };
    for (const sc of maps) {
      for (const swap of process.argv[2] === 'official' ? [false] : [false, true]) {
        const played = play(ourBot, opp.fn, sc, swap);
        const result = played.result;
        total++;
        if (result === 'win') {
          points += 2;
          perOpp[opp.name].win++;
          perOpp[opp.name].pts += 2;
        } else if (result === 'draw') {
          points += 1;
          perOpp[opp.name].draw++;
          perOpp[opp.name].pts += 1;
          if (opp.name === 'territory' || opp.name === 'predict') {
            console.log(result, opp.name, sc.name, 'swap=' + swap, played.reason);
          }
        } else {
          perOpp[opp.name].loss++;
          if (opp.name === 'territory' || opp.name === 'predict') {
            console.log(result, opp.name, sc.name, 'swap=' + swap, played.reason);
          }
        }
      }
    }
  }
  const elapsed = Date.now() - t0;
  console.log('Games:', total);
  console.log('Points:', points, '/', total * 2, '(' + (points / (total * 2) * 100).toFixed(1) + '%)');
  console.log('Elapsed ms:', elapsed);
  for (const name of Object.keys(perOpp)) {
    const s = perOpp[name];
    console.log(
      name.padEnd(10),
      'W', s.win, 'D', s.draw, 'L', s.loss,
      'pts', s.pts, '/', maps.length * 2 * 2
    );
  }
}

main();
