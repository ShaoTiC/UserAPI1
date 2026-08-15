/**
 * Tron / 轨迹对战策略
 *
 * chooseMove(state) -> 'left' | 'straight' | 'right'
 *
 * 1. 过滤立即撞墙 / 越界
 * 2. 双方地盘已断开：在自己区域内贴墙填空（两步前瞻，避免挖洞）
 * 3. 仍在争夺时：按争地型对手预测，用 Voronoi 评估
 * 4. 本回合可能对撞的格子尽量避开，但不因此放弃大块领地
 */

var DIRS = ['up', 'right', 'down', 'left'];
var DR = [-1, 0, 1, 0];
var DC = [0, 1, 0, -1];
var ACTION_TURN = { left: -1, straight: 0, right: 1 };
var ALL_ACTIONS = ['left', 'straight', 'right'];

var WIN = 1000000;
var LOSS = -1000000;
var DRAW = -1200;

function dirIndex(dir) {
  if (dir === 'up') return 0;
  if (dir === 'right') return 1;
  if (dir === 'down') return 2;
  if (dir === 'left') return 3;
  var i = DIRS.indexOf(dir);
  return i < 0 ? 0 : i;
}

function applyAction(player, action) {
  var idx = dirIndex(player.direction);
  var turn = ACTION_TURN[action];
  if (turn === undefined) turn = 0;
  var ni = (idx + turn + 4) % 4;
  return {
    row: player.row + DR[ni],
    col: player.col + DC[ni],
    direction: DIRS[ni],
    dirIdx: ni
  };
}

function inBounds(r, c, rows, cols) {
  return r >= 0 && c >= 0 && r < rows && c < cols;
}

function packGrid(grid, rows, cols) {
  var blocked = new Uint8Array(rows * cols);
  for (var r = 0; r < rows; r++) {
    var row = grid[r];
    for (var c = 0; c < cols; c++) {
      if (row[c] !== '.') blocked[r * cols + c] = 1;
    }
  }
  return blocked;
}

function isBlocked(blocked, rows, cols, r, c) {
  if (!inBounds(r, c, rows, cols)) return true;
  return blocked[r * cols + c] === 1;
}

function liberty(blocked, rows, cols, r, c) {
  var n = 0;
  if (!isBlocked(blocked, rows, cols, r - 1, c)) n++;
  if (!isBlocked(blocked, rows, cols, r + 1, c)) n++;
  if (!isBlocked(blocked, rows, cols, r, c - 1)) n++;
  if (!isBlocked(blocked, rows, cols, r, c + 1)) n++;
  return n;
}

function exitScore(blocked, rows, cols, r, c) {
  var score = 0;
  for (var k = 0; k < 4; k++) {
    var nr = r + DR[k];
    var nc = c + DC[k];
    if (isBlocked(blocked, rows, cols, nr, nc)) continue;
    score += 4;
    for (var k2 = 0; k2 < 4; k2++) {
      var n2r = nr + DR[k2];
      var n2c = nc + DC[k2];
      if (n2r === r && n2c === c) continue;
      if (!isBlocked(blocked, rows, cols, n2r, n2c)) score += 1;
    }
  }
  return score;
}

function bfsReach(blocked, rows, cols, sr, sc, distOut, seen, stamp) {
  var n = rows * cols;
  var q = new Int32Array(n);
  var head = 0;
  var tail = 0;
  var count = 0;
  for (var k = 0; k < 4; k++) {
    var r = sr + DR[k];
    var c = sc + DC[k];
    if (isBlocked(blocked, rows, cols, r, c)) continue;
    var i = r * cols + c;
    if (seen[i] === stamp) continue;
    seen[i] = stamp;
    distOut[i] = 1;
    q[tail++] = i;
    count++;
  }
  while (head < tail) {
    var cur = q[head++];
    var cr = (cur / cols) | 0;
    var cc = cur - cr * cols;
    var nd = distOut[cur] + 1;
    for (var k3 = 0; k3 < 4; k3++) {
      var nr = cr + DR[k3];
      var nc = cc + DC[k3];
      if (isBlocked(blocked, rows, cols, nr, nc)) continue;
      var ni = nr * cols + nc;
      if (seen[ni] === stamp) continue;
      seen[ni] = stamp;
      distOut[ni] = nd;
      q[tail++] = ni;
      count++;
    }
  }
  return count;
}

