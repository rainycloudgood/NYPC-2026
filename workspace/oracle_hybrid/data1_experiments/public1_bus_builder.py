# 데이터 1: 분할트리(상단) + "행=목표굴" 삼각 버스(하단) 구성기.
#
# 핵심 계약:  버스 행 (bus0+j) 는 굴 j 전용 레인.
#   - 대각 셀 (bus0+j, j) = 햄스터 드롭 -> 굴 j
#   - c<j 셀 = 'R' (대각으로 우측 유도),  c>j 셀 = 'L' (좌측 유도)
#   => 어느 열에서 이 행으로 씨앗을 떨어뜨려도 굴 j 로 배송된다 (열 무관).
# 따라서 분할영역은 가로배선이 전혀 필요 없다: 각 리프(굴 j)를 그 리프가
# 놓인 열에서 수직 햄스터로 버스행 (bus0+j) 에 떨궈주기만 하면 된다.
#
# R = split_rows + C.  2^(R-C) = 2^split_rows (버스 C행은 지수패널티에 상쇄).
# D 하한이 ~4600 이라 split_rows<=12(2^12=4096) 면 R항은 D에 묻힌다 -> 여유 큼.

import os, sys, random, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import treegen as TG  # plan_tree, partition_exact 재사용

DELTA = {'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


def build_bus(grid, bus0, C, R):
    for j in range(C):
        br = bus0 + j
        for c in range(C):
            if c == j:
                dist = R - br
                grid[br][c] = 'D' if dist == 1 else f'{dist}D'
            elif c < j:
                grid[br][c] = 'R'
            else:
                grid[br][c] = 'L'


class BusGrid:
    def __init__(self, C, R, bus0):
        self.C, self.R, self.bus0 = C, R, bus0
        self.g = [['X']*C for _ in range(R)]
        build_bus(self.g, bus0, C, R)
        self.budget = 20000

    def free(self, r, c):
        return 0 <= r < self.bus0 and 0 <= c < self.C and self.g[r][c] == 'X'

    def snap(self):
        return [row[:] for row in self.g]

    def restore(self, s):
        self.g = s


def place_leaf(gr, r, c, j):
    """리프(굴 j)를 (r,c)에서 버스행(bus0+j)으로 수직 드롭."""
    if not gr.free(r, c):
        return False
    dist = (gr.bus0 + j) - r
    if dist < 2:
        return False
    gr.g[r][c] = f'{dist}D'
    return True


def place_tree(gr, r, c, tree, rng):
    gr.budget -= 1
    if gr.budget < 0:
        return False
    if tree[0] == 'leaf':
        return place_leaf(gr, r, c, tree[1])
    _, sizes, children = tree
    if not gr.free(r, c):
        return False
    k = len(children)
    # 방향 집합: 하강 위주. D는 반드시 포함(깊이 확보), 나머지 L/R.
    dirsets = []
    if k == 2:
        if c+1 < gr.C:
            dirsets.append(('D', 'R'))
        if c-1 >= 0:
            dirsets.append(('D', 'L'))
        if c+1 < gr.C and False:
            pass
    else:  # k==3
        if c-1 >= 0 and c+1 < gr.C:
            dirsets.append(('D', 'L', 'R'))
    rng.shuffle(dirsets)
    for dset in dirsets:
        if not all(gr.free(r+DELTA[d][0], c+DELTA[d][1]) for d in dset):
            continue
        perms = list(itertools.permutations(dset))
        rng.shuffle(perms)
        for tok in perms:
            snap = gr.snap()
            gr.g[r][c] = ''.join(tok)
            ok = True
            for t, d in enumerate(tok):
                rr, cc = r+DELTA[d][0], c+DELTA[d][1]
                if not place_tree(gr, rr, cc, children[t], rng):
                    ok = False
                    break
            if ok:
                return True
            gr.restore(snap)
    # 릴레이: 아래 빈칸으로 스트림을 내려 재시도 (햄스터 하강)
    for r2 in range(r+1, gr.bus0):
        if gr.free(r2, c):
            snap = gr.snap()
            gr.g[r][c] = 'D' if r2 == r+1 else f'{r2-r}D'
            if place_tree(gr, r2, c, tree, rng):
                return True
            gr.restore(snap)
            break
    return False


def build(C, R, A, demands, seed):
    rng = random.Random(seed)
    bus0 = R - C
    gr = BusGrid(C, R, bus0)
    order = [i for i in range(C) if A[i] > 0]
    rng.shuffle(order)
    for i in order:
        tree = TG.plan_tree(A[i], [d[:] for d in demands[i]], rng)
        if not place_tree(gr, 0, i, tree, rng):
            return None
    return gr.g
