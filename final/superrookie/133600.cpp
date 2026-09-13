// NYPC 2026 Final - SuperRookie
// Exact physics port (boxes treated as static walls) + physics-space BFS.
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

struct S { short y, x; signed char vy, vx, wg, wj, hold, sh, dmg, sp; };

// 1 = picked up coin/shield, -1 = spike we are not allowed to eat.
// A spike consumes a shield if we hold one, otherwise it costs damage. Since
// cost = 1 - c/(cmax+s+h), one coin always outweighs one hit, so damage is a
// price to weigh, never a hard wall.
static inline int touchAt(int y, int x, S &s, bool allowDmg) {
  int r0 = y / 6, r1 = (y + 5) / 6, c0 = x / 6, c1 = (x + 5) / 6, got = 0;
  for (int r = r0; r <= r1; r++)
    for (int c = c0; c <= c1; c++) {
      if (!inb(r, c)) continue;
      unsigned char t = cellT[r * M + c];
      if (t == SPK) {
        if (s.sh > 0) s.sh--;
        else if (allowDmg) { if (s.dmg < 120) s.dmg++; }
        else return -1;
      } else if (t == COIN || t == SHLD) {
        int ay = max(0, y - 6 * r), by = min(5, y + 5 - 6 * r);
        int ax = max(0, x - 6 * c), bx = min(5, x + 5 - 6 * c);
        bool hit = false;
        for (int py = ay; py <= by && !hit; py++)
          for (int px = ax; px <= bx; px++)
            if (itemPix(py, px)) { hit = true; break; }
        if (hit) { got = 1; if (t == SHLD && s.sh < 120) s.sh++; }
      }
    }
  return got;
}

// exact port of Game.step (character only; boxes are static solids here)
static int simStep(S &s, int cmd, bool allowDmg, int &got) {
  got = 0;
  bool ground = blockedAt(s.y + 1, s.x) || onJumpAt(s.y, s.x);
  bool jumped = false;
  if (cmd & 8) { jumped = true; if (s.sp < 120) s.sp++; s.wj = 0; s.hold = 0; }
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
      int t = touchAt(s.y, s.x, s, allowDmg);
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
      int t = touchAt(s.y, s.x, s, allowDmg);
      if (t < 0) return -1;
      got |= t;
    }
  }
  s.wg = ground ? 1 : 0;
  return 0;
}

// ---------- map memory ----------
static char view[2304];
// If ordinary movement says every target is unreachable, a box immediately
// beside the character may be the intended movable bridge rather than a wall.
// The 48x48 observation is pixel-exact: the character occupies local [21,26]
// on each axis, so columns 20/27 are precisely the newly-entered pixels for a
// one-pixel left/right push.  Return the matching movement command.
static inline int visiblePushDir() {
  bool left = false, right = false;
  for (int py = 21; py <= 26; py++) {
    left  |= view[py * 48 + 20] == 'O';
    right |= view[py * 48 + 27] == 'O';
  }
  if (left != right) return left ? 1 : 2;
  return 0; // ambiguous or no adjacent box
}
static inline int pitPushDir(int cy, int cx) {
  int d = visiblePushDir();
  if (!d) return 0;
  int dc = d == 1 ? -1 : 1;
  int br = (cy + 3) / 6;
  int bc = (d == 1 ? cx - 1 : cx + 6) / 6;
  // Push only toward an unsupported destination: this is the generic
  // "drop the crate into the pit as a platform" situation.
  if (solidCell(br + 1, bc) && !solidCell(br, bc + dc) &&
      !solidCell(br + 1, bc + dc)) return d;
  return 0;
}
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
  // cells the character overlaps are hidden by '@' but are provably passable and
  // item-free (anything collectable there was already consumed). A jump block can
  // legally overlap us, so keep a remembered JMP.
  for (int r = cy / 6; r <= (cy + 5) / 6; r++)
    for (int c = cx / 6; c <= (cx + 5) / 6; c++) {
      if (!inb(r, c)) continue;
      unsigned char &t = cellT[r * M + c];
      if (t != JMP) t = EMP;
    }
}

