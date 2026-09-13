// ─────────────────────────────────────────────────────────────────────────
//  NYPC 2026 본선 — 범용 솔버 스켈레톤
//
//  당일 채울 곳은 [FILL] 표시된 곳뿐이다. 나머지(시간예산 강제배분·안전기준안
//  보존·축소선별 게이트·최선선택·출력)는 이미 동작한다.
//
//  설계 근거 (FINAL_ROUND_STRATEGY.md §2.2)
//   - 채점은 1코어 **CPU time**(모든 스레드 합산) → 멀티스레드는 이득이 0이고
//     오히려 손해다. 기본 단일스레드, 로컬 스윕만 -DUSE_THREADS
//   - 예산은 벽시계와 CPU time 을 **둘 다** 재서 먼저 닿는 쪽에서 끊는다
//   - 안전 기준안을 먼저 확보하고, 후보는 "실측이 더 낮을 때만" 교체 → 무효 위험 0
//   - 전 후보 정확평가는 비싸다 → 축소평가로 거르고 상위 K개만 정확평가
//   - 단계별 시간을 강제 배분 → 쉬워 보이는 입력에 과소비하지 않는다
//
//  빌드:  ./build.sh skeleton.cpp sol                 (제출용, 단일스레드)
//         g++ -std=gnu++20 -O2 -DUSE_THREADS -DLOG ...  (로컬 벤치마크용)
// ─────────────────────────────────────────────────────────────────────────
#include <algorithm>
#include <chrono>
#include <climits>
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#ifdef USE_THREADS
#include <atomic>
#include <thread>
#endif
using namespace std;
using ll = long long;

// ───────────────────── 환경변수 오버라이드 (스윕용) ─────────────────────
// run_batch.py 가 파라미터를 **환경변수**로 넘긴다. 재컴파일 없이 스윕하려면
// 튜닝 대상을 여기로 뺄 것. 값이 없으면 기본값을 쓰므로 제출본에서도 안전하다.
static int    envi(const char* k, int d)    { const char* v = getenv(k); return v ? atoi(v) : d; }
static double envd(const char* k, double d) { const char* v = getenv(k); return v ? atof(v) : d; }

// ───────────────────────────── 시간 예산 ─────────────────────────────
static const double TIME_LIMIT = envd("TIME_LIMIT", 2.000); // [FILL 0] 문제의 실행 시간제한(초)
static const double SAFETY     = envd("SAFETY", 0.85);      // 여유율 (I/O·출력 몫)
// 0.85 인 이유: 초과하면 그 입력이 무효(최악)이고, 여유는 탐색을 조금
// 손해볼 뿐이다. 위험이 비대칭이라 안전 쪽으로 잡는다.
// 리허설 실측 오버헤드는 ~0.004초였으나 채점기 사양은 미지수다.

// ⚠️ 채점은 **CPU time**(모든 스레드 합산) 기준이다. 벽시계가 아니다.
//    단일스레드면  벽시계 ≥ CPU time  이라 벽시계만 봐도 안전하지만,
//    스레드를 쓰는 순간  CPU time ≈ N × 벽시계  가 되어 관계가 뒤집힌다.
//    (타이머는 여유롭다고 믿는데 채점기는 초과 판정 → 그 입력 통째로 전손)
//    그래서 **둘 다 재고 먼저 닿는 쪽**에서 멈춘다. 어느 경우든 안전하다.
//    ※ MSVC 의 clock() 은 벽시계를 돌려주므로 윈도우에선 두 값이 같아진다(보수적).
struct Clock_ {
    chrono::steady_clock::time_point t0 = chrono::steady_clock::now();
    clock_t                          c0 = clock();

    double wall() const {
        return chrono::duration<double>(chrono::steady_clock::now() - t0).count();
    }
    double cpu() const {
        clock_t c = clock();
        if (c == (clock_t)-1) return 0.0;          // 측정 불가 → 벽시계에 맡긴다
        return double(c - c0) / CLOCKS_PER_SEC;
    }
    // 예산 판정값 — 보수적으로 더 큰 쪽
    double s() const { return max(wall(), cpu()); }
} CLK;

