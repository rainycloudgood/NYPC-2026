// 씨앗 운반 국소탐색 최적화기 (C++ 포팅 — validate.py/optimizer.py와 동일 의미론)
//
// usage: seed_opt.exe <idx> <budget_sec> [focus_p=0.85] [congest_w=0.0] [seed_file]
//   inputs/input_<idx>.txt 읽고, seed_file(기본 outputs/output_<idx>.txt)에서 시작,
//   SA로 탐색해 개선되면 outputs/output_<idx>.txt 에 덮어씀(.bak 1회 백업).
//   stderr에 진행 로그.

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <fstream>
#include <random>
#include <sstream>
#include <string>
#include <vector>
#include <process.h>   // _getpid

using namespace std;

static int C, R, NC;
static long long T, M;
static vector<long long> A, B;

// 방향: U D L R
static inline void dirvec(char ch, int &dr, int &dc) {
    switch (ch) {
        case 'U': dr = -1; dc = 0; break;
        case 'D': dr = 1;  dc = 0; break;
        case 'L': dr = 0;  dc = -1; break;
        case 'R': dr = 0;  dc = 1; break;
        default:  dr = 0;  dc = 0; break;
    }
}

// 토큰 유효성 (validate.py valid_cell 과 동일)
static bool valid_cell(const string &tok, int r, int c) {
    auto inside = [&](int tr, int tc) {
        return 1 <= tr && tr <= R + 1 && 0 <= tc && tc < C;
    };
    if (tok == "X") return true;
    if (!tok.empty() && isdigit((unsigned char)tok[0])) {
        size_t i = 0;
        while (i < tok.size() && isdigit((unsigned char)tok[i])) i++;
        if (i == 0 || i + 1 != tok.size()) return false;
        char d = tok[i];
        if (d != 'U' && d != 'D' && d != 'L' && d != 'R') return false;
        long long dist = atoll(tok.substr(0, i).c_str());
        if (dist < 2) return false;
        int dr, dc; dirvec(d, dr, dc);
        int tr = r + dr * (int)dist, tc = c + dc * (int)dist;
        if (tr == 0) return false;
        return inside(tr, tc);
    }
    int seen = 0;
    for (char ch : tok) {
        if (ch != 'U' && ch != 'D' && ch != 'L' && ch != 'R') return false;
        int bit = (ch == 'U') ? 1 : (ch == 'D') ? 2 : (ch == 'L') ? 4 : 8;
        if (seen & bit) return false;
        seen |= bit;
        int dr, dc; dirvec(ch, dr, dc);
        int tr = r + dr, tc = c + dc;
        if (tr == 0) return false;
        if (!inside(tr, tc)) return false;
    }
    return true;
}

// 셀 토큰 → 목표 인덱스 리스트 (셀 0..NC-1, 굴 NC+c). cap=size. 'X'/빈 → cap 0.
static inline void parse_targets(const string &tok, int r, int c,
                                 int *tg, int &cap) {
    cap = 0;
    if (tok == "X" || tok.empty()) return;
    if (isdigit((unsigned char)tok[0])) {
        size_t i = 0;
        while (i < tok.size() && isdigit((unsigned char)tok[i])) i++;
        long long dist = atoll(tok.substr(0, i).c_str());
        int dr, dc; dirvec(tok[i], dr, dc);
        int tr = r + dr * (int)dist, tc = c + dc * (int)dist;
        tg[0] = (tr == R + 1) ? (NC + tc) : ((tr - 1) * C + tc);
        cap = 1;
        return;
    }
    for (char ch : tok) {
        int dr, dc; dirvec(ch, dr, dc);
        int tr = r + dr, tc = c + dc;
        tg[cap++] = (tr == R + 1) ? (NC + tc) : ((tr - 1) * C + tc);
    }
}

// 시뮬레이션 (validate.py simulate 와 동일). 반환 cost,E,D,bounces.
struct Res { long long cost, E, D, bounces; };

