"""Exhaustive two-cell repair around measured bounce edges of test 15."""

import itertools
import os
import shutil
import sys

import optimizer as O
import validate as V


def tokens(r, c, C, R):
    dirs = []
    for ch, (dr, dc) in V.DIRS.items():
        tr, tc = r + dr, c + dc
        if tr != 0 and 1 <= tr <= R + 1 and 0 <= tc < C:
            dirs.append(ch)
    out = ['X']
    for k in range(1, len(dirs) + 1):
        out.extend(''.join(p) for p in itertools.permutations(dirs, k))
    for ch, (dr, dc) in V.DIRS.items():
        for dist in range(2, max(R, C) + 2):
            tr, tc = r + dr * dist, c + dc * dist
            if 1 <= tr <= R + 1 and 0 <= tc < C:
                out.append(f'{dist}{ch}')
    return out


def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    pair_start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    pair_count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    C, T, M, A, B = O.read_input(idx)
    path = os.path.join(O.OUT_DIR, f'output_{idx}.txt')
    R, body = O.read_grid(path)
    best, best_sc = list(body), O.evaluate(C, T, M, A, B, R, body)
    # (sender, overloaded target) plus tightly coupled downstream edges.
    pairs = [((2, 4), (1, 4)), ((1, 5), (1, 4)),
             ((1, 1), (1, 2)), ((1, 5), (1, 6)),
             ((1, 8), (2, 8)), ((5, 2), (6, 2)),
             ((6, 2), (7, 2)), ((7, 2), (8, 2)),
             ((1, 3), (2, 3)), ((2, 7), (1, 7))]
    pairs = pairs[pair_start:pair_start + pair_count]
    checked = 0
    for ai, bi in pairs:
        ap = (ai[0] - 1) * C + ai[1] - 1
        bp = (bi[0] - 1) * C + bi[1] - 1
        base = list(best)
        local_best, local_sc = list(best), best_sc
        for ta in tokens(*ai, C, R):
            for tb in tokens(*bi, C, R):
                cand = list(base)
                cand[ap], cand[bp] = ta, tb
                sc = O.evaluate(C, T, M, A, B, R, cand)
                checked += 1
                if O.rank(sc) < O.rank(local_sc):
                    local_best, local_sc = cand, sc
        if O.rank(local_sc) < O.rank(best_sc):
            best, best_sc = local_best, local_sc
            print(f'pair {ai},{bi}: {best_sc}', file=sys.stderr)
        else:
            print(f'pair {ai},{bi}: no improvement', file=sys.stderr)

    old_sc = O.evaluate(C, T, M, A, B, R, body)
    if best_sc[0] < old_sc[0]:
        backup = path + '.pairs.bak'
        if not os.path.exists(backup):
            shutil.copy(path, backup)
        with open(path, 'w') as f:
            f.write(str(R) + '\n')
            for r in range(R):
                f.write(' '.join(best[r*C:(r+1)*C]) + '\n')
        print(f'updated {old_sc} -> {best_sc}; checked={checked}', file=sys.stderr)
    else:
        print(f'no Cost improvement; best={best_sc}; checked={checked}', file=sys.stderr)


if __name__ == '__main__':
    main()
