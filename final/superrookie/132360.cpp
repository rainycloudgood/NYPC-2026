// NYPC 2026 Final - SuperRookie
// v1: exact physics port (boxes treated as static walls) + physics-space BFS.
#include <bits/stdc++.h>
using namespace std;
typedef unsigned int u32;

static int N, M, H, W;
static string KIND;

enum : unsigned char { UNK = 0, EMP, WALL, BOX, SPK, JMP, COIN, SHLD };
static vector<unsigned char> cellT;
static vector<int> seenStamp;
static int frameNo = 0;

static inline bool inb(int r, int c) { return r >= 0 && r < N && c >= 0 && c < M; }
static inline bool solidCell(int r, int c) {
  if (!inb(r, c)) return true;                 // outside map: never enterable
  unsigned char t = cellT[r * M + c];
  return t == WALL || t == BOX;
}
static inline bool blockedAt(int y, int x) {
  int r0 = y / 6, r1 = (y + 5) / 6, c0 = x / 6, c1 = (x + 5) / 6;
  for (int r = r0; r <= r1; r++)
    for (int c = c0; c <= c1; c++)
      if (solidCell(r, c)) return true;
  return false;
}
static inline bool onJumpAt(int y, int x) {
  int r0 = y / 6, r1 = (y + 5) / 6, c0 = x / 6, c1 = (x + 5) / 6;
  for (int r = r0; r <= r1; r++)
    for (int c = c0; c <= c1; c++)
      if (inb(r, c) && cellT[r * M + c] == JMP) return true;
  return false;
}
static inline bool itemPix(int py, int px) {
  if (py == 2 || py == 3) return px >= 1 && px <= 4;
  if (py == 1 || py == 4) return px >= 2 && px <= 3;
  return false;
}
// 1 = picked up coin/shield, -1 = unshielded spike (forbidden)
static inline int touchAt(int y, int x, int shields) {
  int r0 = y / 6, r1 = (y + 5) / 6, c0 = x / 6, c1 = (x + 5) / 6, got = 0;
  for (int r = r0; r <= r1; r++)
    for (int c = c0; c <= c1; c++) {
      if (!inb(r, c)) continue;
      unsigned char t = cellT[r * M + c];
      if (t == SPK) {
        if (shields <= 0) return -1;
      } else if (t == COIN || t == SHLD) {
        int ay = max(0, y - 6 * r), by = min(5, y + 5 - 6 * r);
        int ax = max(0, x - 6 * c), bx = min(5, x + 5 - 6 * c);
        for (int py = ay; py <= by && !got; py++)
          for (int px = ax; px <= bx; px++)
            if (itemPix(py, px)) { got = 1; break; }
      }
    }
  return got;
}

struct S { short y, x; signed char vy, vx, wg, wj, hold; };

// exact port of Game.step (character only; boxes are static solids here)
static int simStep(S &s, int cmd, int shields, int &got) {
  got = 0;
  bool ground = blockedAt(s.y + 1, s.x) || onJumpAt(s.y, s.x);
  bool jumped = false;
  if (cmd & 8) { jumped = true; s.wj = 0; s.hold = 0; }
  else if (cmd & 4) {
    if (ground || (s.wg && !s.wj)) { jumped = true; s.wj = 1; s.hold = 0; }
    else if (s.wj && s.hold < 2) { jumped = true; s.hold++; }
    else { s.wj = 0; s.hold = 0; }
  } else { s.wj = 0; s.hold = 0; }
  if (jumped) s.vy = -3;
  {
    int d = s.vy < 0 ? -1 : 1, n = s.vy < 0 ? -s.vy : s.vy;
    while (n) {
      if (blockedAt(s.y + d, s.x)) { s.vy = 0; break; }
      s.y += d;
      int t = touchAt(s.y, s.x, shields);
      if (t < 0) return -1;
      got |= t;
      n--;
    }
    if (!jumped && !blockedAt(s.y + 1, s.x) && s.vy < 6) s.vy++;
  }
  int dir = (cmd & 2) ? 1 : ((cmd & 1) ? -1 : 0);
  if (s.vx && (dir == 0 || ((s.vx < 0) != (dir < 0)))) s.vx += (s.vx < 0 ? 1 : -1);
  if (dir && !blockedAt(s.y, s.x + dir)) {
    if (s.vx * dir < 4) s.vx += dir;
  }
  if (s.vx) {
    int d = s.vx < 0 ? -1 : 1, n = s.vx < 0 ? -s.vx : s.vx;
    for (int i = 0; i < n; i++) {
      if (blockedAt(s.y, s.x + d)) { s.vx = 0; break; }
      s.x += d;
      int t = touchAt(s.y, s.x, shields);
      if (t < 0) return -1;
      got |= t;
    }
  }
  s.wg = ground ? 1 : 0;
  return 0;
}

