import argparse
import itertools
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


START_RE = re.compile(r"START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)")


def side_matching(c, chosen):
    side = [-1] * len(chosen)

    def dfs(q, used):
        if q == len(chosen):
            return True
        i = chosen[q]
        for j in (i - 1, i + 1):
            if 0 <= j < c and i not in used and j not in used:
                side[q] = j
                if dfs(q + 1, used | {i, j}):
                    return True
        return False

    return side if dfs(0, set()) else None


def strip_sets(c, a):
    k = min(3, c // 2)
    rows = []
    for chosen in itertools.combinations(range(c), k):
        side = side_matching(c, chosen)
        if side is not None:
            rows.append((-sum(a[i] for i in chosen), list(chosen), side))
    rows.sort()
    return [(chosen, side) for _, chosen, side in rows]


def make_pieces(a, chosen, depth):
    take = set(chosen)
    pieces = []
    for src, value in enumerate(a):
        if src not in take:
            pieces.append((value, 1.0, src))
            continue
        x = value
        rate = 1.0
        for _ in range(depth):
            hi, lo = (x + 1) // 2, x // 2
            pieces.append((hi, rate / 2, src))
            x, rate = lo, rate / 2
        pieces.append((x, rate, src))
    return pieces


def solve_assignment(pieces, targets, cap, time_limit):
    n, c = len(pieces), len(targets)
    nx = n * c
    nv = nx + 2 * c
    objective = np.zeros(nv)
    objective[nx:] = 1.0
    integrality = np.zeros(nv)
    integrality[:nx] = 1
    lower = np.zeros(nv)
    upper = np.full(nv, np.inf)
    upper[:nx] = 1

    eq = lil_matrix((n + c, nv), dtype=float)
    rhs = np.zeros(n + c)
    for q in range(n):
        for j in range(c):
            eq[q, q * c + j] = 1
        rhs[q] = 1
    for j in range(c):
        for q, (amount, _, _) in enumerate(pieces):
            eq[n + j, q * c + j] = amount
        eq[n + j, nx + 2 * j] = -1
        eq[n + j, nx + 2 * j + 1] = 1
        rhs[n + j] = targets[j]

    rate = lil_matrix((c, nv), dtype=float)
    for j in range(c):
        for q, (_, piece_rate, _) in enumerate(pieces):
            rate[j, q * c + j] = piece_rate

    constraints = [
        LinearConstraint(eq.tocsr(), rhs, rhs),
        LinearConstraint(rate.tocsr(), np.zeros(c), np.full(c, cap)),
    ]
    result = milp(
        objective,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=constraints,
        options={"time_limit": time_limit, "mip_rel_gap": 0.0},
    )
    if result.x is None:
        return None
    dest = []
    for q in range(n):
        dest.append(int(np.argmax(result.x[q * c : (q + 1) * c])))
    got = [0] * c
    rates = [0.0] * c
    for q, j in enumerate(dest):
        got[j] += pieces[q][0]
        rates[j] += pieces[q][1]
    error = sum(abs(got[j] - targets[j]) for j in range(c))
    return dest, error, got, rates


def hop(distance, direction):
    return direction if distance == 1 else f"{distance}{direction}"


def build_grid(c, a, chosen, side, depth, dest):
    bus0 = depth + 2
    rows = bus0 + c
    grid = [["X"] * c for _ in range(rows)]
    for j in range(c):
        r = bus0 + j
        for col in range(c):
            grid[r][col] = "R" if col < j else ("L" if col > j else hop(rows - r, "D"))
    side_of = [-1] * c
    for src, side_col in zip(chosen, side):
        side_of[src] = side_col
    p = 0
    for src in range(c):
        if side_of[src] < 0:
            grid[0][src] = hop(bus0 + dest[p], "D")
            p += 1
            continue
        side_col = side_of[src]
        side_dir = "R" if side_col > src else "L"
        grid[0][src] = "D"
        for level in range(depth):
            r = 1 + level
            grid[r][src] = side_dir + "D"
            grid[r][side_col] = hop(bus0 + dest[p] - r, "D")
            p += 1
        r = depth + 1
        grid[r][src] = hop(bus0 + dest[p] - r, "D")
        p += 1
    return str(rows) + "\n" + "".join(" ".join(row) + "\n" for row in grid)


def exact_score(simulator, inp, grid_text, scratch):
    grid_path = scratch.with_suffix(".grid")
    out_path = scratch.with_suffix(".out")
    grid_path.write_text(grid_text)
    proc = subprocess.run(
        [str(simulator), str(inp), str(grid_path), str(out_path), "0", "0", "1"],
        text=True,
        capture_output=True,
        check=True,
    )
    match = START_RE.search(proc.stderr)
    return tuple(map(int, match.groups()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--simulator", type=Path, required=True)
    parser.add_argument("--options", type=int, nargs="+", required=True)
    parser.add_argument("--depths", type=int, nargs="+", default=[5, 6, 7, 8, 9, 10])
    parser.add_argument("--caps", type=float, nargs="+", default=[1.1, 1.25, 1.5, 2.0])
    parser.add_argument("--time-limit", type=float, default=2.0)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--best-grid", type=Path, required=True)
    args = parser.parse_args()

    values = list(map(int, args.input.read_text().split()))
    c, _, _ = values[:3]
    a = values[3 : 3 + c]
    b = values[3 + c : 3 + 2 * c]
    strips = strip_sets(c, a)
    best = None
    records = []
    for option in args.options:
        chosen, side = strips[option]
        for depth in args.depths:
            pieces = make_pieces(a, chosen, depth)
            for cap in args.caps:
                solved = solve_assignment(pieces, b, cap, args.time_limit)
                if solved is None:
                    continue
                dest, static_error, got, rates = solved
                grid = build_grid(c, a, chosen, side, depth, dest)
                exact = exact_score(args.simulator, args.input, grid, args.scratch)
                row = {
                    "option": option,
                    "depth": depth,
                    "cap": cap,
                    "static_error": static_error,
                    "got": got,
                    "rates": rates,
                    "exact": exact,
                }
                records.append(row)
                print(row, flush=True)
                if exact[3] == 0 and (best is None or exact[0] < best[0]["exact"][0]):
                    best = (row, grid)
    if best is None:
        raise SystemExit("no feasible exact result")
    args.best_grid.write_text(best[1])
    args.best_grid.with_suffix(".json").write_text(json.dumps({"best": best[0], "all": records}, indent=2))
    print("BEST", best[0])


if __name__ == "__main__":
    main()
