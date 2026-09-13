"""Simulated annealing for step-up test 15.

Unlike optimizer.py this may temporarily accept a worse valid layout, allowing
several routing cells to change together.  It only writes the output when the
best result beats the saved result by actual Cost.
"""

import math
import os
import random
import shutil
import sys
import time

import optimizer as O


def energy(sc):
    cost, error, delay, bounces = sc
    # Loss contributes millions to cost and is therefore rejected naturally.
    return cost + delay * 0.002 + error * 0.0002 + min(bounces, 10000) * 0.000001


def main():
    idx = int(sys.argv[1])
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 300.0
    C, T, M, A, B = O.read_input(idx)
    out_path = os.path.join(O.OUT_DIR, f'output_{idx}.txt')
    seed_path = sys.argv[3] if len(sys.argv) > 3 else out_path
    R, body = O.read_grid(seed_path)
    nc = R * C

    hot_rc = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
              (1, 7), (1, 8), (2, 3), (2, 4), (2, 5), (2, 7),
              (2, 8), (3, 4), (5, 2), (6, 1), (6, 2), (7, 2),
              (8, 2), (8, 3)]
    focus = [(r - 1) * C + c - 1 for r, c in hot_rc
             if r <= R and c <= C]

    rng = random.Random()
    seed = list(body)
    seed_sc = O.evaluate(C, T, M, A, B, R, seed)
    saved_R, saved_body = O.read_grid(out_path)
    saved_sc = O.evaluate(C, T, M, A, B, saved_R, saved_body)
    best, best_sc = list(seed), seed_sc
    cur, cur_sc = list(seed), seed_sc
    start = time.time()
    iterations = accepted = 0
    last_report = start

    while time.time() - start < budget:
        iterations += 1
        elapsed = time.time() - start
        phase = (elapsed % 45.0) / 45.0
        temp = 8.0 * (1.0 - phase) + 0.15

        cand = list(cur)
        x = rng.random()
        nmut = 1 if x < 0.45 else (2 if x < 0.72 else
                (3 if x < 0.88 else rng.randint(4, 7)))
        for _ in range(nmut):
            p = rng.choice(focus) if rng.random() < 0.82 else rng.randrange(nc)
            r, c = p // C + 1, p % C
            cand[p] = O.random_token(r, c, C, R, rng)
        sc = O.evaluate(C, T, M, A, B, R, cand)
        de = energy(sc) - energy(cur_sc)
        if de <= 0 or (sc[0] < 1000 and rng.random() < math.exp(-de / temp)):
            cur, cur_sc = cand, sc
            accepted += 1
        if O.rank(sc) < O.rank(best_sc):
            best, best_sc = list(cand), sc
            print(f'  best cost={sc[0]} E={sc[1]} D={sc[2]} bounce={sc[3]} '
                  f'iter={iterations} t={elapsed:.0f}s', file=sys.stderr)
        # Re-anchor regularly; reheating then explores a different multi-cell path.
        if iterations % 2500 == 0:
            cur, cur_sc = list(best), best_sc
        if time.time() - last_report >= 20:
            print(f'  ... iter={iterations} accepted={accepted} best={best_sc}',
                  file=sys.stderr)
            last_report = time.time()

    if best_sc[0] < saved_sc[0]:
        backup = out_path + '.sa.bak'
        if not os.path.exists(backup):
            shutil.copy(out_path, backup)
        with open(out_path, 'w') as f:
            f.write(str(R) + '\n')
            for r in range(R):
                f.write(' '.join(best[r*C:(r+1)*C]) + '\n')
        print(f'[test {idx}] updated {saved_sc} -> {best_sc}', file=sys.stderr)
    else:
        print(f'[test {idx}] no Cost improvement; saved={saved_sc}, seed={seed_sc}, best={best_sc}',
              file=sys.stderr)


if __name__ == '__main__':
    main()