function makeBuffers(n) {
  return {
    distA: new Int16Array(n),
    distB: new Int16Array(n),
    seenA: new Int32Array(n),
    seenB: new Int32Array(n),
    stamp: 1
  };
}

function bumpStamp(buf, n) {
  if (buf.stamp > 2000000000) {
    buf.stamp = 1;
    for (var i = 0; i < n; i++) {
      buf.seenA[i] = 0;
      buf.seenB[i] = 0;
    }
  }
}

function analyze(blocked, rows, cols, a, b, buf) {
  var n = rows * cols;
  var i;
  for (i = 0; i < n; i++) {
    buf.distA[i] = 32767;
    buf.distB[i] = 32767;
  }
  var reachA = bfsReach(blocked, rows, cols, a.row, a.col, buf.distA, buf.seenA, buf.stamp++);
  var reachB = bfsReach(blocked, rows, cols, b.row, b.col, buf.distB, buf.seenB, buf.stamp++);
  bumpStamp(buf, n);
  var mine = 0;
  var opp = 0;
  var ties = 0;
  var connected = 0;
  for (i = 0; i < n; i++) {
    var da = buf.distA[i];
    var db = buf.distB[i];
    if (da === 32767 && db === 32767) continue;
    if (da < db) mine++;
    else if (db < da) opp++;
    else ties++;
    if (da < 32767 && db < 32767) connected = 1;
  }
  return {
    mine: mine,
    opp: opp,
    ties: ties,
    reachA: reachA,
    reachB: reachB,
    connected: connected
  };
}

function wallFollowBonus(blocked, rows, cols, pos) {
  var right = (pos.dirIdx + 1) % 4;
  var left = (pos.dirIdx + 3) % 4;
  var bonus = 0;
  if (isBlocked(blocked, rows, cols, pos.row + DR[right], pos.col + DC[right])) bonus += 10;
  if (isBlocked(blocked, rows, cols, pos.row + DR[left], pos.col + DC[left])) bonus += 5;
  var deg = liberty(blocked, rows, cols, pos.row, pos.col);
  bonus += (3 - deg) * 6;
  if (pos.row === 0 || pos.col === 0 || pos.row === rows - 1 || pos.col === cols - 1) bonus += 5;
  return bonus;
}

function collectMoves(player, blocked, rows, cols, actions) {
  var list = [];
  for (var i = 0; i < actions.length; i++) {
    var action = actions[i];
    var next = applyAction(player, action);
    list.push({
      action: action,
      next: next,
      crash: isBlocked(blocked, rows, cols, next.row, next.col)
    });
  }
  return list;
}

function safeOnly(moves) {
  var out = [];
  for (var i = 0; i < moves.length; i++) if (!moves[i].crash) out.push(moves[i]);
  return out;
}

function nextMaxSpace(blocked, rows, cols, pos, buf) {
  var best = 0;
  for (var a = 0; a < ALL_ACTIONS.length; a++) {
    var nxt = applyAction(pos, ALL_ACTIONS[a]);
    if (isBlocked(blocked, rows, cols, nxt.row, nxt.col)) continue;
    var idx = nxt.row * cols + nxt.col;
    blocked[idx] = 1;
    for (var t = 0; t < buf.distA.length; t++) buf.distA[t] = 32767;
    var space = bfsReach(blocked, rows, cols, nxt.row, nxt.col, buf.distA, buf.seenA, buf.stamp++);
    blocked[idx] = 0;
    if (space > best) best = space;
  }
  return best;
}

