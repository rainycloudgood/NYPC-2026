"""Aggressive challenge planner: assign three near-equal pieces per flower."""

import random


def assign_thirds(A, B, restarts=80, steps=400000, seed_offset=0):
    C = len(A)
    pieces = []
    for src, a in enumerate(A):
        q, rem = divmod(a, 3)
        for part in range(3):
            pieces.append((q + (part < rem), src, part))

    rng = random.Random(0x3D1F + C + max(A) + seed_offset * 1000003)
    best = None
    for _ in range(restarts):
        perm = list(range(3 * C))
        rng.shuffle(perm)
        sums = [sum(pieces[perm[3*j+t]][0] for t in range(3)) for j in range(C)]
        cur = sum(abs(sums[j] - B[j]) for j in range(C))
        for _ in range(steps // restarts):
            x, y = rng.sample(range(3 * C), 2)
            bx, by = x // 3, y // 3
            if bx == by:
                continue
            px, py = pieces[perm[x]][0], pieces[perm[y]][0]
            old = abs(sums[bx]-B[bx]) + abs(sums[by]-B[by])
            nx, ny = sums[bx]-px+py, sums[by]-py+px
            new = abs(nx-B[bx]) + abs(ny-B[by])
            if new <= old or rng.random() < 0.0001:
                perm[x], perm[y] = perm[y], perm[x]
                sums[bx], sums[by] = nx, ny
                cur += new - old
        if best is None or cur < best[0]:
            target = [-1] * (3 * C)
            for j in range(C):
                for t in range(3):
                    target[perm[3*j+t]] = j
            best = (cur, pieces, target, tuple(sums))
    return best
