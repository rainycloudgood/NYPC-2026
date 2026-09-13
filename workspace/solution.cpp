// 씨앗 운반 - 배치도 생성기 (대규모 데이터 대응 버전)
//
// 데이터 규모: C∈[5,10], ΣA=ΣB=1,000,000+C, M=max(A)∈[1e5,1e6], T=2,000,000
//
// 입력: C T M / A[0..C-1] / B[0..C-1]
// 출력: R / R줄 × C개 토큰
//
// 핵심 아이디어
// -------------
// 다람쥐의 방향 문자열은 씨앗 1개 처리마다 포인터가 1칸 전진하며 순환한다.
// 어떤 칸이 최종적으로 처리하는 씨앗의 총 개수 N은 (과부하가 없다면) 유량
// 보존으로 미리 정확히 계산할 수 있고, 그 칸이 옆으로 보내는 개수는
// "패턴 P를 무한 반복한 앞 N글자 중 옆방향 문자의 개수" — 즉 (P, N)만으로
// 결정되며 도착 타이밍과 무관하다. 따라서 짧은 주기 패턴 P로도 정확히
// Q개를 옆으로 보낼 수 있다:
//   k=len(P), a=N/k, m=N%k, P의 옆방향 문자 p개 중 x개를 앞 m칸에 배치하면
//   옆으로 보내는 총 개수 = a*p + x  (정확)
//
// 구조
// ----
// R = C (2^(R-C)=1 최소화). diff/prefix로 각 열 경계의 순유량 F[b]를 구하고,
// 같은 부호로 연속된 경계들을 run으로 묶어 경계마다 전용 행을 배정한다
// (오른쪽 run은 오름차순, 왼쪽 run은 내림차순 — 연쇄 이동의 의존성 때문).
// 경계 담당 칸만 위 패턴 분배기(splitter)이고 나머지는 전부 "D"×16 통과 칸.
// 통과 용량 16 > 최악 초당 부하(≤C+2)이므로 과부하가 원천적으로 없다.
//
// 분배기 칸의 통과량 N (정확한 정수):
//   오른쪽 경계 b (칸=열 b-1): N = A[b-1] + F[b-1]  (부호 포함! 위쪽 행에서
//     왼쪽 경계 b-1이 이 열에서 빼간 만큼 빼야 한다)
//   왼쪽 경계 b (칸=열 b): N = A[b] + (F[b+1]<0 ? -F[b+1] : 0)
//     (F[b+1]>0인 경우 그 분배기는 나중 run = 아래쪽 행이므로 영향 없음)
//
// 검증: 동일 로직의 Python 프로토타입을 문제 명세 그대로의 시뮬레이터
// (포인터 순환, 과부하/롤백, 굴 초당 1개 저장 포함)로 대조 — 스케일
// 3천/2만 규모 랜덤 케이스에서 전부 L=0, E=0, 과부하 0 확인.
// D(마지막 저장 지연)는 굴 대기열 때문에 스케일의 수 % 수준으로 남는데,
// 이는 이후 개선 여지(도착 시점 분산 최적화)가 있다.

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