function pickFill(blocked, rows, cols, mySafe, buf) {
  var bestAction = mySafe[0].action;
  var best = -Infinity;
  var maxSpace = -1;
  var items = [];
  var i;
  for (i = 0; i < mySafe.length; i++) {
    var nxt = mySafe[i].next;
    var idx = nxt.row * cols + nxt.col;
    blocked[idx] = 1;
    for (var t = 0; t < buf.distA.length; t++) buf.distA[t] = 32767;
    var space = bfsReach(blocked, rows, cols, nxt.row, nxt.col, buf.distA, buf.seenA, buf.stamp++);
    var deg = liberty(blocked, rows, cols, nxt.row, nxt.col);
    var hug = wallFollowBonus(blocked, rows, cols, nxt);
    var look = nextMaxSpace(blocked, rows, cols, nxt, buf);
    blocked[idx] = 0;
    items.push({ space: space, deg: deg, hug: hug, look: look, action: mySafe[i].action });
    if (space > maxSpace) maxSpace = space;
  }
  var viable = 0;
  for (i = 0; i < items.length; i++) {
    if (items[i].space === maxSpace && !(items[i].deg === 0 && items[i].space > 0)) viable++;
  }
  for (i = 0; i < items.length; i++) {
    var it = items[i];
    if (it.space < maxSpace) continue;
    if (it.deg === 0 && it.space > 0 && viable) continue;
    var val = it.look * 120 + it.hug * 22 - it.deg * 70;
    if (it.look < it.space - 1) val -= 2500;
    if (it.action === 'straight') val += 1;
    if (val > best) {
      best = val;
      bestAction = it.action;
    }
  }
  return bestAction;
}

function staticEval(blocked, rows, cols, me, opp, buf) {
  var myLib = liberty(blocked, rows, cols, me.row, me.col);
  var oppLib = liberty(blocked, rows, cols, opp.row, opp.col);
  if (myLib === 0 && oppLib === 0) return DRAW;
  if (myLib === 0) return LOSS + oppLib;
  if (oppLib === 0) return WIN - myLib;

  var a = analyze(blocked, rows, cols, me, opp, buf);
  var fill = wallFollowBonus(blocked, rows, cols, me);
  var myExit = exitScore(blocked, rows, cols, me.row, me.col);
  var oppExit = exitScore(blocked, rows, cols, opp.row, opp.col);
  var mySpace = a.mine + a.ties * 0.35;
  var oppSpace = a.opp + a.ties * 0.35;

  if (!a.connected) {
    var gap = a.reachA - a.reachB;
    var score = gap * 15000 + a.reachA * 40 + fill * 10 + myExit;
    if (gap > 0) score += 80000;
    if (gap < 0) score -= 80000;
    if (myLib === 1 && a.reachA > 2) score -= 80;
    return score;
  }

  var s = (mySpace - oppSpace) * 480;
  s += (a.reachA - a.reachB) * 110;
  s += (myExit - oppExit) * 12;
  s += fill * 2;
  if (myLib === 1 && a.reachA > 4) s -= 90;
  if (a.reachA >= a.reachB + 3) s += fill * 4;
  return s;
}

function evalPair(blocked, rows, cols, meMove, oppMove, buf) {
  if (meMove.crash && oppMove.crash) return DRAW;
  if (meMove.crash) return LOSS;
  if (oppMove.crash) return WIN;
  if (meMove.next.row === oppMove.next.row && meMove.next.col === oppMove.next.col) return DRAW;

  var i1 = meMove.next.row * cols + meMove.next.col;
  var i2 = oppMove.next.row * cols + oppMove.next.col;
  blocked[i1] = 1;
  blocked[i2] = 1;
  var score = staticEval(blocked, rows, cols, meMove.next, oppMove.next, buf);
  blocked[i1] = 0;
  blocked[i2] = 0;
  return score;
}

