"""Fast k-way equal-piece assignment estimate for challenge inputs."""

import random
import sys


def run(A, B, k, restarts=30, steps=200000):
    C = len(A)
    pieces = []
    for a in A:
        q, r = divmod(a, k)
        pieces += [q + (i < r) for i in range(k)]
    best = 10**30
    rng = random.Random(13902 + k)
    for z in range(restarts):
        perm = list(range(k*C))
        rng.shuffle(perm)
        sums = [sum(pieces[perm[k*j+t]] for t in range(k)) for j in range(C)]
        cur = sum(abs(sums[j] - B[j]) for j in range(C))
        for _ in range(steps // restarts):
            x, y = rng.sample(range(k*C), 2)
            bx, by = x // k, y // k
            if bx == by:
                continue
            px, py = pieces[perm[x]], pieces[perm[y]]
            old = abs(sums[bx]-B[bx]) + abs(sums[by]-B[by])
            nsx, nsy = sums[bx]-px+py, sums[by]-py+px
            new = abs(nsx-B[bx]) + abs(nsy-B[by])
            if new <= old or rng.random() < 0.0002:
                perm[x], perm[y] = perm[y], perm[x]
                sums[bx], sums[by] = nsx, nsy
                cur += new-old
                best = min(best, cur)
    return best


data = list(map(int, open(sys.argv[1]).read().split()))
C = data[0]
A = data[3:3+C]
B = data[3+C:3+2*C]
for k in range(2, 7):
    print(k, run(A, B, k))