// ---------- guidance field ----------
static vector<int> gd;
static vector<int> gdCoin;
static int exploreBias = 0;
static vector<int> bq;
static const int INF = 1 << 29;

static inline bool passable(int r, int c) {
  if (!inb(r, c)) return false;
  unsigned char t = cellT[r * M + c];
  return t != WALL && t != BOX;
}
// can stand here: solid ground underneath, or overlapping a jump block
static int optSupport = 0;
static inline bool supported(int r, int c) {
  if (inb(r, c) && cellT[r * M + c] == JMP) return true;
  if (!inb(r + 1, c)) return true;             // map floor
  unsigned char t = cellT[(r + 1) * M + c];
  // Ground we have not seen yet is not provably standable, but calling it
  // unstandable makes half an unexplored map look unreachable and sends us
  // reaching for the special jump we are meant to avoid.
  if (optSupport && t == UNK) return true;
  return t == WALL || t == BOX || t == JMP;
}

static int heldShields = 0;
static int shieldFirst = 1;
static int flightGuide = 0;
static bool computeGuide(bool frontierMode) {
  gd.assign(N * M, INF);
  bq.clear();
  static const int dr[4] = {1, -1, 0, 0}, dc[4] = {0, 0, 1, -1};
  for (int r = 0; r < N; r++)
    for (int c = 0; c < M; c++) {
      int id = r * M + c;
      unsigned char t = cellT[id];
      bool src = false;
      if (!frontierMode) {
        if (t == COIN || t == SHLD) src = true;
      } else if (t == UNK) {
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
  if (!frontierMode && shieldFirst) {
    // Choice maps gate the coin behind a run of spikes and scatter exactly enough
    // shields to walk through unharmed. While spikes outnumber the shields we
    // carry, a shield is worth more than the coin it unlocks, so chase those only.
    int spikes = 0, shieldCells = 0;
    for (int i = 0; i < N * M; i++) {
      if (cellT[i] == SPK) spikes++;
      else if (cellT[i] == SHLD) shieldCells++;
    }
    // Spikes we have not laid eyes on yet are not in `spikes`, so gating on
    // "known spikes outnumber shields in hand" leaves us one shield short at the
    // wall of spikes guarding the coin -- and on a 1-coin Choice map one hit is
    // half the score. Mode 2 sweeps up every reachable shield first instead;
    // shields cost nothing but time, and these maps end in a few hundred frames.
    bool want = (shieldFirst >= 2) ? (spikes > 0) : (spikes > heldShields);
    if (shieldCells > 0 && want) {
      bq.clear();
      gd.assign(N * M, INF);
      for (int i = 0; i < N * M; i++)
        if (cellT[i] == SHLD) { gd[i] = 0; bq.push_back(i); }
    }
  }
  // Backward BFS with the platformer's real move set. A plain 4-neighbour flood
  // claims a shield four cells straight up is four steps away; it is in fact
  // unreachable from below, and chasing it wedges us against the shaft forever.
  // A jump rises at most 15px (2.5 cells), so upward moves are only legal from a
  // supported cell and only two cells at a time. Falling and air-steering are free.
  for (size_t h = 0; h < bq.size(); h++) {
    int id = bq[h], r = id / M, c = id % M, d = gd[id];
    int cand[5][2] = {{r, c - 1}, {r, c + 1}, {r - 1, c}, {r + 1, c}, {r + 2, c}};
    for (int k = 0; k < 5; k++) {
      int nr = cand[k][0], nc = cand[k][1];
      if (!inb(nr, nc)) continue;
      int nid = nr * M + nc;
      if (gd[nid] != INF) continue;
      if (!passable(nr, nc)) continue;
      if (k == 3 || k == 4) {                  // predecessor jumped up to reach us
        if (!flightGuide && !supported(nr, nc)) continue;
        if (k == 4 && !passable(r + 1, c)) continue;
      }
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
static vector<int> visitCnt;
static long long DMG_COST = 200000LL;   // prio: damage vs guide step
static long long SPEC_COST = 200000LL;  // prio: one frame of special jump
static int specAfter = 120;             // frames without a pickup before S is allowed
static long long specEff = 8000000LL;   // SPEC_COST scaled by how much a coin is worth
static long long dmgEff = 8000000LL;
static int scaleByCmax = 1;
static int specBudget = 100000;   // total S frames we will ever spend
static int usedSpec = 0;
static int specGate = 0;
static int refCmax = 8;
// One special-jump frame and one spike hit each add 1 to the cost denominator,
// so their price is set by what a single coin is worth: on a 4-coin Choice map
// that is a catastrophe, on a 700-coin Jump map it is noise. c_max is not given,
// but coins-in-hand plus coins-still-visible is a fair lower bound on it.
static void priceByCoinValue(int coinsHeld) {
  if (!scaleByCmax) { specEff = SPEC_COST; dmgEff = DMG_COST; return; }
  long long est = coinsHeld;
  for (int i = 0; i < N * M; i++)
    if (cellT[i] == COIN) est++;
  if (est < 1) est = 1;
  specEff = SPEC_COST * (long long)refCmax / est;
  dmgEff = DMG_COST * (long long)refCmax / est;
}
static long long DMG_SC = 1LL;          // fallback score: damage weight
static long long VIS_W = 400LL;         // prio: penalty for trodden ground
static long long VIS_SC = 10LL;         // fallback score: same
static long long GUIDE_W = 4000000LL;   // prio: weight of guide distance
static int SHAKE_AT = 60;               // frames wedged before a random hop

static inline u32 stKey(const S &s) {
  unsigned long long k = (unsigned long long)s.y * (unsigned long long)W + (unsigned long long)s.x;
  k = k * 10ull + (unsigned long long)(s.vy + 3);
  k = k * 9ull + (unsigned long long)(s.vx + 4);
  k = k * 12ull + (unsigned long long)(s.wg * 6 + s.wj * 3 + s.hold);
  k = k * 8ull + (unsigned long long)(s.sh < 7 ? s.sh : 7);
  k = k * 4ull + (unsigned long long)(s.dmg < 3 ? s.dmg : 3);
  k = k * 4ull + (unsigned long long)(s.sp < 3 ? s.sp : 3);
  u32 h = (u32)(k ^ (k >> 32)) * 2654435761u;
  return h ? h : 1u;
}
static inline bool hInsert(u32 k) {
  u32 h = k & HMASK;
  while (hgen[h] == curGen) {
    if (hkey[h] == k) return false;
    h = (h + 1) & HMASK;
  }
  hgen[h] = curGen;
  hkey[h] = k;
  return true;
}

static const int ACTS[9] = {0, 1, 2, 4, 5, 6, 8, 9, 10};
// A special jump ignores every ground condition, so pressing S each frame is
// flight at 3px/frame -- the only way out of a pit deeper than a 15px jump.
// It costs one denominator point per frame, but Cost is a min over time, so
// whatever we had banked before spending it can never be taken away.

static void reconstruct(int idx, vector<int> &plan) {
  plan.clear();
  while (idx > 0) { plan.push_back(nodes[idx].act); idx = nodes[idx].par; }
  reverse(plan.begin(), plan.end());
}

// closer to the guide field first, then ground we have stood on least (this is
// what breaks shaft oscillation), then damage taken.
static inline long long scoreState(const S &s) {
  int ry = (s.y + 3) / 6, rx = (s.x + 3) / 6;
  long long g = inb(ry, rx) ? gd[ry * M + rx] : INF;
  long long v = inb(ry, rx) ? (long long)min(visitCnt[ry * M + rx], 4000) : 4000LL;
  return g * 100000LL + v * VIS_SC + (long long)(s.dmg + s.sp) * DMG_SC;
}

// search order: guide distance dominates, then damage, then ground already
// trodden, then elapsed frames.
static inline long long prio(const S &s, int depth) {
  int ry = (s.y + 3) / 6, rx = (s.x + 3) / 6;
  long long g = inb(ry, rx) ? gd[ry * M + rx] : INF;
  long long v = inb(ry, rx) ? (long long)min(visitCnt[ry * M + rx], 400) : 400LL;
  return g * GUIDE_W + (long long)s.dmg * dmgEff + (long long)s.sp * specEff +
         v * VIS_W + depth;
}

// Greedy best-first, not plain BFS: a uniform frontier spends its whole node
// budget on breadth and never sees more than 4-5 frames ahead, which is not
// enough to leave a pocket. Ordering by the guide field lets a few thousand
// nodes reach a hundred frames down a corridor.
static bool planBFS(const S &root, bool allowDmg, int cap, int maxDepth,
                    bool exploreMode, bool allowSpec, vector<int> &plan) {
  nodes.clear();
  curGen++;
  if (curGen == 0) { fill(hgen.begin(), hgen.end(), 0u); curGen = 1; }
  BN rn; rn.s = root; rn.par = -1; rn.act = 0; rn.depth = 0;
  nodes.push_back(rn);
  hInsert(stKey(root));
  priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
  pq.push({prio(root, 0), 0});
  long long bestScore = scoreState(root);
  int bestDepth = 0, bestIdx = 0;
  while (!pq.empty() && (int)nodes.size() < cap) {
    int head = pq.top().second;
    pq.pop();
    BN cur = nodes[head];
    if (cur.depth >= maxDepth) continue;
    int nacts = allowSpec ? 9 : 6;
    for (int a = 0; a < nacts; a++) {
      S ns = cur.s;
      int got;
      if (simStep(ns, ACTS[a], allowDmg, got) < 0) continue;
      if (!hInsert(stKey(ns))) continue;
      BN nn; nn.s = ns; nn.par = head; nn.act = (short)ACTS[a]; nn.depth = cur.depth + 1;
      nodes.push_back(nn);
      int idx = (int)nodes.size() - 1;
      if (got) { reconstruct(idx, plan); return true; }
      if (exploreMode) {                       // stepping onto unseen ground is the goal
        int ry = (ns.y + 3) / 6, rx = (ns.x + 3) / 6;
        if (inb(ry, rx) && cellT[ry * M + rx] == UNK) { reconstruct(idx, plan); return true; }
      }
      long long sc = scoreState(ns);
      if (sc < bestScore || (sc == bestScore && nn.depth < bestDepth)) {
        bestScore = sc; bestDepth = nn.depth; bestIdx = idx;
      }
      pq.push({prio(ns, nn.depth), idx});
      if ((int)nodes.size() >= cap) break;
    }
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
  char buf[16], cs[4];
  int k = 0;
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
  const int BUDGET_MS = envInt("BUDGET_MS", 1200);
  const int OVERHEAD_NS = envInt("OVERHEAD_NS", 30000);
  const int NODE_CAP = envInt("NODE_CAP", 12000);
  const int MAX_DEPTH = envInt("MAX_DEPTH", 160);
  const int REPLAN_PERIOD = envInt("REPLAN_PERIOD", 12);
  const long long NS_PER_NODE = (long long)envInt("NS_PER_NODE", 140);
  DMG_COST = (long long)envInt("DMG_COST", 8000000);
  DMG_SC   = (long long)envInt("DMG_SC", 1);
  VIS_W    = (long long)envInt("VIS_W", 400);
  VIS_SC   = (long long)envInt("VIS_SC", 10);
  GUIDE_W  = (long long)envInt("GUIDE_W", 4000000);
  SHAKE_AT = envInt("SHAKE_AT", 60);
  shieldFirst = envInt("SHIELD_FIRST", 0);
  SPEC_COST = (long long)envInt("SPEC_COST", 8000000);
  specAfter = envInt("SPEC_AFTER", 120);
  optSupport = envInt("OPT_SUPPORT", 0);
  scaleByCmax = envInt("SCALE_CMAX", 0);
  refCmax = envInt("REF_CMAX", 8);
  specBudget = envInt("SPEC_BUDGET", 64);
  specGate = envInt("SPEC_GATE", 0);
  exploreBias = envInt("EXPLORE_BIAS", 0);
  const int PUSH_PIT = envInt("PUSH_PIT", 1);
  const int PUSH_TRIES = envInt("PUSH_TRIES", 3);

  string line;
  if (!getLine(line)) return 0;
  { istringstream is(line); if (!(is >> N >> M >> KIND)) return 0; }
  H = 6 * N; W = 6 * M;
  cellT.assign(N * M, UNK);
  seenStamp.assign(N * M, -1);
  visitCnt.assign(N * M, 0);
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

  S cur; cur.y = (short)cy; cur.x = (short)cx;
  cur.vy = cur.vx = cur.wg = cur.wj = cur.hold = cur.dmg = cur.sp = 0;
  cur.sh = (signed char)min(shields, 120);

  vector<int> plan;
  size_t planPos = 0;
  int actions = 0, sinceReplan = 1 << 20, noTargetStreak = 0, stuckCnt = 0;
  long long replans = 0;
  int lastY = cy, lastX = cx, prevCoins = coins, prevShields = shields;
  int noProgress = 0;
  unsigned rng = 12345u;

  while (true) {
    auto t0 = chrono::steady_clock::now();
    // the judge charges us wall time between its send and our reply, so allow for
    // per-frame pipe/scheduling overhead on top of our own measured compute.
    long long charged = usedNs + (long long)actions * (long long)OVERHEAD_NS;
    if (actions >= 10000 || charged > budgetNs) { finishNow(); return 0; }

    { int r = (cur.y + 3) / 6, c = (cur.x + 3) / 6; if (inb(r, c)) visitCnt[r * M + c]++; }

    bool needReplan = (planPos >= plan.size()) || (sinceReplan >= REPLAN_PERIOD) ||
                      (coins != prevCoins) || (shields != prevShields);
    if (needReplan) {
      heldShields = shields;
      priceByCoinValue(coins);
      int rc = (cur.y + 3) / 6, cc = (cur.x + 3) / 6;
      bool haveTargets = computeGuide(false);
      bool exploreMode = false;
      long long coinD = INF;
      if (haveTargets && inb(rc, cc)) coinD = gd[rc * M + cc];
      if (coinD >= INF) haveTargets = false;
      // A known coin normally outranks exploring. But on a 5621-cell Puzzle the
      // nearest coin can be far behind us while unseen ground -- and the coins in
      // it -- is a step away, so allow trading one for the other by ratio.
      if (haveTargets && exploreBias > 0) gdCoin = gd;
      bool resolved = haveTargets && exploreBias == 0;
      if (!resolved) {
        bool hasFront = computeGuide(true);
        long long frontD = (hasFront && inb(rc, cc)) ? (long long)gd[rc * M + cc] : INF;
        if (hasFront && frontD < INF &&
            (!haveTargets || frontD * 100 < coinD * exploreBias)) {
          exploreMode = true;
          resolved = true;
        } else if (haveTargets) {
          gd.swap(gdCoin);
          resolved = true;
        }
      }
      // Nothing left that ordinary movement can reach: we are sealed in a pit
      // deeper than a 15px jump. Special jump ignores every ground condition, so
      // re-derive the guide as if we could fly and let the planner buy its way
      // out. Cost is a min over time, so whatever we banked before is safe.
      bool needSpec = false;
      if (!resolved) {
        needSpec = true;
        flightGuide = 1;
        bool any = computeGuide(false);
        if (any && inb(rc, cc) && gd[rc * M + cc] < INF) exploreMode = false;
        else { any = computeGuide(true); exploreMode = true; }
        bool reach = any && inb(rc, cc) && gd[rc * M + cc] < INF;
        flightGuide = 0;
        if (!reach) { finishNow(); return 0; }
      }
      // spread whatever compute is left over the frames we may still play, so we
      // never burn the whole budget in the first few hundred frames.
      long long left = budgetNs - charged;
      int remainFrames = max(1, 10000 - actions);
      // budget per replan must use how often we ACTUALLY replan, not how often we
      // hoped to: plans get invalidated whenever unseen ground turns out to be a
      // wall, and assuming REPLAN_PERIOD there burnt the whole budget in 2339
      // frames of a 32x32 maze.
      replans++;
      long long period = max(1LL, (long long)actions / (long long)replans);
      long long perReplanNs = left / remainFrames * period;
      int cap = (int)(perReplanNs / NS_PER_NODE);
      cap = max(400, min(cap, NODE_CAP));
      cur.sh = (signed char)min(shields, 120);
      cur.dmg = 0;
      cur.sp = 0;
      plan.clear(); planPos = 0;
      bool ok = false;
      if (!needSpec) {
        ok = planBFS(cur, false, cap, MAX_DEPTH, exploreMode, false, plan);
        if (!ok || plan.empty())
          ok = planBFS(cur, true, cap, MAX_DEPTH, exploreMode, false, plan);
      }
      if ((needSpec || !ok || plan.empty()) && usedSpec < specBudget) {
        vector<int> spPlan;
        if (planBFS(cur, true, cap, MAX_DEPTH, exploreMode, true, spPlan) &&
            !spPlan.empty()) {
          int k = 0;
          for (int a : spPlan) if (a & 8) k++;
          // Spending k special-jump frames to win one more coin pays off only
          // while (c+1)/(cmax+s+k) > c/(cmax+s), i.e. k*c < cmax+s. On a 39-coin
          // Jump map that means ~zero: one wasted S frame is a whole rank.
          bool worth = true;
          if (specGate && k > 0 && coins > 0) {
            long long cmaxEst = coins;
            for (int i = 0; i < N * M; i++) if (cellT[i] == COIN) cmaxEst++;
            worth = (long long)k * (long long)coins < cmaxEst + (long long)usedSpec;
          }
          if (worth) { plan = spPlan; ok = true; }
        }
      }
      if (!ok || plan.empty()) {
        noTargetStreak++;
        if (noTargetStreak > 60) { finishNow(); return 0; }
      } else noTargetStreak = 0;
      sinceReplan = 0;
    }

    int cmd = 0;
    if (planPos < plan.size()) cmd = plan[planPos++];
    int proactivePush = (PUSH_PIT && stuckCnt < PUSH_TRIES) ? pitPushDir(cy, cx) : 0;
    if (proactivePush) { cmd = proactivePush; plan.clear(); planPos = 0; }
    if (SHAKE_AT > 0 && stuckCnt > SHAKE_AT) {   // wedged: hop at random to break out
      rng = rng * 1103515245u + 12345u;
      cmd = ACTS[(rng >> 16) % 6] | 4;
      plan.clear(); planPos = 0; stuckCnt = 0;
    }

    if (cmd & 8) usedSpec++;
    prevCoins = coins; prevShields = shields;
    int dummy;
    S pred = cur;
    simStep(pred, cmd, true, dummy);

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
    if (pred.y != cy || pred.x != cx) {        // divergence: resync and force a replan
      cur.y = (short)cy; cur.x = (short)cx;
      plan.clear(); planPos = 0;
    }
    if (coins != prevCoins || shields != prevShields) noProgress = 0;
    else noProgress++;
    if (cy == lastY && cx == lastX) stuckCnt++; else stuckCnt = 0;
    lastY = cy; lastX = cx;
    usedNs += chrono::duration_cast<chrono::nanoseconds>(chrono::steady_clock::now() - t1).count();
  }
}
