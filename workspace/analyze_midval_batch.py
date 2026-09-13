import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import tempfile
import time
from pathlib import Path


RESULT_RE = re.compile(
    r"(?:^|\s)R=(\d+)\s+cost=(\d+)\s+E=(\d+)\s+D=(\d+)\s+L=(\d+)\s+bounce=(\d+)"
)
START_RE = re.compile(
    r"START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)"
)


def read_input(path: Path):
    values = list(map(int, path.read_text().split()))
    c, t, m = values[:3]
    a = values[3 : 3 + c]
    b = values[3 + c : 3 + 2 * c]
    return c, t, m, a, b


def simulate_saved(simulator: Path, inp: Path, grid: Path, scratch: Path):
    proc = subprocess.run(
        [str(simulator), str(inp), str(grid), str(scratch), "0", "0", "1"],
        text=True,
        capture_output=True,
        check=True,
    )
    match = START_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(f"no START result for {inp.name}: {proc.stderr}")
    cost, e, d, loss, bounce = map(int, match.groups())
    return {"cost": cost, "E": e, "D": d, "L": loss, "bounce": bounce}


def run_current(executable: Path, inp: Path):
    env = os.environ.copy()
    env["ORACLE_LOG_SAMPLES"] = "1"
    started = time.perf_counter()
    proc = subprocess.run(
        [str(executable)],
        input=inp.read_text(),
        text=True,
        capture_output=True,
        env=env,
        timeout=5,
        check=True,
    )
    elapsed = time.perf_counter() - started
    result_lines = [line for line in proc.stderr.splitlines() if RESULT_RE.search(line)]
    if not result_lines:
        raise RuntimeError(f"no final result for {inp.name}: {proc.stderr}")
    final_line = result_lines[-1]
    final_match = RESULT_RE.search(final_line)
    r, cost, e, d, loss, bounce = map(int, final_match.groups())
    label = final_line.split(" R=", 1)[0].removeprefix("sample ")
    samples = []
    for line in proc.stderr.splitlines():
        if not line.startswith("sample "):
            continue
        sm = re.search(r"cost=(\d+) E=(\d+) D=(\d+) L=(\d+)", line)
        if sm:
            samples.append(
                {
                    "label": line[7 : line.index(" cost=")],
                    "cost": int(sm.group(1)),
                    "E": int(sm.group(2)),
                    "D": int(sm.group(3)),
                    "L": int(sm.group(4)),
                }
            )
    return (
        {"R": r, "cost": cost, "E": e, "D": d, "L": loss, "bounce": bounce},
        label,
        elapsed,
        samples,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--prefix", default="150")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--simulator", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    args.report.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.report.with_suffix(".scratch.grid")
    for index in range(1, args.count + 1):
        inp = args.downloads / f"{args.prefix}-{index}.data.txt"
        grid = args.downloads / f"{args.prefix}-{index}.log.txt"
        c, t, m, a, b = read_input(inp)
        submitted = simulate_saved(args.simulator, inp, grid, scratch)
        current, label, elapsed, samples = run_current(args.exe, inp)
        row = {
            "index": index,
            "C": c,
            "band": (index - 1) % 5,
            "M": m,
            "sumA": sum(a),
            "maxA_share": max(a) / sum(a),
            "maxB_share": max(b) / sum(b),
            "submitted": submitted,
            "current": current,
            "delta": current["cost"] - submitted["cost"],
            "label": label,
            "runtime": elapsed,
            "samples": samples,
        }
        rows.append(row)
        print(
            f"{index:2d} C{c} b{row['band']} M={m:7d} "
            f"saved={submitted['cost']:7d} current={current['cost']:7d} "
            f"E={current['E']:7d} D={current['D']:7d} L={current['L']} "
            f"t={elapsed:.3f}s {label}"
        )

    args.report.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    csv_path = args.report.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["index", "C", "band", "M", "saved", "current", "E", "D", "L", "bounce", "runtime", "label"]
        )
        for row in rows:
            cur = row["current"]
            writer.writerow(
                [row["index"], row["C"], row["band"], row["M"], row["submitted"]["cost"], cur["cost"], cur["E"], cur["D"], cur["L"], cur["bounce"], f"{row['runtime']:.6f}", row["label"]]
            )

    costs = [row["current"]["cost"] for row in rows]
    runtimes = [row["runtime"] for row in rows]
    print(
        "SUMMARY",
        f"avg={statistics.mean(costs):.1f}",
        f"median={statistics.median(costs):.1f}",
        f"max={max(costs)}",
        f"over50={sum(x > 50000 for x in costs)}",
        f"over60={sum(x > 60000 for x in costs)}",
        f"over100={sum(x > 100000 for x in costs)}",
        f"runtime_med={statistics.median(runtimes):.3f}",
        f"runtime_max={max(runtimes):.3f}",
    )


if __name__ == "__main__":
    main()
