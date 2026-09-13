"""Purpose-built compact prefix-split generator for step-up test 15."""

import os
import random
import shutil
import sys

import treegen as G


def prefix_tree(n, radix, depth, q, left, right):
    """Route the first q leaves of a balanced radix tree to left."""
    den = radix ** depth
    if q <= 0:
        return ('leaf', right)
    if q >= den or depth == 0:
        return ('leaf', left)
    base, rem = divmod(n, radix)
    sizes = [base + (i < rem) for i in range(radix)]
    block = den // radix
    children = []
    for i, size in enumerate(sizes):
        take = max(0, min(block, q - i * block))
        children.append(prefix_tree(size, radix, depth - 1, take, left, right))
    return ('split', sizes, children)


def build(R, rng):
    C = 8
    A = [684, 297, 330, 609, 999, 198, 474, 108]
    # (radix, depth, prefix leaves); source i feeds burrows i and i+1.
    # 51 core cells, theoretical E=28.  At R=11 this leaves ample routing
    # slack while keeping base cost 8 (target total Cost about 36).
    plan = [(2, 6, 33), (2, 4, 6), (2, 4, 11), (3, 2, 8),
            (3, 4, 43), (2, 1, 1), (3, 1, 1)]
    gr = G.Grid(C, R)
    gr.search_left = 30000
    order = list(range(7))
    rng.shuffle(order)
    for i in order:
        radix, depth, q = plan[i]
        tr = prefix_tree(A[i], radix, depth, q, i, i + 1)
        if not G.place_stream(gr, 0, i, tr, rng, relay=3):
            return None
    if not G.place_stream(gr, 0, 7, ('leaf', 7), rng, relay=1):
        return None
    return gr.g


def main():
    tries = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    C, T, M, A, B = G.read_input(15)
    best = None
    rng = random.Random(150015)
    for R in (11, 12):
        for it in range(tries):
            grid = build(R, rng)
            if grid is None:
                continue
            sc = G.evaluate(C, T, M, A, B, R, grid)
            if sc and (best is None or (sc[0], sc[3]) < (best[0][0], best[0][3])):
                best = (sc, R, [row[:] for row in grid])
                print(f'best R={R} cost={sc[0]} E={sc[1]} D={sc[2]} bounce={sc[3]}',
                      file=sys.stderr)
        if best and best[0][0] <= 20:
            break
    if best is None:
        print('no placement', file=sys.stderr)
        raise SystemExit(1)
    sc, R, grid = best
    path = os.path.join(G.OUT_DIR, 'output_15.txt')
    old = open(path).read().split()
    old_R = int(old[0])
    old_grid = [old[1+r*C:1+(r+1)*C] for r in range(old_R)]
    old_sc = G.evaluate(C, T, M, A, B, old_R, old_grid)
    if sc[0] < old_sc[0]:
        shutil.copy(path, path + '.chain.bak')
        with open(path, 'w') as f:
            f.write(str(R) + '\n')
            for row in grid:
                f.write(' '.join(row) + '\n')
        print(f'updated {old_sc} -> {sc}', file=sys.stderr)
    else:
        print(f'kept old {old_sc}; chain best={sc}', file=sys.stderr)


if __name__ == '__main__':
    main()