static Res simulate(const vector<string> &grid) {
    static vector<int> cap, tgt;       // tgt: NC*4 평면
    static vector<long long> cnt;
    static vector<int> ptr;
    cap.assign(NC, 0);
    tgt.assign((size_t)NC * 4, 0);
    for (int r = 1; r <= R; r++)
        for (int c = 0; c < C; c++) {
            int p = (r - 1) * C + c, k;
            parse_targets(grid[p], r, c, &tgt[(size_t)p * 4], k);
            cap[p] = k;
        }
    cnt.assign(NC + C, 0);
    ptr.assign(NC, 0);
    vector<long long> Bp(C, 0);
    long long t_last = 0, bounces = 0, tot_a = 0, dropped = 0;
    for (int i = 0; i < C; i++) tot_a += A[i];
    vector<long long> drop_from(C);
    for (int i = 0; i < C; i++) drop_from[i] = M - A[i] + 1;

    // recv: 목표별 송신자 리스트를 셀별 카운트로. senders 저장.
    vector<int> recv_cnt(NC + C, 0);
    vector<char> is_over(NC + C, 0);   // 반송 판정 스냅샷
    vector<int> touched;               // recv 이번 초 목표들
    vector<vector<int>> senders(NC + C); // 목표별 송신 셀

    for (long long t = 1; t <= T; t++) {
        bool anyq = false;
        for (int c = 0; c < C; c++) if (cnt[NC + c] > 0) { anyq = true; break; }
        if (dropped >= tot_a) {
            bool anynz = false;
            for (int i = 0; i < NC; i++) if (cnt[i] > 0) { anynz = true; break; }
            if (!anynz && !anyq) break;
        }
        // 1. 수확
        for (int i = 0; i < C; i++)
            if (A[i] > 0 && drop_from[i] <= t && t <= M) { cnt[i]++; dropped++; }
        // 2. 발송
        touched.clear();
        for (int p = 0; p < NC; p++) {
            long long s = cnt[p];
            int k = cap[p];
            if (s <= 0 || k == 0) continue;
            long long amt = s < k ? s : k;
            int *tg = &tgt[(size_t)p * 4];
            if (k == 1) {
                int d = tg[0];
                if (recv_cnt[d] == 0) touched.push_back(d);
                recv_cnt[d]++; senders[d].push_back(p);
            } else {
                int pp = ptr[p];
                for (long long j = 0; j < amt; j++) {
                    int d = tg[(pp + j) % k];
                    if (recv_cnt[d] == 0) touched.push_back(d);
                    recv_cnt[d]++; senders[d].push_back(p);
                }
                ptr[p] = (int)((pp + amt) % k);
            }
            cnt[p] = s - amt;
        }
        // 3. 받기: over = 발송 후 cnt>0 인 목표를 '반송 적용 전' 스냅샷으로 판정
        //    (반송이 뒤 목표의 판정을 오염시키면 안 됨 — validate.py와 동일)
        for (int d : touched) is_over[d] = (cnt[d] > 0);
        for (int d : touched) {
            if (is_over[d]) {                 // 과부하 → 반송
                bounces += recv_cnt[d];
                for (int snd : senders[d]) cnt[snd]++;
            } else {
                cnt[d] += recv_cnt[d];
            }
            recv_cnt[d] = 0;
            senders[d].clear();
        }
        // 4. 저장
        for (int c = 0; c < C; c++) {
            if (cnt[NC + c] > 0) { cnt[NC + c]--; Bp[c]++; t_last = t; }
        }
    }

    long long L = 0, E = 0;
    for (int i = 0; i < C; i++) { L += B[i] - Bp[i]; E += llabs(Bp[i] - B[i]); }
    long long D = (L == 0) ? (t_last - M) : T;
    long long cost = (1LL << (R - C)) + max(E, D) + T * L;
    return {cost, E, D, bounces};
}

// rank: (cost, D, E, bounces) 사전식
static inline bool rank_lt(const Res &a, const Res &b) {
    if (a.cost != b.cost) return a.cost < b.cost;
    if (a.D != b.D) return a.D < b.D;
    if (a.E != b.E) return a.E < b.E;
    return a.bounces < b.bounces;
}
static inline bool rank_le(const Res &a, const Res &b) {
    return !rank_lt(b, a);
}

static std::mt19937 rng;
static inline double urand() { return (double)rng() / 4294967296.0; }
static inline int irand(int n) { return (int)(rng() % (unsigned)n); }

// random_token (optimizer.py 와 동일)
static string random_token(int r, int c) {
    double x = urand();
    if (x < 0.5) {
        char ds[4]; int n = 0;
        ds[n++] = 'D';
        if (r >= 2) ds[n++] = 'U';
        if (c >= 1) ds[n++] = 'L';
        if (c <= C - 2) ds[n++] = 'R';
        int k = 1 + irand(n);
        // sample k distinct
        int idx[4]; for (int i = 0; i < n; i++) idx[i] = i;
        for (int i = 0; i < k; i++) { int j = i + irand(n - i); swap(idx[i], idx[j]); }
        string s; for (int i = 0; i < k; i++) s += ds[idx[i]];
        return s;
    }
    if (x < 0.85) {
        // opts
        static vector<pair<char,int>> opts; opts.clear();
        for (int d = 2; d <= R + 1 - r; d++) opts.push_back({'D', d});
        for (int d = 2; d <= r - 1; d++) opts.push_back({'U', d});
        for (int d = 2; d <= c; d++) opts.push_back({'L', d});
        for (int d = 2; d <= C - 1 - c; d++) opts.push_back({'R', d});
        if (opts.empty()) return "D";
        if (R + 1 - r >= 2 && urand() < 0.3) return to_string(R + 1 - r) + "D";
        auto pr = opts[irand((int)opts.size())];
        return to_string(pr.second) + string(1, pr.first);
    }
    if (x < 0.95) return "D";
    return "X";
}

