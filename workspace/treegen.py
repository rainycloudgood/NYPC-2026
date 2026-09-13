# 씨앗 운반 - 재귀 분할 트리 생성기 v2 (E=0 목표)
#
# usage: python treegen.py <테스트번호> [시도횟수=400]
#
# 원리:
#  * 다람쥐 k방향 분배기는 스트림 N을 각 방향에 ceil/floor(N/k)씩 정확 분배
#    (커서 첫 방향부터 N%k개 방향이 ceil). 2방향(DR형)과 3방향(DLR형) 사용.
#  * 노드의 수요집합을 부분합 DP(안 되면 수요를 쪼개서라도)로 크기가 정확히
#    맞는 그룹들로 나눠 재귀 → 리프에서 굴로 배송 → E = 0 보장.
#  * 분배기를 놓을 자리가 좁으면 릴레이(단방향 다람쥐/햄스터)로 빈 칸까지
#    스트림을 옮긴 뒤 설치. 배선은 전부 단방향 장치 → 반송돼도 개수 보존.
#  * 기하 배치는 랜덤 재시도 + 공식 의미론 시뮬레이터 실측으로 선택.

import os
import random
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V

IN_DIR = r'C:\Users\<user>\Downloads'
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')


def read_input(i):
    path = os.path.join(IN_DIR, f'input_{i}.txt')
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'inputs', f'input_{i}.txt')
    data = open(path).read().split()
    it = iter(data)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def transport(C, A, B):
    g = [[] for _ in range(C)]
    i = j = 0
    ai, bj = A[0], B[0]
    while i < C and j < C:
        m = min(ai, bj)
        if m > 0:
            g[i].append([j, m])
        ai -= m
        bj -= m
        if ai == 0:
            i += 1
            ai = A[i] if i < C else 0
        if bj == 0:
            j += 1
            bj = B[j] if j < C else 0
    return g


# ---------------------------------------------------------------- split plan
def partition_exact(demands, sizes, rng):
    """demands를 합이 정확히 sizes[k]인 그룹들로 분할 (필요시 수요 쪼개기).
    반환: 그룹 리스트 (sizes 순서)."""
    groups = []
    rem = [d[:] for d in demands]
    for si, size in enumerate(sizes):
        if si == len(sizes) - 1:
            groups.append(rem)
            return groups
        # 부분합 DP: 정확히 size가 되는 부분집합
        n = len(rem)
        reach = {0: 0}
        for idx in range(n):
            a = rem[idx][1]
            new = dict(reach)
            for s, mk in reach.items():
                s2 = s + a
                if s2 <= size and s2 not in new:
                    new[s2] = mk | (1 << idx)
            reach = new
        if size in reach:
            mk = reach[size]
            grp = [rem[k] for k in range(n) if mk >> k & 1]
            rem = [rem[k] for k in range(n) if not mk >> k & 1]
        else:
            items = sorted(rem, key=lambda d: -d[1])
            rng.shuffle(items)
            items.sort(key=lambda d: -d[1])
            grp, rest, cur = [], [], 0
            for j, a in items:
                if cur + a <= size:
                    grp.append([j, a])
                    cur += a
                elif cur < size:
                    grp.append([j, size - cur])
                    rest.append([j, a - (size - cur)])
                    cur = size
                else:
                    rest.append([j, a])
            rem = rest
        groups.append(grp)
    return groups


def plan_tree(N, demands, rng, allow3=True):
    """반환: ('leaf', j) | ('split', [child_tree...])  (children은 ceil부터,
    크기 내림차순 — 커서 첫 방향부터 배정)."""
    demands = [d for d in demands if d[1] > 0]
    if len(demands) == 1:
        return ('leaf', demands[0][0])
    # 3방향 분배는 수요 2개(예: 334+166 = 167+167+166)에도 유효 — 깊이 급감
    k = 3 if (allow3 and N >= 3 and rng.random() < 0.55) else 2
    q, m = divmod(N, k)
    if q == 0:
        k = 2
        q, m = divmod(N, k)
    sizes = [q + 1] * m + [q] * (k - m)
    groups = partition_exact(demands, sizes, rng)
    children = [plan_tree(sizes[t], groups[t], rng, allow3)
                for t in range(len(sizes))]
    return ('split', sizes, children)


# ------------------------------------------------------------------ builder
class Grid:
    def __init__(self, C, R):
        self.C, self.R = C, R
        self.g = [['X'] * C for _ in range(R)]
        # 한 후보가 기하 백트래킹에 무한히 가까운 시간을 쓰지 않도록 제한.
        self.search_left = 4000

    def free(self, r, c):
        return 0 <= r < self.R and 0 <= c < self.C and self.g[r][c] == 'X'

    def snap(self):
        return [row[:] for row in self.g]

    def restore(self, s):
        self.g = [row[:] for row in s]


def route_to_burrow(gr, r, c, j, rng):
    R = gr.R
    if not gr.free(r, c):
        return False
    if c == j:
        dist = R - r
        gr.g[r][c] = 'D' if dist == 1 else f'{dist}D'
        return True
    dist = abs(j - c)
    dirc = 'R' if j > c else 'L'
    if gr.free(r, j):
        gr.g[r][c] = dirc if dist == 1 else f'{dist}{dirc}'
        dd = R - r
        gr.g[r][j] = 'D' if dd == 1 else f'{dd}D'
        return True
    rows = list(range(r + 1, R))
    rng.shuffle(rows)
    for r2 in rows:
        if gr.free(r2, c) and gr.free(r2, j):
            d1 = r2 - r
            gr.g[r][c] = 'D' if d1 == 1 else f'{d1}D'
            gr.g[r2][c] = dirc if dist == 1 else f'{dist}{dirc}'
            dd = R - r2
            gr.g[r2][j] = 'D' if dd == 1 else f'{dd}D'
            return True
    return False