// ---------- map memory ----------
static char view[2304];
static void updateMap(int cy, int cx) {
  frameNo++;
  for (int i = 0; i < 2304; i++) {
    char ch = view[i];
    if (ch == '.' || ch == '@') continue;
    int y = cy + (i / 48) - 21, x = cx + (i % 48) - 21;
    if (y < 0 || x < 0) continue;
    int r = y / 6, c = x / 6;
    if (!inb(r, c)) continue;
    unsigned char t = ch == '#' ? WALL : ch == 'O' ? BOX : ch == '^' ? SPK
                    : ch == '+' ? JMP : ch == '$' ? COIN : ch == '*' ? SHLD : UNK;
    if (t != UNK) { cellT[r * M + c] = t; seenStamp[r * M + c] = frameNo; }
  }
  for (int i = 0; i < 2304; i++) {
    if (view[i] != '.') continue;
    int y = cy + (i / 48) - 21, x = cx + (i % 48) - 21;
    if (y < 0 || x < 0) continue;
    int r = y / 6, c = x / 6;
    if (!inb(r, c)) continue;
    int id = r * M + c;
    if (seenStamp[id] == frameNo) continue;
    int py = y - 6 * r, px = x - 6 * c;
    if (itemPix(py, px)) cellT[id] = EMP;               // definitive: no item, no solid
    else {
      unsigned char t = cellT[id];
      if (t == WALL || t == BOX || t == SPK || t == JMP) cellT[id] = EMP;
    }
  }
}

// ---------- guidance field ----------
static vector<int> gd;
static vector<int> bq;
static const int INF = 1 << 29;

static bool computeGuide(int shields, bool frontierMode) {
  gd.assign(N * M, INF);
  bq.clear();
  for (int r = 0; r < N; r++)
    for (int c = 0; c < M; c++) {
      int id = r * M + c;
      unsigned char t = cellT[id];
      bool src = false;
      if (!frontierMode) {
        if (t == COIN || t == SHLD) src = true;
      } else if (t == UNK) {
        static const int dr[4] = {1, -1, 0, 0}, dc[4] = {0, 0, 1, -1};
        for (int k = 0; k < 4; k++) {
          int nr = r + dr[k], nc = c + dc[k];
          if (!inb(nr, nc)) continue;
          unsigned char nt = cellT[nr * M + nc];
          if (nt != UNK && nt != WALL && nt != BOX) { src = true; break; }
        }
      }
      if (src) { gd[id] = 0; bq.push_back(id); }
    }
  if (bq.empty()) return false;
  static const int dr[4] = {1, -1, 0, 0}, dc[4] = {0, 0, 1, -1};
  for (size_t h = 0; h < bq.size(); h++) {
    int id = bq[h], r = id / M, c = id % M, d = gd[id];
    for (int k = 0; k < 4; k++) {
      int nr = r + dr[k], nc = c + dc[k];
      if (!inb(nr, nc)) continue;
      int nid = nr * M + nc;
      if (gd[nid] != INF) continue;
      unsigned char t = cellT[nid];
      if (t == WALL || t == BOX) continue;
      if (t == SPK && shields <= 0) continue;
      gd[nid] = d + 1;
      bq.push_back(nid);
    }
  }
  return true;
}

// ---------- physics BFS ----------
struct BN { S s; int par; short act; short depth; };
static vector<BN> nodes;
static const int HB = 18, HSZ = 1 << HB, HMASK = HSZ - 1;
static vector<u32> hkey, hgen;
static u32 curGen = 0;