static void mutate_one(vector<string> &cand, int p) {
    int r = p / C + 1, c = p % C;
    string tok = cand[p];
    double x = urand();
    if (x < 0.45) { cand[p] = random_token(r, c); return; }
    if (x < 0.60) {
        if (tok != "X" && !isdigit((unsigned char)tok[0]) && tok.size() > 1) {
            string ds = tok;
            for (int i = (int)ds.size() - 1; i > 0; i--) { int j = irand(i + 1); swap(ds[i], ds[j]); }
            if (ds.size() > 1 && urand() < 0.3) ds.pop_back();
            cand[p] = ds; return;
        }
        cand[p] = random_token(r, c); return;
    }
    if (x < 0.72) {
        if (tok != "X" && isdigit((unsigned char)tok[0])) {
            size_t i = 0; while (i < tok.size() && isdigit((unsigned char)tok[i])) i++;
            long long nd = atoll(tok.substr(0, i).c_str()) + (urand() < 0.5 ? 1 : -1);
            string c2 = to_string(nd) + tok.substr(i);
            if (nd >= 2 && valid_cell(c2, r, c)) { cand[p] = c2; return; }
        }
        cand[p] = random_token(r, c); return;
    }
    int q = irand(NC);
    int r2 = q / C + 1, c2 = q % C;
    if (x < 0.88) {
        string a = cand[p], b = cand[q];
        if (valid_cell(b, r, c) && valid_cell(a, r2, c2)) { cand[p] = b; cand[q] = a; return; }
    } else {
        if (valid_cell(cand[p], r2, c2)) { cand[q] = cand[p]; return; }
    }
    cand[p] = random_token(r, c);
}

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: seed_opt idx budget [focus_p] [congest_w] [seed]\n"); return 1; }
    int idx = atoi(argv[1]);
    double budget = atof(argv[2]);
    double focus_p = argc > 3 ? atof(argv[3]) : 0.85;
    double congest_w = argc > 4 ? atof(argv[4]) : 0.0;
    string seed_file = argc > 5 ? argv[5] : ("outputs/output_" + to_string(idx) + ".txt");

    // 입력
    {
        ifstream f("inputs/input_" + to_string(idx) + ".txt");
        if (!f) { fprintf(stderr, "no input\n"); return 1; }
        f >> C >> T >> M;
        A.resize(C); B.resize(C);
        for (auto &x : A) f >> x;
        for (auto &x : B) f >> x;
    }
    // 시드
    vector<string> body;
    {
        ifstream f(seed_file);
        if (!f) { fprintf(stderr, "no seed\n"); return 1; }
        f >> R;
        string t; while (f >> t) body.push_back(t);
    }
    NC = R * C;
    if ((int)body.size() != NC) { fprintf(stderr, "grid size mismatch %d vs %d\n", (int)body.size(), NC); return 1; }

    // focus hotspot (idx 15, R=8, C=8)
    vector<int> focus;
    if (idx == 15 && R == 8 && C == 8) {
        int hot[][2] = {{1,2},{1,4},{1,6},{1,7},{2,3},{2,4},{2,5},{2,7},{2,8},{3,4},{5,2},{6,1},{6,2},{7,2},{8,2},{8,3}};
        for (auto &h : hot) focus.push_back((h[0]-1)*C + (h[1]-1));
    }

    // 시드: 동시 실행 프로세스가 서로 다르도록 random_device + PID + 시각 혼합
    // (예전엔 시각만 써서 동시 런들이 같은 시드→같은 탐색을 반복하는 버그)
    std::random_device rd;
    unsigned seed = (unsigned)chrono::high_resolution_clock::now().time_since_epoch().count();
    seed ^= rd() * 2654435761u;
    seed ^= (unsigned)_getpid() * 40503u;
    seed ^= (unsigned)idx * 2246822519u;
    rng.seed(seed);

    vector<string> cur = body, best = body;
    Res cur_sc = simulate(cur), best_sc = cur_sc;
    fprintf(stderr, "[%d] 시드 cost=%lld E=%lld D=%lld\n", idx, cur_sc.cost, cur_sc.E, cur_sc.D);

    auto t0 = chrono::high_resolution_clock::now();
    long long it = 0, stall = 0;
    // T_HI(초기 온도)와 restart kick 강도를 인자로 (argv[7], argv[8])
    double T_HI = argc > 7 ? atof(argv[7]) : 3.0, T_LO = 0.02;
    int kick_lo = argc > 8 ? atoi(argv[8]) : 2;
    int kick_hi = kick_lo + 4;
    long long stall_limit = argc > 9 ? atoll(argv[9]) : 8000;
    double block_p = argc > 10 ? atof(argv[10]) : 0.0;  // 열/행 통째 재생성 확률
    vector<string> cand;
    while (true) {
        double el = chrono::duration<double>(chrono::high_resolution_clock::now() - t0).count();
        if (el >= budget) break;
        it++;
        double frac = el / budget; if (frac > 1) frac = 1;
        double temp = T_HI * pow(T_LO / T_HI, frac);
        cand = cur;
        if (block_p > 0 && urand() < block_p) {
            // 구조적 큰 이동: 한 열(또는 행) 전체를 무작위 재생성 → 다른 basin으로 점프
            if (urand() < 0.5) {
                int cc = irand(C);
                for (int r = 1; r <= R; r++) cand[(r - 1) * C + cc] = random_token(r, cc);
            } else {
                int rr2 = 1 + irand(R);
                for (int cc = 0; cc < C; cc++) cand[(rr2 - 1) * C + cc] = random_token(rr2, cc);
            }
        } else {
            double rr = urand();
            int nmut = (rr < 0.7) ? 1 : (urand() < 0.8 ? 2 : 3);
            for (int m = 0; m < nmut; m++) {
                int p = (!focus.empty() && urand() < focus_p) ? focus[irand((int)focus.size())] : irand(NC);
                mutate_one(cand, p);
            }
        }
        Res sc = simulate(cand);
        // 혼잡 가중 비교
        bool accept;
        // cr = (cost, congest_w*bounces, D, E, bounces)
        double cr_a[2] = {(double)sc.cost, congest_w * sc.bounces};
        double cr_b[2] = {(double)cur_sc.cost, congest_w * cur_sc.bounces};
        bool cr_le;
        if (cr_a[0] != cr_b[0]) cr_le = cr_a[0] < cr_b[0];
        else if (cr_a[1] != cr_b[1]) cr_le = cr_a[1] < cr_b[1];
        else if (sc.D != cur_sc.D) cr_le = sc.D < cur_sc.D;
        else if (sc.E != cur_sc.E) cr_le = sc.E < cur_sc.E;
        else cr_le = sc.bounces <= cur_sc.bounces;
        if (cr_le) accept = true;
        else {
            double d = (double)(sc.cost - cur_sc.cost) + congest_w * (sc.bounces - cur_sc.bounces)
                     + 0.001 * (sc.D - cur_sc.D) + 0.0005 * (sc.E - cur_sc.E);
            accept = (d < 12 * temp) && (urand() < exp(-max(d, 1e-9) / temp));
        }
        if (accept) {
            if (rank_lt(sc, cur_sc)) stall = 0;
            cur = cand; cur_sc = sc;
            if (rank_lt(sc, best_sc)) {
                best = cand; best_sc = sc;
                fprintf(stderr, "  개선: cost=%lld E=%lld D=%lld (%lld회, %.0fs)\n",
                        sc.cost, sc.E, sc.D, it, el);
            }
        } else {
            stall++;
            if (stall > stall_limit) {
                cur = best; cur_sc = best_sc;
                int kk = kick_lo + irand(kick_hi - kick_lo + 1);
                for (int m = 0; m < kk; m++) {
                    int p = (!focus.empty() && urand() < focus_p) ? focus[irand((int)focus.size())] : irand(NC);
                    mutate_one(cur, p);
                }
                cur_sc = simulate(cur);
                stall = 0;
            }
        }
    }

    // 항상 best를 자신만의 후보 파일에 기록 (동시성 안전: 파일 경쟁 없음).
    // 병합은 별도 단일 스레드 스크립트(merge_candidates.py)가 담당.
    // cand_path = argv[6] 있으면 그 경로, 없으면 outputs/_cand/cand_<idx>_<seed>.txt
    string cand_path = (argc > 6) ? string(argv[6])
        : ("outputs/_cand/cand_" + to_string(idx) + "_" + to_string(seed) + ".txt");
    ofstream f(cand_path);
    f << R << "\n";
    for (int r = 0; r < R; r++) {
        for (int c = 0; c < C; c++) { if (c) f << ' '; f << best[r * C + c]; }
        f << "\n";
    }
    fprintf(stderr, "[%d] best cost=%lld E=%lld D=%lld (%lld회) -> %s\n",
            idx, best_sc.cost, best_sc.E, best_sc.D, it, cand_path.c_str());
    printf("CAND %d cost=%lld iters=%lld\n", idx, best_sc.cost, it);
    return 0;
}
