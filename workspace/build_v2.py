# 전체 라우터 v2 — 원리: 분배기(라운드로빈,혼잡X) + 배송(순수 단방향,혼잡해도 E=0).
#
# 레이아웃:
#   행 1..DCAS   : 꽃 i 세로 캐스케이드(열 i). continue=아래, peel=DL/DR로 조각을
#                  '즉시 아래 배송영역으로' 보내기 위해, peel은 인접열이 아니라
#                  햄스터로 배송영역(행 DCAS+1 이하)의 목표굴 열에 직접 투입.
#   배송영역     : 각 굴 j 열 = 단방향 'D' 수집(혼잡 안전). 조각은 그 열에 떨어져
#                  굴로 흐름. 열간 이동 필요시 단방향 L/R.
#
# peel을 목표굴 열로: 캐스케이드 셀에서 peel 방향(L/R)로 한 칸 뒤, 그 칸(단방향)에서
#   햄스터로 배송영역 목표열에 투입 — 복잡. v2 단순화:
#   '각 조각을, 캐스케이드가 끝난 뒤 배송영역에서 단방향 경로로 굴까지' 보내되,
#   캐스케이드 자체를 '열 i에서 아래로 내려가며 각 레벨 peel을 배송영역 진입점으로
#   단방향 하강'시킨다. 이를 위해 캐스케이드 continue를 '햄스터 2D'로 하여 홀수행을
#   비우고, 짝수행 peel이 그 빈칸(단방향)으로 내려가게 한다. (인터리브)
#
# 실제 구현은 아래. 측정 우선.
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V


def read_input(idx):
    d = open(f'inputs/input_{idx}.txt').read().split()
    it = iter(d); C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]; B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def pieces_of(N, depth):
    ps = []; s = N
    for _ in range(depth):
        if s <= 1: break
        pl = s // 2; ps.append(pl); s -= pl
    ps.append(s)
    return ps


def assign(A, B, C, depth, band):
    allp = [[p, i, k] for i, a in enumerate(A) for k, p in enumerate(pieces_of(a, depth))]
    rng = random.Random(3); best = None; bestE = 1 << 60
    for _ in range(800):
        order = allp[:]; rng.shuffle(order); order.sort(key=lambda x: -x[0])
        got = [0] * C; asn = {}
        for (p, i, k) in order:
            cs = [j for j in range(C) if abs(i - j) <= band]
            j = max(cs, key=lambda j: B[j] - got[j]); got[j] += p; asn[(i, k)] = j
        E = sum(abs(got[j] - B[j]) for j in range(C))
        if E < bestE: bestE, best = E, asn
        if E == 0: break
    return best, bestE


def build(idx, depth=8, band=2):
    """캐스케이드 열 i(짝수행 splitter, continue=2D 햄스터로 홀수행 skip),
    peel은 홀수행(단방향)으로 내려 배송영역으로. 배송영역서 단방향 L/R/D로 굴."""
    C, T, M, A, B = read_input(idx)
    asn, Eest = assign(A, B, C, depth, band)
    # 캐스케이드: 각 레벨 2행 사용(splitter행 + skip행). depth 레벨 -> 2*depth 행.
    DCAS = 2 * depth
    DELIV = C + 2      # 배송영역 행 수(넉넉히)
    R = DCAS + DELIV
    g = [['X'] * C for _ in range(R)]

    # 배송영역: 모든 열 단방향 D (굴로). 행 DCAS..R-1
    for r in range(DCAS, R):
        for c in range(C):
            g[r][c] = 'D'
    # 배송영역서 조각을 목표열로 옮기려면 단방향 L/R 필요 — 진입점을 목표열에 맞추면 불필요.

    # 캐스케이드: 열 i. splitter는 짝수 로컬행. continue = '2D' 햄스터(다음 splitter행).
    # peel은 배송영역 진입을 위해, splitter 셀에서 L/R로 한칸 이동 후 그 칸에서 아래로.
    # 단순·정확 위해: splitter 셀 = 'DL'/'DR'(1칸 peel) 대신, peel을 바로 아래 배송으로
    #   보내는 건 불가(continue가 아래). 그래서 continue를 '2D'로, peel을 'D'로.
    #   'D2D'? 다람쥐는 방향 문자만. 햄스터는 1거리방향. splitter는 다람쥐여야 분할.
    #   → splitter 다람쥐 'DR': D=continue(1아래), R=peel(1오른). 문제 여전.
    # 결론: 이 인터리브도 continue/peel 둘 다 아래로 못 보냄.
    # ⇒ v2도 근본 한계. 대신 '배송영역 진입'을 위해 peel을 R/L로 인접열에 두고,
    #   인접열의 그 행을 '단방향 D'로 만들어 배송영역까지 안전 하강.
    #   즉 캐스케이드 열과 '그 오른쪽 열'을 번갈아: 홀수열=캐스케이드, 짝수열=peel하강로.
    #   8열에 4캐스케이드밖에 안 들어감 → band로 커버 안 될 수 있음. 측정.
    return None


if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    C, T, M, A, B = read_input(idx)
    asn, E = assign(A, B, C, 8, 2)
    print(f"배정 E={E} (참고). 실제 배치는 인접열 peel하강 필요 — 다음 단계.")
