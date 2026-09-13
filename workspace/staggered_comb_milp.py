import argparse
import itertools
import json
import re
import subprocess
from pathlib import Path

from exact_comb_milp import solve_assignment


START_RE = re.compile(r"START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)")


def pieces_for_depths(a, depths):
    pieces = []
    for src, (value, depth) in enumerate(zip(a, depths)):
        if depth == 0:
            pieces.append((value, 1.0, src))
            continue
        x, rate = value, 1.0
        for _ in range(depth):
            hi, lo = (x + 1) // 2, x // 2
            pieces.append((hi, rate / 2, src))
            x, rate = lo, rate / 2
        pieces.append((x, rate, src))
    return pieces


def hop(distance, direction):
    if distance == 1:
        return direction
    return f"{distance}{direction}"


def build_grid(c, depths, dest):
    split_rows = 1 + sum(depth + 1 for depth in depths if depth > 0)
    if split_rows > 20:
        raise ValueError(f"R-C budget exceeded: {split_rows}")
    rows = split_rows + c
    grid = [["X"] * c for _ in range(rows)]

    for target in range(c):
        r = split_rows + target
        for col in range(c):
            grid[r][col] = "R" if col < target else ("L" if col > target else hop(rows - r, "D"))

    cursor = 1
    p = 0
    for src, depth in enumerate(depths):
        if depth == 0:
            grid[0][src] = hop(split_rows + dest[p], "D")
            p += 1
            continue
        grid[0][src] = "D" if cursor == 1 else hop(cursor, "D")
        side_col = src + 1 if src + 1 < c else src - 1
        side_dir = "R" if side_col > src else "L"
        for level in range(depth):
            r = cursor + level
            grid[r][src] = side_dir + "D"
            grid[r][side_col] = hop(split_rows + dest[p] - r, "D")
            p += 1
        r = cursor + depth
        grid[r][src] = hop(split_rows + dest[p] - r, "D")
        p += 1
        cursor += depth + 1
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
    if not match:
        raise RuntimeError(proc.stderr)
    return tuple(map(int, match.groups()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--simulator", type=Path, required=True)
    parser.add_argument("--depth-vectors", type=str, nargs="+", required=True)
    parser.add_argument("--enumerate-budget", type=int, default=None)
    parser.add_argument("--min-extra", type=int, default=0)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--exact-top", type=int, default=None)
    parser.add_argument("--caps", type=float, nargs="+", default=[1.5, 1.8, 2.0])
    parser.add_argument("--time-limit", type=float, default=3.0)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--best-grid", type=Path, required=True)
    args = parser.parse_args()

    values = list(map(int, args.input.read_text().split()))
    c = values[0]
    a = values[3 : 3 + c]
    b = values[3 + c : 3 + 2 * c]
    best = None
    records = []
    vectors = [tuple(map(int, encoded.split(","))) for encoded in args.depth_vectors]
    if args.enumerate_budget is not None:
        vectors = []
        for depths in itertools.product(range(args.max_depth + 1), repeat=c):
            extra = 1 + sum(depth + 1 for depth in depths if depth > 0)
            if args.min_extra <= extra <= args.enumerate_budget:
                vectors.append(depths)

    static_candidates = []
    for depths in vectors:
        if len(depths) != c:
            raise ValueError(depths)
        pieces = pieces_for_depths(a, depths)
        for cap in args.caps:
            solved = solve_assignment(pieces, b, cap, args.time_limit)
            if solved is None:
                continue
            dest, static_error, got, rates = solved
            static_candidates.append((static_error, depths, cap, dest, got, rates))

    static_candidates.sort(key=lambda row: row[0])
    if args.exact_top is not None:
        static_candidates = static_candidates[: args.exact_top]

    for static_error, depths, cap, dest, got, rates in static_candidates:
            grid = build_grid(c, depths, dest)
            exact = exact_score(args.simulator, args.input, grid, args.scratch)
            row = {
                "depths": depths,
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
