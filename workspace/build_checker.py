# 체커보드 라우터: 분배기 (r+c)짝수, 단방향 배송 나머지.
# 원리: 분배기끼리 비인접 -> peel이 단방향 칸에 안착 -> 혼잡해도 E=0.
#
# 꽃 i: 열 i에서 세로 캐스케이드. 분배기 셀은 행 parity==i. 각 분배기서 조각 peel.
# 조각은 배정된 굴 j로: 단방향 셀들로 수평 이동 후 하강.
# 배송은 전부 단방향(D/L/R) — 혼잡 안전.
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
    rng = random.Random(5); best = None; bestE = 1 << 60
    for _ in range(1000):
        order = allp[:]; rng.shuffle(order); order.sort(key=lambda x: -x[0])
        got = [0] * C; asn = {}
        for (p, i, k) in order:
            cs = [j for j in range(C) if abs(i - j) <= band]
            j = max(cs, key=lambda j: B[j] - got[j]); got[j] += p; asn[(i, k)] = j
        E = sum(abs(got[j] - B[j]) for j in range(C))
        if E < bestE: bestE, best = E, asn
        if E == 0: break
    return best, bestE


def build(idx, depth, band, deliv_rows):
    C, T, M, A, B = read_input(idx)
    asn, Eest = assign(A, B, C, depth, band)
    # 캐스케이드 영역: 각 꽃 분배기가 2행마다. depth 레벨 -> 2*depth 행 정도.
    CAS = 2 * depth
    R = CAS + deliv_rows
    g = [['X'] * C for _ in range(R)]

    # --- 배송영역(행 CAS..R-1): 각 열 단방향 D (굴로). ---
    for r in range(CAS, R):
        for c in range(C):
            g[r][c] = 'D'

    # --- 캐스케이드: 꽃 i, 열 i. 분배기는 로컬 레벨 l -> 실제행 rr=2*l+(i%2 맞춤).
    #     continue: 분배기 아래 단방향 D로 다음 분배기(2행 아래)까지.
    #     peel: 배정굴 j로 가려면, 먼저 인접 단방향칸으로 L/R, 그다음 그 열 아래로 내려
    #           배송영역서 수평정렬. 단순화: peel을 '배정굴 열'로 향하는 단방향 경로에 태움.
    # 구현: 분배기 셀 = 'DL' 또는 'DR' (continue=D 아래, peel= L/굴<i 또는 R/굴>i).
    #   peel이 간 인접열 칸을 '단방향 D'로 만들어 배송영역까지 하강 -> 배송영역서 그 열=굴.
    #   즉 조각이 인접열(i±1)로 가면 굴 i±1에 배송됨. band=1만 정확 지원.
    #   band>1은 배송영역서 추가 수평이동 필요(단방향) — 여기선 우선 band=1 측정.
    for i in range(C):
        if A[i] == 0:
            continue
        ps = pieces_of(A[i], depth)
        r = 0
        for l in range(len(ps) - 1):
            if r + 1 >= CAS:
                break
            j = asn.get((i, l), i)
            # 분배기 셀 (r,i)
            if j < i:
                g[r][i] = 'DL'
            elif j > i:
                g[r][i] = 'DR'
            else:
                g[r][i] = 'D'
            # continue 아래칸 (r+1,i) 단방향 D
            g[r + 1][i] = 'D'
            r += 2
        # remainder: 마지막 조각 -> 그냥 열 i 아래로(굴 i) 또는 배정
    # peel이 간 인접열의 그 행 칸을 D로 (배송영역까지 하강)
    for r in range(CAS):
        for c in range(C):
            if g[r][c] == 'X':
                g[r][c] = 'D'   # 빈칸은 단방향 하강(peel 받으면 아래로)
    return C, T, M, A, B, R, g, Eest


def evalgrid(C, T, M, A, B, R, g):
    cells = {(r + 1, c): V.parse_cell(g[r][c]) for r in range(R) for c in range(C)}
    Bp, tl, bnc, lf = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B) - sum(Bp); E = sum(abs(Bp[j] - B[j]) for j in range(C))
    D = (tl - M) if L == 0 else T
    cost = (1 << (R - C)) + max(E, D) + T * L
    return Bp, E, D, bnc, cost


if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    for depth in [6, 8]:
        for band in [1]:
            C, T, M, A, B, R, g, Eest = build(idx, depth, band, 3)
            Bp, E, D, bnc, cost = evalgrid(C, T, M, A, B, R, g)
            print(f"depth={depth} band={band}: 배정E={Eest} 실측E={E} D={D} 반송={bnc} cost={cost} R={R}")
            print(f"  B'={Bp}")
            print(f"  B ={B}")
