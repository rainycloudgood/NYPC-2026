# 씨앗 운반 챌린지(대규모) - 분할 트리 생성기
#
# usage: python bigtree.py <입력파일> <출력파일> [배치시도수=2000] [심시도수=3]
#
# 스텝업 treegen과 같은 원리(HANDOFF.md 2장)를 대규모에 적용:
#  * E=0: 다람쥐 분배기의 ceil/floor 정확성은 N=40만에서도 성립.
#  * D≈트리깊이+홉: 모든 배선은 단방향 장치(반송 안전) + 굴 유입률 합 ≤ 1.
#  * 굴 유입률 제약을 지키기 위해 수송 계획을 "큰 굴 <- 큰 꽃" 순 그리디로
#    세움 (유량비율 X_ij 합이 굴마다 1을 넘지 않게 예산 관리).
#  * T=2e6 시뮬은 회당 수 분 → 배치는 시뮬 없이 다수 생성, 휴리스틱(깊이)으로
#    고른 소수 후보만 시뮬로 실측해 최종 선택.

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V
from treegen import Grid, place_stream, plan_tree


def read_file(path):
    data = open(path).read().split()
    it = iter(data)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def rate_transport(C, A, B):
    """굴 유입률 제약(합<=1)을 고려한 수송 계획.
    큰 굴부터, 남은 꽃 중 큰 것부터 채운다 (큰 꽃 = 낮은 비율 비용).
    반환: g[i] = [(j, amt), ...], 그리고 굴별 비율 합."""
    remA = A[:]
    g = [[] for _ in range(C)]
    rate = [0.0] * C
    for j in sorted(range(C), key=lambda j: -B[j]):
        need = B[j]
        while need > 0:
            # 남은 양이 있는 꽃 중 A가 가장 큰 것
            cands = [i for i in range(C) if remA[i] > 0]
            if not cands:
                break
            i = max(cands, key=lambda i: remA[i])
            take = min(remA[i], need)
            g[i].append([j, take])
            remA[i] -= take
            rate[j] += take / A[i]
            need -= take
    return g, rate


def tree_stats(tree, depth=0):
    if tree[0] == 'leaf':
        return depth, 1
    _, sizes, children = tree
    mx, leaves = 0, 0
    for ch in children:
        d, l = tree_stats(ch, depth + 1)
        mx = max(mx, d)
        leaves += l
    return mx, leaves


def build_once(C, A, B, R, rng, g):
    gr = Grid(C, R)
    order = sorted((i for i in range(C) if A[i] > 0),
                   key=lambda i: -len(g[i]))  # 파트 많은(복잡한) 트리 먼저
    maxdepth = 0
    for i in order:
        tree = plan_tree(A[i], [d[:] for d in g[i]], rng)
        d, _ = tree_stats(tree)
        maxdepth = max(maxdepth, d)
        if not place_stream(gr, 0, i, tree, rng):
            return None, None
    return gr.g, maxdepth


def simulate_grid(C, T, M, A, B, R, grid):
    cells = {}
    for r in range(1, R + 1):
        for c in range(C):
            tok = grid[r - 1][c]
            ok, why = V.valid_cell(tok, r, c, R, C)
            if not ok:
                return None
            cells[(r, c)] = V.parse_cell(tok)
    Bp, t_last, bounces, leftover = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B) - sum(Bp)
    E = sum(abs(Bp[i] - B[i]) for i in range(C))
    D = T if L > 0 else t_last - M
    cost = (1 << (R - C)) + max(E, D) + T * L
    return cost, E, D, bounces


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    tries = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    sims = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    C, T, M, A, B = read_file(in_path)

    g, rate = rate_transport(C, A, B)
    print(f'수송 계획: 파트 {sum(len(x) for x in g)}개, '
          f'굴별 유입률 최대 {max(rate):.3f}', file=sys.stderr)
    if max(rate) > 1.0 + 1e-9:
        print('경고: 유입률 1 초과 굴 존재 — D가 커질 수 있음', file=sys.stderr)

    rng = random.Random(20260711)
    # 배치 후보 생성 (시뮬 없이): (maxdepth, R) 낮은 순으로 상위 후보 유지
    cands = []
    t0 = time.time()
    for R in range(C, C + 9):
        got = 0
        for _ in range(tries):
            grid, md = build_once(C, A, B, R, rng, g)
            if grid is None:
                continue
            cands.append((md, R, grid))
            got += 1
            if got >= 30:
                break
        if got and R >= C + 2:
            break  # 낮은 R에서 충분히 얻으면 종료
    if not cands:
        print('배치 실패', file=sys.stderr)
        sys.exit(1)
    cands.sort(key=lambda x: (x[1] - C, x[0]))  # R 작은 것, 깊이 얕은 것
    print(f'배치 후보 {len(cands)}개 (탐색 {time.time() - t0:.0f}s), '
          f'상위 {sims}개 시뮬 검증', file=sys.stderr)

    best = None
    for md, R, grid in cands[:sims]:
        t1 = time.time()
        res = simulate_grid(C, T, M, A, B, R, grid)
        if res is None:
            continue
        cost, E, D, bounces = res
        print(f'  R={R} depth={md}: cost={cost} E={E} D={D} '
              f'bounces={bounces} ({time.time() - t1:.0f}s)', file=sys.stderr)
        if best is None or cost < best[0]:
            best = (cost, R, grid, res)

    if best is None:
        print('시뮬 검증 실패', file=sys.stderr)
        sys.exit(1)
    cost, R, grid, res = best

    # 기존 출력과 비교
    old_cost = None
    if os.path.exists(out_path):
        try:
            out = open(out_path).read().split()
            oR = int(out[0])
            og = [[out[1 + r * C + c] for c in range(C)] for r in range(oR)]
            oe = simulate_grid(C, T, M, A, B, oR, og)
            old_cost = oe[0] if oe else None
        except Exception:
            old_cost = None
    if old_cost is None or cost < old_cost:
        with open(out_path, 'w') as f:
            f.write(str(R) + '\n')
            for row in grid:
                f.write(' '.join(row) + '\n')
        print(f'갱신: {old_cost} -> {cost}', file=sys.stderr)
    else:
        print(f'기존({old_cost})이 더 좋음 — 유지 (신규 {cost})', file=sys.stderr)


if __name__ == '__main__':
    main()