function oppGreedyValue(blocked, rows, cols, meMove, oppMove, buf) {
  if (oppMove.crash) return -WIN;
  if (meMove.next.row === oppMove.next.row && meMove.next.col === oppMove.next.col) return -500;
  var i1 = meMove.next.row * cols + meMove.next.col;
  var i2 = oppMove.next.row * cols + oppMove.next.col;
  blocked[i1] = 1;
  blocked[i2] = 1;
  var a = analyze(blocked, rows, cols, meMove.next, oppMove.next, buf);
  var val = (a.opp - a.mine) * 24 + (a.reachB - a.reachA) * 10;
  val += exitScore(blocked, rows, cols, oppMove.next.row, oppMove.next.col);
  blocked[i1] = 0;
  blocked[i2] = 0;
  return val;
}

function corridorClear(blocked, rows, cols, me, opp) {
  var i;
  if (me.row === opp.row) {
    var c0 = Math.min(me.col, opp.col) + 1;
    var c1 = Math.max(me.col, opp.col);
    for (i = c0; i < c1; i++) if (blocked[me.row * cols + i]) return false;
    return true;
  }
  if (me.col === opp.col) {
    var r0 = Math.min(me.row, opp.row) + 1;
    var r1 = Math.max(me.row, opp.row);
    for (i = r0; i < r1; i++) if (blocked[i * cols + me.col]) return false;
    return true;
  }
  return false;
}

function facingBonus(me, opp, move, rows, cols, blocked) {
  var bonus = 0;
  if (me.row === opp.row && corridorClear(blocked, rows, cols, me, opp)) {
    var toward =
      (me.direction === 'right' && opp.direction === 'left' && me.col < opp.col) ||
      (me.direction === 'left' && opp.direction === 'right' && me.col > opp.col);
    if (toward) {
      var up = me.row;
      var down = rows - 1 - me.row;
      if (move.next.row === me.row) bonus -= 8000;
      else if (move.next.row < me.row) bonus += up >= down ? 2500 : 800;
      else bonus += down > up ? 2500 : 800;
    }
  }
  if (me.col === opp.col && corridorClear(blocked, rows, cols, me, opp)) {
    var towardC =
      (me.direction === 'down' && opp.direction === 'up' && me.row < opp.row) ||
      (me.direction === 'up' && opp.direction === 'down' && me.row > opp.row);
    if (towardC) {
      var left = me.col;
      var right = cols - 1 - me.col;
      if (move.next.col === me.col) bonus -= 8000;
      else if (move.next.col < me.col) bonus += left >= right ? 2500 : 800;
      else bonus += right > left ? 2500 : 800;
    }
  }
  return bonus;
}

function reachAfter(blocked, rows, cols, meMove, oppMove, buf) {
  var i1 = meMove.next.row * cols + meMove.next.col;
  var i2 = oppMove.next.row * cols + oppMove.next.col;
  blocked[i1] = 1;
  blocked[i2] = 1;
  for (var t = 0; t < buf.distA.length; t++) buf.distA[t] = 32767;
  var reach = bfsReach(blocked, rows, cols, meMove.next.row, meMove.next.col, buf.distA, buf.seenA, buf.stamp++);
  blocked[i1] = 0;
  blocked[i2] = 0;
  return reach;
}

function chooseMove(state) {
  try {
    return chooseMoveInner(state);
  } catch (e) {
    return 'straight';
  }
}

