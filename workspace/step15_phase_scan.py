"""Exhaustive direction-phase polishing for the saved step-up test 15 grid."""

import itertools
import os

import optimizer as O


def main():
    idx = 15
    C, T, M, A, B = O.read_input(idx)
    path = os.path.join(O.OUT_DIR, "output_15.txt")
    R, original = O.read_grid(path)
    best = list(original)
    best_sc = O.evaluate(C, T, M, A, B, R, best)
    checked = 0

    # Repeated coordinate descent.  Accepting a same-cost phase with smaller
    # D/E/bounces can open a later improving move without changing topology.
    for sweep in range(4):
        changed = False
        for p, token in enumerate(list(best)):
            if token == "X" or token[0].isdigit() or len(token) < 2:
                continue
            variants = sorted(set("".join(x) for x in itertools.permutations(token)))
            local, local_sc = best[p], best_sc
            for candidate in variants:
                if candidate == best[p]:
                    continue
                body = list(best)
                body[p] = candidate
                sc = O.evaluate(C, T, M, A, B, R, body)
                checked += 1
                if O.rank(sc) < O.rank(local_sc):
                    local, local_sc = candidate, sc
            if O.rank(local_sc) < O.rank(best_sc):
                best[p] = local
                best_sc = local_sc
                changed = True
                print(f"sweep={sweep} cell={p // C + 1},{p % C + 1} token={local} score={best_sc}")
        if not changed:
            break

    old_sc = O.evaluate(C, T, M, A, B, R, original)
    if O.rank(best_sc) < O.rank(old_sc):
        trial = os.path.join(O.OUT_DIR, "output_15_phase_trial.txt")
        with open(trial, "w") as f:
            f.write(str(R) + "\n")
            for r in range(R):
                f.write(" ".join(best[r * C:(r + 1) * C]) + "\n")
        print(f"TRIAL {trial}: {old_sc} -> {best_sc}; checked={checked}")
    else:
        print(f"NO_CHANGE best={best_sc}; checked={checked}")


if __name__ == "__main__":
    main()
