"""Fast adaptive 2/3-piece rescue prototype for high-risk inputs."""
import itertools
import random


def tok(d, ch):
    return ch if d == 1 else f"{d}{ch}"


def route(g, r, c, j, R):
    if not (1 <= r <= R and 0 <= c < len(g[0])) or g[r-1][c] != 'X':
        return False
    if c == j:
        g[r-1][c] = tok(R+1-r, 'D')
        return True
    if g[r-1][j] != 'X':
        return False
    g[r-1][c] = tok(abs(j-c), 'R' if j > c else 'L')
    g[r-1][j] = tok(R+1-r, 'D')
    return True


def split(a, k, src):
    q, r = divmod(a, k)
    return [(q + (p < r), src, p) for p in range(k)]


def assign_config(A, B, half_sources, half_targets, seed, steps=2500):
    C = len(A)
    pieces = []
    for i, a in enumerate(A):
        pieces += split(a, 2 if i in half_sources else 3, i)
    caps = [2 if j in half_targets else 3 for j in range(C)]
    starts, z = [], 0
    for cap in caps:
        starts.append(z); z += cap
    if z != len(pieces):
        return None
    rng = random.Random(seed)
    best = None
    # Two short starts are more useful than one long start for routability.
    for restart in range(2):
        perm = list(range(len(pieces))); rng.shuffle(perm)
        posbin = [0] * len(pieces)
        sums = [0] * C
        for j in range(C):
            for pos in range(starts[j], starts[j] + caps[j]):
                posbin[pos] = j
                sums[j] += pieces[perm[pos]][0]
        cur = sum(abs(sums[j] - B[j]) for j in range(C))
        for _ in range(steps // 2):
            x, y = rng.sample(range(len(pieces)), 2)
            bx, by = posbin[x], posbin[y]
            if bx == by:
                continue
            px, py = pieces[perm[x]][0], pieces[perm[y]][0]
            old = abs(sums[bx]-B[bx]) + abs(sums[by]-B[by])
            nx, ny = sums[bx]-px+py, sums[by]-py+px
            new = abs(nx-B[bx]) + abs(ny-B[by])
            if new <= old or rng.random() < 0.00015:
                perm[x], perm[y] = perm[y], perm[x]
                sums[bx], sums[by] = nx, ny
                cur += new-old
        if best is None or cur < best[0]:
            target = [-1] * len(pieces)
            for j in range(C):
                for pos in range(starts[j], starts[j] + caps[j]):
                    target[perm[pos]] = j
            best = cur, pieces, target
    return best


def layout(C, assignment):
    e, pieces, target = assignment
    ts = [[] for _ in range(C)]
    for q, piece in enumerate(pieces):
        ts[piece[1]].append(target[q])
    R = 2*C + 4
    g = [['X'] * C for _ in range(R)]
    for i in range(C):
        r = 2*i + 3
        dirs = ('U','D','R') if i == 0 else (('U','D','L') if i == C-1 else ('L','D','R'))
        dirsets = itertools.combinations(dirs, 2) if len(ts[i]) == 2 else (dirs,)
        ok = False
        for ds0 in dirsets:
            for ds in itertools.permutations(ds0):
                snap = [row[:] for row in g]
                if g[0][i] != 'X' or g[r-1][i] != 'X':
                    continue
                g[0][i] = tok(r-1, 'D'); g[r-1][i] = ''.join(ds)
                good = True
                for d, j in zip(ds, ts[i]):
                    rr, cc = ((r-1,i) if d == 'U' else
                              ((r+1,i) if d == 'D' else
                               (r, i-1 if d == 'L' else i+1)))
                    if not route(g, rr, cc, j, R):
                        good = False; break
                if good:
                    ok = True; break
                g = snap
            if ok:
                break
        if not ok:
            return None
    return R, g, e


def selections(values, k):
    order = sorted(range(len(values)), key=values.__getitem__)
    choices = [tuple(order[:k]), tuple(order[-k:])]
    mixed = []
    lo, hi = 0, len(order)-1
    while len(mixed) < k:
        mixed.append(order[hi] if len(mixed) % 2 == 0 else order[lo])
        hi -= (len(mixed) % 2 == 1)
        lo += (len(mixed) % 2 == 0)
    choices.append(tuple(sorted(mixed)))
    return list(dict.fromkeys(tuple(sorted(x)) for x in choices))


def solve(C, T, M, A, B, max_k=3):
    best = None
    for k in range(1, min(max_k, C-1)+1):
        for si, hs in enumerate(selections(A, k)):
            for ti, ht in enumerate(selections(B, k)):
                seed = 0x23A1 + 101*k + 17*si + ti + sum((q+1)*x for q,x in enumerate(A+B))
                z = assign_config(A, B, frozenset(hs), frozenset(ht), seed)
                placed = layout(C, z) if z else None
                if placed is not None and (best is None or placed[2] < best[2]):
                    best = placed
    return best