function chooseMoveInner(state) {
  if (!state || !state.you) return 'straight';
  var rows = state.rows | 0;
  var cols = state.cols | 0;
  var actions = state.legalActions && state.legalActions.length ? state.legalActions : ALL_ACTIONS;
  if (!rows || !cols || !state.grid) return actions[0] || 'straight';

  var blocked = packGrid(state.grid, rows, cols);
  var me = {
    row: state.you.row,
    col: state.you.col,
    direction: state.you.direction,
    dirIdx: dirIndex(state.you.direction)
  };
  var myMoves = collectMoves(me, blocked, rows, cols, actions);
  var mySafe = safeOnly(myMoves);
  if (mySafe.length === 0) return preferStraight(myMoves, actions);
  if (mySafe.length === 1) return mySafe[0].action;

  var buf = makeBuffers(rows * cols);
  if (!state.opponent) return pickFill(blocked, rows, cols, mySafe, buf);

  var opp = {
    row: state.opponent.row,
    col: state.opponent.col,
    direction: state.opponent.direction,
    dirIdx: dirIndex(state.opponent.direction)
  };
  var oppSafe = safeOnly(collectMoves(opp, blocked, rows, cols, ALL_ACTIONS));
  if (oppSafe.length === 0) return mySafe[0].action;

  var cur = analyze(blocked, rows, cols, me, opp, buf);
  var dist = Math.abs(me.row - opp.row) + Math.abs(me.col - opp.col);
  if (!cur.connected || (dist >= 9 && cur.ties <= 3 && cur.mine >= cur.opp + 5)) {
    return pickFill(blocked, rows, cols, mySafe, buf);
  }

  var i;
  var j;
  var contested = {};
  for (j = 0; j < oppSafe.length; j++) {
    contested[oppSafe[j].next.row + ',' + oppSafe[j].next.col] = 1;
  }

  var scored = [];
  var globalMaxReach = -1;

  for (i = 0; i < mySafe.length; i++) {
    var mine = mySafe[i];
    var key = mine.next.row + ',' + mine.next.col;
    var nonCol = [];
    for (j = 0; j < oppSafe.length; j++) {
      if (mine.next.row !== oppSafe[j].next.row || mine.next.col !== oppSafe[j].next.col) {
        nonCol.push(oppSafe[j]);
      }
    }
    var replies = nonCol.length ? nonCol : oppSafe;
    var pred = replies[0];
    var predVal = -Infinity;
    for (j = 0; j < replies.length; j++) {
      var gv = oppGreedyValue(blocked, rows, cols, mine, replies[j], buf);
      if (gv > predVal) {
        predVal = gv;
        pred = replies[j];
      }
    }

    var vsPred = evalPair(blocked, rows, cols, mine, pred, buf);
    var worst = Infinity;
    var sum = 0;
    var predReach = reachAfter(blocked, rows, cols, mine, pred, buf);
    for (j = 0; j < replies.length; j++) {
      var s = evalPair(blocked, rows, cols, mine, replies[j], buf);
      if (s < worst) worst = s;
      sum += s;
    }
    if (predReach > globalMaxReach) globalMaxReach = predReach;
    scored.push({
      action: mine.action,
      mine: mine,
      key: key,
      nonCol: nonCol,
      vsPred: vsPred,
      worst: worst,
      avg: sum / replies.length,
      predReach: predReach
    });
  }

  var bestAction = scored[0].action;
  var bestScore = -Infinity;
  var turn = state.turn | 0;
  var wWorst = turn <= 10 ? 0.18 : 0.38;
  var wPred = turn <= 10 ? 0.62 : 0.45;
  for (i = 0; i < scored.length; i++) {
    var it = scored[i];
    var score = wPred * it.vsPred + wWorst * it.worst + (1 - wPred - wWorst) * it.avg;
    score += it.predReach * 12;
    score -= (globalMaxReach - it.predReach) * 900;
    score += facingBonus(me, opp, it.mine, rows, cols, blocked);
    score += wallFollowBonus(blocked, rows, cols, it.mine.next) * 3;
    if (it.action === 'straight') score += 3;
    if (contested[it.key] && it.nonCol.length) score -= 6000;
    if (!it.nonCol.length) score -= 400;
    if (score > bestScore) {
      bestScore = score;
      bestAction = it.action;
    }
  }

  return bestAction;
}

function preferStraight(moves, actions) {
  for (var i = 0; i < moves.length; i++) {
    if (moves[i].action === 'straight') return 'straight';
  }
  return (moves[0] && moves[0].action) || (actions && actions[0]) || 'straight';
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = chooseMove;
  module.exports.chooseMove = chooseMove;
}
if (typeof globalThis !== 'undefined') {
  globalThis.chooseMove = chooseMove;
}
