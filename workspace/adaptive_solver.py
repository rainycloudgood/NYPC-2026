# NYPC 씨앗 운반 챌린지 - 적응형 단일 제출본 (사용자 제공, 다른 세션 산출)
import random
import itertools
import sys
from itertools import combinations

def solve_whole(C, T, M, A, B):
    R = C + 1  # sigma 계산 후 교차 스트림 수에 맞춰 축소

    INF = float('inf')
    FULL = 1 << C
    dp = [INF] * FULL
    dp[0] = 0
    choice = [[-1] * FULL for _ in range(C)]
    for mask in range(FULL):
        if dp[mask] == INF:
            continue
        i = bin(mask).count('1')
        if i >= C:
            continue
        for j in range(C):
            if mask & (1 << j):
                continue
            nm = mask | (1 << j)
            nd = dp[mask] + abs(A[i] - B[j])
            if nd < dp[nm]:
                dp[nm] = nd
                choice[i][nm] = j
    sigma = [-1] * C
    mask = FULL - 1
    for i in range(C - 1, -1, -1):
        j = choice[i][mask]
        sigma[i] = j
        mask ^= (1 << j)

    n_cross = sum(1 for i in range(C) if A[i] > 0 and sigma[i] != i)
    R = C if n_cross <= C - 1 else C + 1

    grid = [['X'] * C for _ in range(R)]

    next_slot = 2
    for i in range(C):
        j = sigma[i]
        if A[i] == 0:
            continue
        if j == i:
            grid[0][i] = f'{R}D'
            continue
        r = next_slot
        next_slot += 1
        assert 2 <= r <= R
        grid[0][i] = 'D' if r == 2 else f'{r - 1}D'
        d = j - i
        if abs(d) >= 2:
            grid[r - 1][i] = f'{abs(d)}{"R" if d > 0 else "L"}'
        else:
            grid[r - 1][i] = 'R' if d > 0 else 'L'
        grid[r - 1][j] = 'D' if r == R else f'{R + 1 - r}D'

    return R, grid


