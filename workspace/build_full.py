# 전체 정확 라우터 v1 — 세로 캐스케이드(검증된 프리미티브) 8꽃 배치.
#
# 레이아웃: 캐스케이드는 '홀수 열'에만, 수집은 '짝수 열' + 사이. 열이 모자라면
# 실제 test는 C=8 고정이므로 캐스케이드/수집을 행으로 분리한다:
#   - 각 꽃 i: (1,i)에서 햄스터로 캐스케이드 시작행까지 내림.
#   - 캐스케이드는 '자기 열'에서 세로로. 각 레벨 peel을 왼/오른 인접열로.
#   - peel이 인접열(다른 캐스케이드)과 충돌하면 → 그 조각 오염.
#   이 v1은 충돌 피해를 '측정'하는 것이 목적. 이후 햄스터 배송으로 교정.
#
# 더 정확히: peel을 인접열로 보내는 대신, 캐스케이드를 '충분히 벌려' 놓기 위해
# 각 꽃 캐스케이드를 서로 다른 '열 그룹'에 두는 건 8열에 불가.
# → v1은 '검증된 프리미티브를 그대로, 단 각 꽃을 순차 열에, peel은 D로 아래
#   배송행에 떨구고 배송행에서 햄스터로 굴 열로' 방식.
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V


def read_input(idx):
    d = open(f'inputs/input_{idx}.txt').read().split()
    it = iter(d)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def cascade_pieces(N, depth):
    ps = []; s = N
    for _ in range(depth):
        if s <= 1: break
        pl = s // 2
        ps.append(pl); s -= pl
    ps.append(s)
    return ps  # 마지막이 remainder


def assign(A, B, C, depth, band):
    allp = []
    for i, a in enumerate(A):
        for k, p in enumerate(cascade_pieces(a, depth)):
            allp.append([p, i, k])
    rng = random.Random(7)
    best = None; bestE = 1 << 60
    for _ in range(600):
        order = allp[:]; rng.shuffle(order); order.sort(key=lambda x: -x[0])
        got = [0]*C; asn = {}
        for (p, i, k) in order:
            cs = [j for j in range(C) if abs(i-j) <= band]
            j = max(cs, key=lambda j: B[j]-got[j]); got[j]+=p
            asn[(i, k)] = j
        E = sum(abs(got[j]-B[j]) for j in range(C))
        if E < bestE: bestE, best = E, asn
        if E == 0: break
    return best, bestE


def build(idx, depth, band):
    """검증된 세로 프리미티브: 꽃 i 캐스케이드를 열 i에.
    peel은 DL(왼굴)·DR(오른굴)로 인접 수집열에. |i-j|>1은 이 v1에선 근사(인접까지만).
    수집열은 각 열을 D로. (충돌: 인접열이 캐스케이드면 오염 → 측정)"""
    C, T, M, A, B = read_input(idx)
    asn, Eest = assign(A, B, C, depth, band)
    R = depth + 2
    g = [['X']*C for _ in range(R)]
    # 모든 열을 기본 D(수집) — 캐스케이드가 덮어씀
    for r in range(R):
        for c in range(C):
            g[r][c] = 'D'
    # 각 꽃 캐스케이드 배치
    for i in range(C):
        if A[i] == 0:
            continue
        pieces = cascade_pieces(A[i], depth)
        # 캐스케이드 열 i, 행 1..len(pieces)-1 (마지막 remainder는 continue로 굴 i행 흐름)
        for k in range(len(pieces)-1):
            j = asn.get((i, k), i)
            if j < i:
                g[k][i] = 'DL'   # 아래계속(ceil), 왼쪽 peel(floor)
            elif j > i:
                g[k][i] = 'DR'
            else:
                g[k][i] = 'D'    # 자기 굴: 그냥 아래로
        # remainder는 마지막 조각 -> asn[(i,len-1)] 굴로. continue가 열 i 아래로 감(굴 i).
        jl = asn.get((i, len(pieces)-1), i)
        # remainder 위치: 캐스케이드 끝 셀에서 처리. 간단화: 그대로 D(굴 i).
    return C, T, M, A, B, R, g, Eest


def evalgrid(C, T, M, A, B, R, g):
    cells = {(r+1, c): V.parse_cell(g[r][c]) for r in range(R) for c in range(C)}
    Bp, tl, bnc, lf = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B)-sum(Bp); E = sum(abs(Bp[j]-B[j]) for j in range(C))
    D = (tl-M) if L == 0 else T
    cost = (1 << (R-C)) + max(E, D) + T*L
    return Bp, E, D, bnc, cost


if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    band = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    C, T, M, A, B, R, g, Eest = build(idx, depth, band)
    Bp, E, D, bnc, cost = evalgrid(C, T, M, A, B, R, g)
    print(f"배정E추정={Eest}  실측: E={E} D={D} 반송={bnc} cost={cost} (R={R})")
    print(f"B'={Bp}")
    print(f"B ={B}")