def place_stream(gr, r, c, tree, rng, relay=3):
    """(r,c)에 도착하는 스트림에 tree를 배치. 실패 시 False(격자 복원은
    호출측 스냅샷으로)."""
    gr.search_left -= 1
    if gr.search_left < 0:
        return False
    if tree[0] == 'leaf':
        return route_to_burrow(gr, r, c, tree[1], rng)
    _, sizes, children = tree
    k = len(children)
    if not gr.free(r, c):
        return False

    # 이 칸에 분배기 설치 시도.
    # 커서 규칙: 토큰의 t번째 방향이 t번째 몫을 받음 (앞쪽 N%k개 방향이 ceil).
    # children/sizes는 크기 내림차순이므로, 방향 집합의 순열 각각에 대해
    # "토큰 t번째 방향 <- children[t]" 로 배정하면 정합.
    import itertools
    dirsets = []
    if k == 2:
        if c + 1 < gr.C:
            dirsets.append(('D', 'R'))
        if c - 1 >= 0:
            dirsets.append(('D', 'L'))
    else:  # k == 3
        if c - 1 >= 0 and c + 1 < gr.C:
            dirsets.append(('D', 'L', 'R'))
    rng.shuffle(dirsets)

    DELTA = {'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
    for dset in dirsets:
        cells_ok = all(gr.free(r + DELTA[d][0], c + DELTA[d][1]) for d in dset)
        if not cells_ok:
            continue
        perms = list(itertools.permutations(dset))
        rng.shuffle(perms)
        for tok_dirs in perms:
            snap = gr.snap()
            gr.g[r][c] = ''.join(tok_dirs)
            ok = True
            for t, d in enumerate(tok_dirs):
                rr, cc = r + DELTA[d][0], c + DELTA[d][1]
                if not place_stream(gr, rr, cc, children[t], rng, relay):
                    ok = False
                    break
            if ok:
                return True
            gr.restore(snap)

    if relay <= 0:
        return False
    # 릴레이: 아래 or 옆의 빈 칸으로 스트림을 옮긴 뒤 재시도
    cands = []
    for r2 in range(r + 1, gr.R):
        cands.append((r2, c, ('D' if r2 == r + 1 else f'{r2 - r}D')))
    for c2 in range(gr.C):
        if c2 != c:
            d = abs(c2 - c)
            dirc = 'R' if c2 > c else 'L'
            cands.append((r, c2, (dirc if d == 1 else f'{d}{dirc}')))
    rng.shuffle(cands)
    for r2, c2, tok in cands[:12]:
        if not gr.free(r2, c2):
            continue
        snap = gr.snap()
        gr.g[r][c] = tok
        if place_stream(gr, r2, c2, tree, rng, relay - 1):
            return True
        gr.restore(snap)
    return False


def build(C, T, M, A, B, R, rng):
    g = transport(C, A, B)
    gr = Grid(C, R)
    order = [i for i in range(C) if A[i] > 0]
    rng.shuffle(order)
    for i in order:
        tree = plan_tree(A[i], [d[:] for d in g[i]], rng)
        if not place_stream(gr, 0, i, tree, rng):
            return None
    return gr.g


def evaluate(C, T, M, A, B, R, grid):
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


def solve(idx, tries=400, max_delta=20):
    C, T, M, A, B = read_input(idx)
    rng = random.Random(1234 + idx)
    best = None
    for R in range(C, C + max_delta + 1):
        base = 1 << (R - C)
        if best is not None and base >= best[0]:
            break
        if base > 4096:
            break
        for _ in range(tries):
            grid = build(C, T, M, A, B, R, rng)
            if grid is None:
                continue
            res = evaluate(C, T, M, A, B, R, grid)
            if res is None:
                continue
            cost, E, D, bounces = res
            key = (cost, bounces)
            if best is None or key < (best[0], best[3][3]):
                best = (cost, R, [row[:] for row in grid], res)
    return best


def main():
    idx = int(sys.argv[1])
    tries = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    max_delta = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    best = solve(idx, tries, max_delta)
    if best is None:
        print(f'[테스트 {idx}] 구성 실패', file=sys.stderr)
        sys.exit(1)
    cost, R, grid, res = best
    print(f'[테스트 {idx}] treegen: cost={cost} E={res[1]} D={res[2]} '
          f'bounces={res[3]} R={R}', file=sys.stderr)

    out_path = os.path.join(OUT_DIR, f'output_{idx}.txt')
    C, T, M, A, B = read_input(idx)
    old = None
    if os.path.exists(out_path):
        out = open(out_path).read().split()
        oR = int(out[0])
        og = [[out[1 + r * C + c] for c in range(C)] for r in range(oR)]
        oe = evaluate(C, T, M, A, B, oR, og)
        old = oe[0] if oe else None
    if old is None or cost < old:
        if os.path.exists(out_path) and not os.path.exists(out_path + '.bak'):
            shutil.copy(out_path, out_path + '.bak')
        with open(out_path, 'w') as f:
            f.write(str(R) + '\n')
            for row in grid:
                f.write(' '.join(row) + '\n')
        print(f'[테스트 {idx}] 갱신: {old} -> {cost}', file=sys.stderr)
    else:
        print(f'[테스트 {idx}] 기존({old})이 더 좋음 — 유지', file=sys.stderr)


if __name__ == '__main__':
    main()