static inline u32 stKey(const S &s) {
  u32 idx = (u32)s.y * (u32)W + (u32)s.x;
  u32 k = idx * 10u + (u32)(s.vy + 3);
  k = k * 9u + (u32)(s.vx + 4);
  k = k * 12u + (u32)(s.wg * 6 + s.wj * 3 + s.hold);
  return k ? k : 1u;
}
static inline bool hInsert(u32 k) {
  u32 h = (k * 2654435761u) & HMASK;
  while (hgen[h] == curGen) {
    if (hkey[h] == k) return false;
    h = (h + 1) & HMASK;
  }
  hgen[h] = curGen;
  hkey[h] = k;
  return true;
}

static const int ACTS[6] = {0, 1, 2, 4, 5, 6};

static void reconstruct(int idx, vector<int> &plan) {
  plan.clear();
  while (idx > 0) { plan.push_back(nodes[idx].act); idx = nodes[idx].par; }
  reverse(plan.begin(), plan.end());
}

static bool planBFS(const S &root, int shields, int cap, int maxDepth, vector<int> &plan) {
  nodes.clear();
  curGen++;
  if (curGen == 0) { fill(hgen.begin(), hgen.end(), 0u); curGen = 1; }
  BN rn; rn.s = root; rn.par = -1; rn.act = 0; rn.depth = 0;
  nodes.push_back(rn);
  hInsert(stKey(root));
  int cyc = (root.y + 3) / 6, cxc = (root.x + 3) / 6;
  int bestScore = (inb(cyc, cxc) ? gd[cyc * M + cxc] : INF), bestDepth = 0, bestIdx = 0;
  for (size_t head = 0; head < nodes.size() && (int)nodes.size() < cap; head++) {
    BN cur = nodes[head];
    if (cur.depth >= maxDepth) continue;
    for (int a = 0; a < 6; a++) {
      S ns = cur.s;
      int got;
      if (simStep(ns, ACTS[a], shields, got) < 0) continue;
      if (!hInsert(stKey(ns))) continue;
      BN nn; nn.s = ns; nn.par = (int)head; nn.act = (short)ACTS[a]; nn.depth = cur.depth + 1;
      nodes.push_back(nn);
      if (got) { reconstruct((int)nodes.size() - 1, plan); return true; }
      int ry = (ns.y + 3) / 6, rx = (ns.x + 3) / 6;
      int sc = inb(ry, rx) ? gd[ry * M + rx] : INF;
      if (sc < bestScore || (sc == bestScore && nn.depth < bestDepth)) {
        bestScore = sc; bestDepth = nn.depth; bestIdx = (int)nodes.size() - 1;
      }
      if ((int)nodes.size() >= cap) break;
    }
  }
  if (getenv("DBG")) {
    int rc = (root.y + 3) / 6, cc = (root.x + 3) / 6;
    fprintf(stderr, "dbg y=%d x=%d cell=(%d,%d) gdroot=%d nodes=%d best=%d bestIdx=%d\n",
            root.y, root.x, rc, cc, inb(rc, cc) ? gd[rc * M + cc] : -1,
            (int)nodes.size(), bestScore, bestIdx);
  }
  if (bestIdx == 0) return false;
  reconstruct(bestIdx, plan);
  return true;
}

// ---------- io ----------
static bool getLine(string &s) {
  if (!std::getline(cin, s)) return false;
  while (!s.empty() && (s.back() == '\r' || s.back() == '\n')) s.pop_back();
  return true;
}
static void decode(const string &e) {
  int p = 0, n = (int)e.size(), i = 0;
  while (p < n && i < 2304) {
    char ch = e[p++];
    int cnt = 0;
    while (p < n && e[p] >= '0' && e[p] <= '9') cnt = cnt * 10 + (e[p++] - '0');
    while (cnt-- > 0 && i < 2304) view[i++] = ch;
  }
}
static void emit(int cmd) {
  char buf[16];
  int k = 0;
  char cs[4];
  if (cmd & 8) cs[k++] = 'S';
  else if (cmd & 4) cs[k++] = 'J';
  if (cmd & 2) cs[k++] = '>';
  else if (cmd & 1) cs[k++] = '<';
  int len = 0;
  buf[len++] = (char)('0' + k);
  buf[len++] = '\n';
  for (int i = 0; i < k; i++) { buf[len++] = cs[i]; buf[len++] = '\n'; }
  fwrite(buf, 1, len, stdout);
  fflush(stdout);
}
static void finishNow() { fputs("FINISH\n", stdout); fflush(stdout); }

static int envInt(const char *k, int d) { const char *v = getenv(k); return v ? atoi(v) : d; }

