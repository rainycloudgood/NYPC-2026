# 조밀 흐름망 라우터: 격자를 위→아래 흐름으로 보고, 층별로 열 분포를 A→B로 변형.
# 각 셀은 라운드로빈(균등분할). 충돌 없음(모든 셀 아래로 흐름, 조밀 packing).
#
# 아이디어: 각 행에서 '현재 열 분포'를 목표(그 깊이의 보간 분포)로 밀기.
#   - 셀이 D면 자기 열 유지, DL/DR이면 절반을 옆으로.
#   - 마지막 행 아래 = 굴.
# 시뮬로 실측하여 E/D/cost 확인.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V


def read_input(idx):
    d = open(f'inputs/input_{idx}.txt').read().split()
    it = iter(d)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def design(C, A, B, R):
    """층별 구성: cur[c]=현재 열 c에 있어야 할 누적 유량(정수).
    각 행에서 cur를 목표 tgt로 밀도록 셀 방향 결정.
    tgt(r) = A에서 B로 선형 보간. 반환 grid."""
    g = [['D'] * C for _ in range(R)]  # 기본 전부 아래
    cur = A[:]  # 행 1 진입 시 열 분포(누적, 각 열 총량)
    for r in range(R):
        frac = (r + 1) / R
        tgt = [round(A[c] * (1 - frac) + B[c] * frac) for c in range(C)]
        # cur -> tgt 로 한 행에서 이동. 초과열->부족열로 절반씩(DL/DR) 밀기.
        # 간단 규칙: 각 열 c에서 넘치면 부족한 인접 방향으로 절반.
        newdir = ['D'] * C
        # 이동 필요량
        for c in range(C):
            over = cur[c] - tgt[c]
            if over > 5:
                # 어느 쪽이 더 부족한가
                left_need = (tgt[c - 1] - cur[c - 1]) if c > 0 else -1
                right_need = (tgt[c + 1] - cur[c + 1]) if c < C - 1 else -1
                if right_need >= left_need and right_need > 0:
                    newdir[c] = 'DR'
                elif left_need > 0:
                    newdir[c] = 'DL'
        # cur 갱신 (DR/DL은 절반 옆으로)
        nxt = [0] * C
        for c in range(C):
            if newdir[c] == 'DR':
                h = cur[c] // 2
                nxt[c] += cur[c] - h
                nxt[c + 1] += h
            elif newdir[c] == 'DL':
                h = cur[c] // 2
                nxt[c] += cur[c] - h
                nxt[c - 1] += h
            else:
                nxt[c] += cur[c]
        for c in range(C):
            g[r][c] = newdir[c]
        cur = nxt
    return g


def evalgrid(C, T, M, A, B, R, g):
    cells = {(r + 1, c): V.parse_cell(g[r][c]) for r in range(R) for c in range(C)}
    Bp, tl, bnc, lf = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B) - sum(Bp)
    E = sum(abs(Bp[j] - B[j]) for j in range(C))
    D = (tl - M) if L == 0 else T
    cost = (1 << (R - C)) + max(E, D) + T * L
    return Bp, E, D, bnc, cost


if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    C, T, M, A, B = read_input(idx)
    for R in [C, C + 1, C + 2, C + 3]:
        g = design(C, A, B, R)
        Bp, E, D, bnc, cost = evalgrid(C, T, M, A, B, R, g)
        print(f"R={R}: E={E} D={D} 반송={bnc} cost={cost}")
