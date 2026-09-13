# 정확 라우터 v1 (측정용): 꽃별 세로 캐스케이드 + 굴 전용 세로 수집열 + 레인 배송
#
# 목적: 물리적으로 E=0(정확)이 되는지, 그때 D(혼잡)가 얼마인지 '실제 시뮬'로 측정.
# R 압축은 나중. 지금은 achievable (E,D) 데이터포인트 확보가 목표.
#
# 레이아웃 (R = 1 + DCAS + DELIV):
#   행 1..DCAS  : 꽃 i의 캐스케이드 (열 i). 각 셀은 아래로 continue, 옆으로 peel.
#                 peel 조각은 배정된 굴 j로 가야 함.
#   배송        : 각 조각을 굴 j 열로 햄스터 수평 이동 후, 그 열을 타고 굴로.
#
# 단순·정확을 위해: 캐스케이드는 열 i에서 '아래=continue(D), 오른쪽=peel(R)' 대신
# peel도 아래로 보내되 배송열과 안 겹치게, 여기선 '굴 전용 배송은 맨 아래 행'으로.
# → 구현 단순화: 각 조각을 (그 조각이 마지막으로 있는 셀에서) 햄스터로 굴 열 꼭대기에
#   쏘고, 굴 열은 D로 내려보냄. 굴 열 = 캐스케이드 열과 같으므로 '전용 배송행'을 씀.
#
# 실제로는 아래 build()가 셀 단위로 명시 배치하고 validate.simulate로 측정.
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import validate as V


def read_input(idx):
    d = open(f'inputs/input_{idx}.txt').read().split()
    it = iter(d)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def cascade_pieces(N, depth):
    """세로 캐스케이드 peel 조각들 + 마지막 remainder. (크기, 그 조각이 나오는 레벨)."""
    ps = []
    s = N
    for lvl in range(depth):
        if s <= 1:
            break
        pl = s // 2
        ps.append((pl, lvl))   # 레벨 lvl에서 peel
        s -= pl
    ps.append((s, depth))      # remainder
    return ps


def assign_pieces(A, B, C, depth, band):
    """각 꽃의 조각을 |i-j|<=band 굴로 배정, E 최소 (그리디 다중시드)."""
    import random
    allp = []
    for i, a in enumerate(A):
        for (p, lvl) in cascade_pieces(a, depth):
            allp.append((p, i, lvl))
    rng = random.Random(12345)
    best = None
    best_E = 10**9
    for trial in range(400):
        order = allp[:]
        rng.shuffle(order)
        order.sort(key=lambda x: -x[0])
        got = [0] * C
        asn = {}
        for k, (p, i, lvl) in enumerate(order):
            cands = [j for j in range(C) if abs(i - j) <= band]
            j = max(cands, key=lambda j: B[j] - got[j])
            got[j] += p
            asn[(i, lvl, p)] = j
        E = sum(abs(got[k] - B[k]) for k in range(C))
        if E < best_E:
            best_E = E
            best = asn
        if E == 0:
            break
    return best, best_E


def build(idx, depth=8, band=2, extra_deliv=6):
    C, T, M, A, B = read_input(idx)
    asn, Eest = assign_pieces(A, B, C, depth, band)
    print(f'[build] 배정 E추정={Eest}', file=sys.stderr)

    DCAS = depth + 1           # 캐스케이드 행 수
    R = DCAS + extra_deliv     # 총 행
    grid = [['X'] * C for _ in range(R)]

    # 캐스케이드: 열 i, 행 1..DCAS. 각 레벨에서 아래=continue, 조각은 '그 셀에서 굴로 햄스터'.
    # 셀 (r,i): 만약 이 레벨 조각이 굴 j로 가야 하면, 그 조각을 굴로 보내려면
    #   - continue(아래로 절반)와 peel(굴로 절반)을 동시에 해야 함 → 다람쥐 2방향.
    #   문제: peel을 굴 j(열 j)로 보내려면 수평이동인데 다람쥐는 1칸씩.
    # 여기서는 '조각을 아래 배송행으로 떨구고, 배송행에서 수평정렬' 방식 대신
    #   단순화: peel을 바로 아래(D)로 보내되, continue를 오른쪽 하향 대각... 불가.
    #
    # === 정확·단순 버전: 캐스케이드 continue = 아래(D), peel = 위쪽?불가 →
    #   대신 continue = 오른쪽 아래로 못감. 따라서 v1은 'peel을 D, continue를 R'로 뒤집어
    #   캐스케이드가 오른쪽으로 진행하게 하고 각 열에서 아래로 조각을 떨군다.
    # 이 구현은 복잡하므로, 측정 우선을 위해 '이상적 배치 불가 시 X'로 두고
    #   최소한 유효한 격자를 만들어 E를 근사 측정하는 데 목적을 둔다.
    # (실제 배송 배선은 다음 반복에서 정교화)
    #
    # 지금은 배정 결과(Eest)만 신뢰 지표로 출력하고, 실제 격자 시뮬은 다음 단계.
    return R, grid, Eest


if __name__ == '__main__':
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    for depth in [6, 8, 10]:
        for band in [2, 3]:
            C, T, M, A, B = read_input(idx)
            asn, E = assign_pieces(A, B, C, depth, band)
            maxlvl = max(lvl for (i, lvl, p), j in asn.items()) if asn else 0
            print(f'depth={depth} band={band}: E={E}, 최대사용레벨={maxlvl}')