static const double BUDGET   = TIME_LIMIT * SAFETY;
static const double T_GEN    = BUDGET * 0.40;   // 후보 생성 마감
static const double T_SCREEN = BUDGET * 0.65;   // 축소 선별 마감
static const double T_EXACT  = BUDGET * 0.95;   // 정확 평가 마감
static const int    TOPK     = envi("TOPK", 4);      // 정확 평가할 상위 후보 수
static const int    FAMILIES = envi("FAMILIES", 2);  // [FILL] 후보 가족 수(안전형+공격형)

// ─────────────────────────── 문제 정의 [FILL] ───────────────────────────
struct Input {
    int n = 0;                    // [FILL 1] 문제 입력 필드로 교체
    vector<ll> a;
};

struct Cand {
    vector<int> plan;             // [FILL 2] 해의 표현으로 교체
    // ↓ 메타 (건드리지 말 것)
    int  family = -1;             // 어느 생성기에서 나왔나 (로깅용)
    ll   cheap  = LLONG_MAX;      // 축소 평가값
};

struct Score {
    bool valid = false;           // 유효성 — 무효면 절대 채택하지 않는다
    ll   cost  = LLONG_MAX;       // 낮을수록 좋음
};

// [FILL 3] 입력 읽기
static Input read_input(istream& in) {
    Input I;
    in >> I.n;
    I.a.resize(I.n);
    for (auto& x : I.a) in >> x;
    return I;
}

// [FILL 4] 안전 기준안 — **반드시 유효**해야 한다. 절대 실패하면 안 됨.
//          greedy / 항등 / 아무것도 안 하기 등 가장 단순한 것으로.
static Cand make_safe(const Input& I) {
    Cand c;
    c.family = -1;
    c.plan.assign(I.n, 0);
    return c;
}

// [FILL 5] 후보 생성. fam = 가족 번호, seed = 난수 시드. 못 만들면 false.
static bool gen_candidate(const Input& I, int fam, uint64_t seed, Cand& out) {
    mt19937_64 rng(seed);
    out.plan.assign(I.n, 0);
    for (auto& v : out.plan) v = int(rng() % 2);
    (void)fam;
    return true;
}

// [FILL 6] 평가. fidelity 0 = 축소(빠르고 대략), 1 = 정확(공식 규칙 그대로).
//          축소는 예: 시뮬 스텝을 1/4만 돌리기, 격자를 성기게 보기 등.
//          ★ fidelity 1 은 반드시 공식 채점기와 완전히 일치해야 한다.
//
//  ⚠️ 축소 평가의 품질이 전부다. 축소 순위와 정확 순위의 상관이 낮으면
//     선별이 오히려 해롭다(엉뚱한 후보만 정확평가하게 됨).
//     리허설에서 반드시 확인할 것:
//        후보 N개를 뽑아 축소/정확 둘 다 평가 → 순위 상관을 본다.
//        상관이 낮으면  -DNO_SCREEN 으로 빌드해 선별을 끄고
//        예산이 허락하는 만큼 정확평가만 돌리는 편이 낫다.
static Score evaluate(const Input& I, const Cand& C, int fidelity) {
    Score s;
    s.valid = true;
    ll acc = 0;
    int lim = fidelity ? I.n : max(1, I.n / 4);   // 축소: 일부만 계산
    for (int i = 0; i < lim; i++) acc += I.a[i] * C.plan[i];
    if (!fidelity) acc *= 4;                      // 축소값 스케일 보정
    s.cost = -acc;   // (더미) 큰 값을 많이 고를수록 좋다 → 후보가 안전안을 이긴다
    return s;
}

// [FILL 7] 출력
static void write_output(ostream& os, const Input& I, const Cand& C) {
    for (int i = 0; i < I.n; i++) os << C.plan[i] << (i + 1 == I.n ? '\n' : ' ');
}

