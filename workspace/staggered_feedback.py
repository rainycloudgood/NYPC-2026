import argparse
import re
import subprocess
from pathlib import Path

from exact_comb_milp import solve_assignment
from staggered_comb_milp import build_grid, pieces_for_depths


SCORE_RE = re.compile(
    r"START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+) bp=([0-9,]+)"
)


def simulate(simulator, inp, grid, scratch):
    grid_path = scratch.with_suffix(".grid")
    out_path = scratch.with_suffix(".out")
    grid_path.write_text(grid)
    proc = subprocess.run(
        [str(simulator), str(inp), str(grid_path), str(out_path), "0", "0", "1"],
        text=True,
        capture_output=True,
        check=True,
    )
    match = SCORE_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(proc.stderr)
    score = tuple(map(int, match.groups()[:5]))
    bp = [int(x) for x in match.group(6).split(",") if x]
    return score, bp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--simulator", type=Path, required=True)
    p.add_argument("--depths", required=True)
    p.add_argument("--cap", type=float, required=True)
    p.add_argument("--alphas", type=float, nargs="+", default=[0.25, 0.5, 0.75])
    p.add_argument("--iterations", type=int, default=10)
    p.add_argument("--time-limit", type=float, default=1.0)
    p.add_argument("--scratch", type=Path, required=True)
    p.add_argument("--best-grid", type=Path, required=True)
    args = p.parse_args()

    vals = list(map(int, args.input.read_text().split()))
    c = vals[0]
    a = vals[3 : 3 + c]
    b = vals[3 + c : 3 + 2 * c]
    depths = tuple(map(int, args.depths.split(",")))
    pieces = pieces_for_depths(a, depths)
    best = None

    for alpha in args.alphas:
        target = list(b)
        seen = set()
        for iteration in range(args.iterations):
            solved = solve_assignment(pieces, target, args.cap, args.time_limit)
            if solved is None:
                break
            dest, static_error, got, rates = solved
            key = tuple(dest)
            if key in seen:
                break
            seen.add(key)
            grid = build_grid(c, depths, dest)
            score, bp = simulate(args.simulator, args.input, grid, args.scratch)
            print({"alpha": alpha, "iteration": iteration, "target": target,
                   "static_error": static_error, "score": score, "bp": bp}, flush=True)
            if score[3] == 0 and (best is None or score[0] < best[0][0]):
                best = (score, grid, alpha, iteration, bp)
            correction = [b[i] - bp[i] for i in range(c)]
            target = [max(0, int(round(target[i] + alpha * correction[i]))) for i in range(c)]
            delta = sum(a) - sum(target)
            order = sorted(range(c), key=lambda i: abs(correction[i]), reverse=True)
            step = 1 if delta > 0 else -1
            for k in range(abs(delta)):
                i = order[k % c]
                if step < 0 and target[i] == 0:
                    continue
                target[i] += step

    if best is None:
        raise SystemExit("no valid result")
    args.best_grid.write_text(best[1])
    print("BEST", {"score": best[0], "alpha": best[2], "iteration": best[3], "bp": best[4]})


if __name__ == "__main__":
    main()
