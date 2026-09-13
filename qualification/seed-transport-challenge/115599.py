import random
import sys


def assign_halves(A, B):
    C = len(A)
    pieces = []
    for i, a in enumerate(A):
        pieces.append((a - a // 2, i, 0))  # splitter first direction
        pieces.append((a // 2, i, 1))

    # A permutation represents two pieces assigned to each successive burrow.
    # Start greedily, then improve by pairwise swaps.  The extra penalty avoids
    # assigning both halves of source i back to burrow i, which the compact
    # two-row geometric routing cannot realize without a collision.
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

    target = [-1] * (2 * C)
    for j in range(C):
        target[perm[2 * j]] = j
        target[perm[2 * j + 1]] = j
    return pieces, target


def put_route(grid, r, c, j, R):
    """Route a rate<=1 stream at (r,c) horizontally, then to burrow j."""
    if c == j:
        d = R + 1 - r
        grid[r - 1][c] = 'D' if d == 1 else f'{d}D'
        return
    d = j - c
    grid[r - 1][c] = (str(abs(d)) if abs(d) >= 2 else '') + ('R' if d > 0 else 'L')
    down = R + 1 - r
    grid[r - 1][j] = 'D' if down == 1 else f'{down}D'


def solve(C, T, M, A, B):
    pieces, target = assign_halves(A, B)
    R = 2 * C + 1
    grid = [['X'] * C for _ in range(R)]

    by_source = [[None, None] for _ in range(C)]
    for p, (_, src, half) in enumerate(pieces):
        by_source[src][half] = target[p]

    for i, a in enumerate(A):
        if a == 0:
            continue
        s = 2 * i + 2  # splitter row; row s+1 belongs to its downward child
        side = 1 if i + 1 < C else -1
        sc = i + side
        ceil_target, floor_target = by_source[i]

        # The lateral branch may not target column i because the splitter itself
        # occupies that cell.  Put an own-column half on the downward branch.
        lateral_half = 0
        if ceil_target == i:
            lateral_half = 1
        lateral_target = by_source[i][lateral_half]
        down_target = by_source[i][1 - lateral_half]
        if lateral_target == i:
            # Assignment scoring makes this unreachable unless both halves target i.
            lateral_target, down_target = down_target, lateral_target
            lateral_half = 1 - lateral_half

        # Flower entry -> splitter.  All splitters are below row 1.
        entry = s - 1
        grid[0][i] = 'D' if entry == 1 else f'{entry}D'
        side_dir = 'R' if side > 0 else 'L'
        # First listed direction receives ceil(A/2).
        if lateral_half == 0:
            grid[s - 1][i] = side_dir + 'D'
        else:
            grid[s - 1][i] = 'D' + side_dir

        put_route(grid, s, sc, lateral_target, R)
        put_route(grid, s + 1, i, down_target, R)

    return R, grid


def main():
    data = list(map(int, sys.stdin.read().split()))
    C, T, M = data[:3]
    A = data[3:3 + C]
    B = data[3 + C:3 + 2 * C]
    R, grid = solve(C, T, M, A, B)
    print(R)
    for row in grid:
        print(*row)


if __name__ == '__main__':
    main()

