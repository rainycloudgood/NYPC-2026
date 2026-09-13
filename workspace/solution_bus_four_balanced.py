"""Rate-safe 1/3,1/3,1/6,1/6 splitter bank feeding destination buses."""
import sys

from balanced_weighted4_planner import assign


def tok(n, ch):
    return ch if n == 1 else f'{n}{ch}'


def solve(C, T, M, A, B, seed=0, compact=False, restarts=4, steps=30_000):
    e, pieces, targets, got = assign(A, B, seed, restarts=restarts, steps=steps)
    split_rows = 9 if compact else 11
    R = split_rows + C
    g = [['X'] * C for _ in range(R)]

    for j in range(C):
        br = split_rows + 1 + j
        for col in range(C):
            if col < j:
                g[br-1][col] = 'R'
            elif col > j:
                g[br-1][col] = 'L'
            else:
                g[br-1][col] = tok(R + 1 - br, 'D')

    def send(r, col, dest):
        if not (1 <= r <= split_rows and 0 <= col < C):
            return False
        if g[r-1][col] != 'X':
            return False
        br = split_rows + 1 + dest
        g[r-1][col] = tok(br-r, 'D')
        return True

    for i in range(C):
        r = 3 + (2 if compact else 3) * (i % 3)
        side = 'R' if i < C-1 else 'L'
        dc = 1 if side == 'R' else -1
        if g[0][i] != 'X' or g[r-1][i] != 'X' or g[r][i] != 'X':
            return None
        g[0][i] = tok(r-1, 'D')
        g[r-1][i] = 'U' + side + 'D'
        g[r][i] = 'D' + side
        starts = ((r-1, i), (r, i+dc), (r+2, i), (r+1, i+dc))
        for (rr, cc), dest in zip(starts, targets[i]):
            if not send(rr, cc, dest):
                return None
    return R, g, e, got


if __name__ == '__main__':
    d = list(map(int, sys.stdin.read().split()))
    C, T, M = d[:3]
    A = d[3:3+C]
    B = d[3+C:3+2*C]
    best = None
    for compact in (True, False):
        for seed in range(3):
            z = solve(C, T, M, A, B, seed, compact)
            if z and (best is None or (1 << (z[0]-C)) + z[2] < (1 << (best[0]-C)) + best[2]):
                best = z
    if best is None:
        raise SystemExit('no layout')
    R, g, e, got = best
    print(R)
    for row in g:
        print(*row)
    print('E_est', e, 'got', got, file=sys.stderr)
