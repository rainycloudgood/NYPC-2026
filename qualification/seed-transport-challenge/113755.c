#include <algorithm>
#include <cassert>
#include <iostream>
#include <numeric>
#include <string>
#include <utility>
#include <vector>

using namespace std;

static const int W_PASS = 16;  // 통과 칸 "D" 반복 수 (용량)
static const int MIN_K = 16;   // 분배기 최소 패턴 길이
static const int KMAX = 4000;  // 분배기 기본 최대 패턴 길이

static int sign(long long x) {
    if (x > 0) return 1;
    if (x < 0) return -1;
    return 0;
}

// 패턴 앞 m칸에 minority x개, 뒤 (k-m)칸에 (p-x)개를 배치해 만든 문자열
static string arrange(long long k, long long m, long long x, long long p,
                      char mino, char majo) {
    string s;
    s.reserve((size_t)k);
    s.append((size_t)x, mino);
    s.append((size_t)(m - x), majo);
    s.append((size_t)(p - x), mino);
    s.append((size_t)((k - m) - (p - x)), majo);
    return s;
}

// N개 처리 중 정확히 Q개를 lat 방향으로, 나머지를 D로 보내는 패턴 생성
static string findPattern(long long N, long long Q, char lat) {
    assert(0 <= Q && Q <= N);
    if (N <= KMAX) {
        // 정확히 한 바퀴만 도므로 버스트를 그대로 사용 가능
        string s;
        s.append((size_t)Q, lat);
        s.append((size_t)(N - Q), 'D');
        return s;
    }
    for (long long k = KMAX; k >= MIN_K; k--) {
        long long a = N / k, m = N % k;
        if (a == 0) continue;
        long long base = Q / a;
        long long cand[3] = {base, base + 1, base - 1};
        for (long long p : cand) {
            if (p < 0 || p > k) continue;
            long long x = Q - p * a;
            if (x < 0 || x > m || x > p) continue;
            if ((p - x) > (k - m)) continue;
            return arrange(k, m, x, p, lat, 'D');
        }
    }
    // 극단적 Q(0이나 N에 매우 근접): 소수(minority) 문자 개수를 기준으로
    // 패턴을 잡는다. k ~ N*p/target 로 버스트(N)보다 항상 짧거나 같다.
    long long target;
    char mino, majo;
    if (Q <= N - Q) {
        target = Q; mino = lat; majo = 'D';
    } else {
        target = N - Q; mino = 'D'; majo = lat;
    }
    if (target == 0) return string((size_t)MIN_K, majo);
    for (long long p = 1; p <= 4096; p++) {
        long long a = target / p;
        if (a == 0) break;
        long long x = target - p * a;
        long long lo = N / (a + 1) + 1;  // floor(N/k)==a 가 되는 k 범위
        long long hi = N / a;
        long long cand[3] = {hi, max(lo, (long long)MIN_K), (lo + hi) / 2};
        for (long long k : cand) {
            if (k < max(p, (long long)MIN_K) || k < lo || k > hi) continue;
            long long m = N - a * k;
            if (x <= m && x <= p && (p - x) <= (k - m)) {
                return arrange(k, m, x, p, mino, majo);
            }
        }
    }
    // 최후 수단: 버스트 (길지만 항상 정확)
    string s;
    s.append((size_t)Q, lat);
    s.append((size_t)(N - Q), 'D');
    return s;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int C;
    long long T, M;
    if (!(cin >> C >> T >> M)) return 0;
    vector<long long> A(C), B(C);
    for (auto &x : A) cin >> x;
    for (auto &x : B) cin >> x;
    (void)T;
    (void)M;

    int R = C;

    // F[b] = 경계 b(열 b-1 와 열 b 사이, 1<=b<=C-1)를 지나는 순유량 (+: 오른쪽)
    vector<long long> F(C + 1, 0);
    {
        long long s = 0;
        for (int i = 0; i < C - 1; i++) {
            s += A[i] - B[i];
            F[i + 1] = s;
        }
    }

    // 같은 부호 연속 경계 → run. run마다 행 블록 배정.
    vector<int> rowOf(C + 1, -1);
    {
        int nextRow = 1;
        int b = 1;
        while (b <= C - 1) {
            if (F[b] == 0) { b++; continue; }
            int sg = sign(F[b]);
            int start = b;
            while (b + 1 <= C - 1 && F[b + 1] != 0 && sign(F[b + 1]) == sg) b++;
            int len = b - start + 1;
            if (sg > 0) {
                for (int k = 0; k < len; k++) rowOf[start + k] = nextRow + k;
            } else {
                for (int k = 0; k < len; k++) rowOf[b - k] = nextRow + k;
            }
            nextRow += len;
            b++;
        }
    }

    vector<vector<string>> grid(R, vector<string>(C, string(W_PASS, 'D')));

    for (int bb = 1; bb <= C - 1; bb++) {
        int r = rowOf[bb];
        if (r < 0) continue;
        int col;
        long long Q, N;
        char lat;
        if (F[bb] > 0) {
            col = bb - 1;
            Q = F[bb];
            N = A[col] + (bb - 1 >= 1 ? F[bb - 1] : 0);  // 부호 포함
            lat = 'R';
        } else {
            col = bb;
            Q = -F[bb];
            N = A[col] + (bb + 1 <= C - 1 && F[bb + 1] < 0 ? -F[bb + 1] : 0);
            lat = 'L';
        }
        grid[r - 1][col] = findPattern(N, Q, lat);
    }

    cout << R << '\n';
    for (int r = 0; r < R; r++) {
        for (int c = 0; c < C; c++) {
            if (c) cout << ' ';
            cout << grid[r][c];
        }
        cout << '\n';
    }
    return 0;
}