int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);
  const int BUDGET_MS = envInt("BUDGET_MS", 1500);
  const int NODE_CAP = envInt("NODE_CAP", 12000);
  const int MAX_DEPTH = envInt("MAX_DEPTH", 160);
  const int REPLAN_PERIOD = envInt("REPLAN_PERIOD", 24);

  string line;
  if (!getLine(line)) return 0;
  {
    istringstream is(line);
    if (!(is >> N >> M >> KIND)) return 0;
  }
  H = 6 * N; W = 6 * M;
  cellT.assign(N * M, UNK);
  seenStamp.assign(N * M, -1);
  gd.assign(N * M, INF);
  hkey.assign(HSZ, 0u);
  hgen.assign(HSZ, 0u);
  nodes.reserve(NODE_CAP + 16);

  long long usedNs = 0;
  const long long budgetNs = (long long)BUDGET_MS * 1000000LL;

  int coins = 0, shields = 0, cy = 0, cx = 0;
  if (!getLine(line)) return 0;
  { istringstream is(line); is >> coins >> shields >> cy >> cx; }
  if (!getLine(line)) return 0;
  decode(line);
  updateMap(cy, cx);

  S cur; cur.y = (short)cy; cur.x = (short)cx; cur.vy = 0; cur.vx = 0; cur.wg = 0; cur.wj = 0; cur.hold = 0;

  vector<int> plan;
  size_t planPos = 0;
  int actions = 0, sinceReplan = 1 << 20, noTargetStreak = 0, stuckCnt = 0;
  int lastY = cy, lastX = cx, prevCoins = coins, prevShields = shields;
  unsigned rng = 12345u;

  while (true) {
    auto t0 = chrono::steady_clock::now();
    if (actions >= 10000 || usedNs > budgetNs) { finishNow(); return 0; }

    bool needReplan = (planPos >= plan.size()) || (sinceReplan >= REPLAN_PERIOD) ||
                      (coins != prevCoins) || (shields != prevShields);
    if (needReplan) {
      bool ok = computeGuide(shields, false);
      if (!ok) ok = computeGuide(shields, true);
      else {
        int rc = (cur.y + 3) / 6, cc = (cur.x + 3) / 6;
        if (!inb(rc, cc) || gd[rc * M + cc] >= INF) ok = computeGuide(shields, true);
      }
      if (!ok) { finishNow(); return 0; }
      int cap = NODE_CAP;
      long long left = budgetNs - usedNs;
      if (left < budgetNs / 4) cap = NODE_CAP / 3;
      if (left < budgetNs / 10) cap = 1200;
      plan.clear(); planPos = 0;
      if (!planBFS(cur, shields, cap, MAX_DEPTH, plan)) {
        noTargetStreak++;
        if (noTargetStreak > 40) { finishNow(); return 0; }
      } else noTargetStreak = 0;
      sinceReplan = 0;
    }

    int cmd = 0;
    if (planPos < plan.size()) cmd = plan[planPos++];
    if (stuckCnt > 40) {                       // unstick: random hop
      rng = rng * 1103515245u + 12345u;
      cmd = ACTS[(rng >> 16) % 6];
      if ((rng >> 24) & 1) cmd |= 4;
      plan.clear(); planPos = 0; stuckCnt = 0;
    }

    prevCoins = coins; prevShields = shields;
    int dummy;
    S pred = cur;
    simStep(pred, cmd, shields, dummy);

    emit(cmd);
    actions++;
    sinceReplan++;
    usedNs += chrono::duration_cast<chrono::nanoseconds>(chrono::steady_clock::now() - t0).count();

    if (!getLine(line)) return 0;
    { istringstream is(line); is >> coins >> shields >> cy >> cx; }
    if (!getLine(line)) return 0;
    auto t1 = chrono::steady_clock::now();
    decode(line);
    updateMap(cy, cx);

    cur = pred;
    if (pred.y != cy || pred.x != cx) {        // divergence: resync, force replan
      cur.y = (short)cy; cur.x = (short)cx;
      plan.clear(); planPos = 0;
    }
    if (cy == lastY && cx == lastX) stuckCnt++; else stuckCnt = 0;
    lastY = cy; lastX = cx;
    usedNs += chrono::duration_cast<chrono::nanoseconds>(chrono::steady_clock::now() - t1).count();
  }
}