// ───────────────────────── 드라이버 (수정 불필요) ─────────────────────────
static void screen(const Input& I, vector<Cand>& pool) {
#ifdef USE_THREADS
    atomic<size_t> next{0};
    unsigned nt = max(1u, thread::hardware_concurrency());
    nt = min<unsigned>(nt, (unsigned)pool.size());
    vector<thread> pool_t;
    for (unsigned w = 0; w < nt; w++)
        pool_t.emplace_back([&] {
            for (;;) {
                size_t i = next++;
                if (i >= pool.size()) break;
                if (CLK.s() > T_SCREEN) continue;         // 예산 초과분은 탈락
                Score s = evaluate(I, pool[i], 0);
                pool[i].cheap = s.valid ? s.cost : LLONG_MAX;
            }
        });
    for (auto& t : pool_t) t.join();
#else
    for (auto& c : pool) {
        if (CLK.s() > T_SCREEN) break;                    // 남은 건 LLONG_MAX 유지
        Score s = evaluate(I, c, 0);
        c.cheap = s.valid ? s.cost : LLONG_MAX;
    }
#endif
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    Input I = read_input(cin);

    // ① 안전 기준안 — 무슨 일이 있어도 이건 낼 수 있다
    Cand  best  = make_safe(I);
    Score bestS = evaluate(I, best, 1);
    if (!bestS.valid) bestS.cost = LLONG_MAX;   // 안전안조차 무효면 정의를 의심할 것

    // ② 후보 생성 (예산 내에서 가족별로 번갈아)
    vector<Cand> pool;
    for (int round = 0; CLK.s() < T_GEN && (int)pool.size() < 4096; round++) {
        bool any = false;
        for (int f = 0; f < FAMILIES && CLK.s() < T_GEN; f++) {
            Cand c;
            uint64_t seed = 0x9E3779B97F4A7C15ull * (uint64_t)(round * FAMILIES + f + 1);
            if (gen_candidate(I, f, seed, c)) { c.family = f; pool.push_back(move(c)); any = true; }
        }
        if (!any) break;
    }

#ifndef NO_SCREEN
    // ③ 축소 평가로 선별 (축소 지표가 정확 지표와 상관 높을 때만 이득)
    screen(I, pool);
    sort(pool.begin(), pool.end(),
         [](const Cand& x, const Cand& y) { return x.cheap < y.cheap; });
    const int EXACT_LIMIT = TOPK;
#else
    // 선별 없이 예산이 허락하는 만큼 정확평가 (축소 지표를 못 믿을 때)
    const int EXACT_LIMIT = INT_MAX;
#endif

    // ④ 정확 평가 — 안전안보다 실측이 낮을 때만 교체
    int exact_done = 0;
    for (auto& c : pool) {
        if (exact_done >= EXACT_LIMIT || CLK.s() > T_EXACT) break;
#ifndef NO_SCREEN
        if (c.cheap == LLONG_MAX) break;               // 이후는 전부 무효/미평가
#endif
        Score s = evaluate(I, c, 1);
        exact_done++;
        if (s.valid && s.cost < bestS.cost) { best = c; bestS = s; }
    }

    // ⑤ 출력 (항상 유효한 해)
    write_output(cout, I, best);

#ifdef LOG
    // 로컬 벤치마크용 지표 한 줄 (stderr — 채점 출력 오염 없음)
    // ★ key=value 형식 — run_batch.py 가 이 형식을 그대로 수집한다. 바꾸지 말 것.
    // ★ t_cpu 가 t_wall 보다 크면 스레드가 돌고 있다는 뜻 = 채점 기준으론 그만큼 쓴 것.
    //   제출본에서는 두 값이 거의 같아야 정상이다.
    cerr << "n=" << I.n << " family=" << best.family << " cand=" << pool.size()
         << " exact=" << exact_done << " cost=" << bestS.cost
         << " valid=" << (int)bestS.valid
         << " t_wall=" << CLK.wall() << " t_cpu=" << CLK.cpu() << '\n';
#endif
    return 0;
}