def assign_halves_exact(A, B):
    C = len(A)
    pieces = []
    for i, a in enumerate(A):
        pieces.append((a - a // 2, i, 0))
        pieces.append((a // 2, i, 1))
    n = 2 * C
    dp = {0: (0, ())}
    for j in range(C):
        ndp = {}
        for mask, (cost, pairs) in dp.items():
            rem = [p for p in range(n) if not (mask >> p) & 1]
            for x in range(len(rem)):
                for y in range(x + 1, len(rem)):
                    p, q = rem[x], rem[y]
                    nm = mask | (1 << p) | (1 << q)
                    nc = cost + abs(pieces[p][0] + pieces[q][0] - B[j])
                    if nm not in ndp or nc < ndp[nm][0]:
                        ndp[nm] = (nc, pairs + ((p, q),))
        dp = ndp
    _cost, pairs = dp[(1 << n) - 1]
    target = [-1] * n
    for j, pair in enumerate(pairs):
        for p in pair:
            target[p] = j
    return pieces, target


def assign_halves(A, B):
    C = len(A)
    if C <= 6:
        return assign_halves_exact(A, B)
    pieces = []
    for i, a in enumerate(A):
        pieces.append((a - a // 2, i, 0))
        pieces.append((a // 2, i, 1))

    remaining = list(range(2 * C))
    perm = []
    order = sorted(range(C), key=lambda j: -B[j])
    slots = [None] * C
    for j in order:
        best = None
        for x in range(len(remaining)):
            for y in range(x + 1, len(remaining)):
                p, q = remaining[x], remaining[y]
                bad = pieces[p][1] == j and pieces[q][1] == j
                key = (bad, abs(pieces[p][0] + pieces[q][0] - B[j]))
                if best is None or key < best[0]:
                    best = (key, x, y, p, q)
        _, x, y, p, q = best
        slots[j] = [p, q]
        remaining.pop(y)
        remaining.pop(x)
    for pair in slots:
        perm.extend(pair)

    def score(v):
        err = 0
        bad = 0
        for j in range(C):
            p, q = v[2 * j], v[2 * j + 1]
            err += abs(pieces[p][0] + pieces[q][0] - B[j])
            if pieces[p][1] == j and pieces[q][1] == j:
                bad += 1
        return bad * 10**9 + err

    rng = random.Random(0x5EED + C + max(A))
    cur = score(perm)
    for _ in range(30000):
        x, y = rng.sample(range(2 * C), 2)
        perm[x], perm[y] = perm[y], perm[x]
        ns = score(perm)
        if ns <= cur:
            cur = ns
        else:
            perm[x], perm[y] = perm[y], perm[x]

    def pair_cost(j, p, q):
        bad = pieces[p][1] == j and pieces[q][1] == j
        return (10**9 if bad else 0) + abs(pieces[p][0] + pieces[q][0] - B[j])

    for _ in range(8):
        changed = False
        for a, b, c in combinations(range(C), 3):
            ids = [perm[2 * j + z] for j in (a, b, c) for z in (0, 1)]
            old = sum(pair_cost(j, perm[2 * j], perm[2 * j + 1]) for j in (a, b, c))
            best = old
            best_pairs = None
            for ia, xa in combinations(range(6), 2):
                pa, qa = ids[ia], ids[xa]
                rem1 = [k for k in range(6) if k not in (ia, xa)]
                for u in range(4):
                    for v in range(u + 1, 4):
                        ib, xb = rem1[u], rem1[v]
                        rem2 = [k for k in rem1 if k not in (ib, xb)]
                        pb, qb = ids[ib], ids[xb]
                        pc, qc = ids[rem2[0]], ids[rem2[1]]
                        val = pair_cost(a, pa, qa) + pair_cost(b, pb, qb) + pair_cost(c, pc, qc)
                        if val < best:
                            best = val
                            best_pairs = ((pa, qa), (pb, qb), (pc, qc))
            if best_pairs is not None:
                for j, pair in zip((a, b, c), best_pairs):
                    perm[2 * j], perm[2 * j + 1] = pair
                changed = True
        if not changed:
            break

    for _ in range(1):
        changed = False
        for js in combinations(range(C), 4):
            ids = tuple(perm[2 * j + z] for j in js for z in (0, 1))
            old = sum(pair_cost(j, perm[2 * j], perm[2 * j + 1]) for j in js)
            best = old
            best_pairs = None

            def search(k, rem, val, made):
                nonlocal best, best_pairs
                if val >= best:
                    return
                if k == 4:
                    best = val
                    best_pairs = tuple(made)
                    return
                j = js[k]
                for x in range(len(rem)):
                    for y in range(x + 1, len(rem)):
                        p, q = rem[x], rem[y]
                        nxt = rem[:x] + rem[x + 1:y] + rem[y + 1:]
                        search(k + 1, nxt, val + pair_cost(j, p, q), made + [(p, q)])

            search(0, ids, 0, [])
            if best_pairs is not None:
                for j, pair in zip(js, best_pairs):
                    perm[2 * j], perm[2 * j + 1] = pair
                changed = True
        if not changed:
            break

    target = [-1] * (2 * C)
    for j in range(C):
        target[perm[2 * j]] = j
        target[perm[2 * j + 1]] = j
    return pieces, target


def put_route(grid, r, c, j, R):
    if c == j:
        d = R + 1 - r
        grid[r - 1][c] = 'D' if d == 1 else f'{d}D'
        return
    d = j - c
    grid[r - 1][c] = (str(abs(d)) if abs(d) >= 2 else '') + ('R' if d > 0 else 'L')
    down = R + 1 - r
    grid[r - 1][j] = 'D' if down == 1 else f'{down}D'


def solve_split(C, T, M, A, B):
    pieces, target = assign_halves(A, B)
    R = 2 * C + 1
    grid = [['X'] * C for _ in range(R)]

    by_source = [[None, None] for _ in range(C)]
    for p, (_, src, half) in enumerate(pieces):
        by_source[src][half] = target[p]

    for i, a in enumerate(A):
        if a == 0:
            continue
        s = 2 * i + 2
        side = 1 if i + 1 < C else -1
        sc = i + side
        ceil_target, floor_target = by_source[i]

        if ceil_target == floor_target:
            entry = s - 1
            grid[0][i] = 'D' if entry == 1 else f'{entry}D'
            put_route(grid, s, i, ceil_target, R)
            continue

        lateral_half = 0
        if ceil_target == i:
            lateral_half = 1
        lateral_target = by_source[i][lateral_half]
        down_target = by_source[i][1 - lateral_half]
        if lateral_target == i:
            lateral_target, down_target = down_target, lateral_target
            lateral_half = 1 - lateral_half

        entry = s - 1
        grid[0][i] = 'D' if entry == 1 else f'{entry}D'
        side_dir = 'R' if side > 0 else 'L'
        if lateral_half == 0:
            grid[s - 1][i] = side_dir + 'D'
        else:
            grid[s - 1][i] = 'D' + side_dir

        put_route(grid, s, sc, lateral_target, R)
        put_route(grid, s + 1, i, down_target, R)

    return R, grid


def whole_error(A, B):
    C = len(A)
    dp = [10**30] * (1 << C)
    dp[0] = 0
    for mask in range(1 << C):
        i = mask.bit_count()
        if i == C:
            continue
        for j in range(C):
            if not (mask >> j) & 1:
                nm = mask | (1 << j)
                dp[nm] = min(dp[nm], dp[mask] + abs(A[i] - B[j]))
    return dp[-1]


def split_error(A, B):
    pieces, target = assign_halves(A, B)
    got = [0] * len(B)
    for p, (amount, _src, _half) in enumerate(pieces):
        got[target[p]] += amount
    return sum(abs(got[j] - B[j]) for j in range(len(B)))


def main():
    d = list(map(int, sys.stdin.read().split()))
    C, T, M = d[:3]
    A = d[3:3 + C]
    B = d[3 + C:3 + 2 * C]
    ew = whole_error(A, B)
    whole_est = 2 + max(ew, 2)
    es = split_error(A, B)
    split_est = (1 << (C + 1)) + max(es, 4)
    if split_est < whole_est:
        safe_R, safe_g = solve_split(C, T, M, A, B)
    else:
        safe_R, safe_g = solve_whole(C, T, M, A, B)
    R, g = safe_R, safe_g
    print(R)
    for row in g:
        print(*row)


if __name__ == '__main__':
    main()
