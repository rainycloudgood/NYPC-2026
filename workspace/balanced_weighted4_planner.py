"""Rate-safe weighted-four assignment.

Every source is split into two ~1/3 and two ~1/6 streams.  Every destination
receives exactly two streams from each class, so its fluid input rate is
exactly 1.0.  Only equal-rate pieces are exchanged during optimisation.
"""
import random


def pieces_for(a):
    q, r = divmod(a, 3)
    thirds = [q + (i < r) for i in range(3)]
    x = thirds[2]
    return [thirds[0], thirds[1], (x + 1) // 2, x // 2]


def pieces5_for(a):
    q, r = divmod(a, 3)
    thirds = [q + (i < r) for i in range(3)]
    out = [thirds[0]]
    for x in thirds[1:]:
        out.extend(((x + 1) // 2, x // 2))
    return out


def _assign_pattern(A, B, make_pieces, class_parts, seed, restarts, steps):
    c = len(A)
    pieces = [make_pieces(a) for a in A]
    rng = random.Random(0xB51A + seed * 1_000_003)
    best = None
    for _ in range(restarts):
        classes = []
        for qs in class_parts:
            arr = [(src, q) for src in range(c) for q in qs]
            rng.shuffle(arr)
            classes.append(arr)
        got = [0] * c
        for arr, qs in zip(classes, class_parts):
            width = len(qs)
            for j in range(c):
                for src, q in arr[width*j:width*(j+1)]:
                    got[j] += pieces[src][q]
        cur = sum(abs(got[j] - B[j]) for j in range(c))
        temp = max(100.0, cur / max(1, c))
        for _it in range(steps // restarts):
            ci = rng.randrange(len(classes))
            arr, width = classes[ci], len(class_parts[ci])
            x, y = rng.sample(range(len(arr)), 2)
            bx, by = x // width, y // width
            if bx == by:
                continue
            sx, qx = arr[x]
            sy, qy = arr[y]
            vx, vy = pieces[sx][qx], pieces[sy][qy]
            old = abs(got[bx]-B[bx]) + abs(got[by]-B[by])
            nx, ny = got[bx]-vx+vy, got[by]-vy+vx
            new = abs(nx-B[bx]) + abs(ny-B[by])
            delta = new-old
            if delta <= 0 or rng.random() < pow(2.718281828, -delta/max(1.0, temp)):
                arr[x], arr[y] = arr[y], arr[x]
                got[bx], got[by] = nx, ny
                cur += delta
            temp *= 0.9995
        if best is None or cur < best[0]:
            target = [[-1] * len(pieces[0]) for _ in range(c)]
            for arr, qs in zip(classes, class_parts):
                width = len(qs)
                for j in range(c):
                    for src, q in arr[width*j:width*(j+1)]:
                        target[src][q] = j
            best = cur, pieces, target, tuple(got)
    return best


def assign5(A, B, seed=0, restarts=4, steps=30_000):
    """One third plus four sixths per destination; fluid rate exactly 1."""
    return _assign_pattern(A, B, pieces5_for, ((0,), (1, 2, 3, 4)), seed,
                           restarts, steps)


def assign(A, B, seed=0, restarts=12, steps=120_000):
    c = len(A)
    pieces = [pieces_for(a) for a in A]
    rng = random.Random(0xB41A + seed * 1_000_003)
    best = None

    # The two classes are optimised independently, but their errors are
    # scored jointly because both contribute to the same destination sum.
    large_ids = [(src, q) for src in range(c) for q in (0, 1)]
    small_ids = [(src, q) for src in range(c) for q in (2, 3)]
    for _ in range(restarts):
        large = large_ids[:]
        small = small_ids[:]
        rng.shuffle(large)
        rng.shuffle(small)
        got = [0] * c
        for j in range(c):
            for src, q in large[2*j:2*j+2] + small[2*j:2*j+2]:
                got[j] += pieces[src][q]
        cur = sum(abs(got[j] - B[j]) for j in range(c))
        temp = max(100.0, cur / max(1, c))
        for it in range(steps // restarts):
            arr = large if rng.random() < 2/3 else small
            x, y = rng.sample(range(2*c), 2)
            bx, by = x // 2, y // 2
            if bx == by:
                continue
            sx, qx = arr[x]
            sy, qy = arr[y]
            vx, vy = pieces[sx][qx], pieces[sy][qy]
            old = abs(got[bx] - B[bx]) + abs(got[by] - B[by])
            nx, ny = got[bx] - vx + vy, got[by] - vy + vx
            new = abs(nx - B[bx]) + abs(ny - B[by])
            delta = new - old
            if delta <= 0 or rng.random() < pow(2.718281828, -delta / max(1.0, temp)):
                arr[x], arr[y] = arr[y], arr[x]
                got[bx], got[by] = nx, ny
                cur += delta
            temp *= 0.9995
        if best is None or cur < best[0]:
            target = [[-1] * 4 for _ in range(c)]
            for j in range(c):
                for src, q in large[2*j:2*j+2] + small[2*j:2*j+2]:
                    target[src][q] = j
            best = cur, pieces, target, tuple(got)
    return best
