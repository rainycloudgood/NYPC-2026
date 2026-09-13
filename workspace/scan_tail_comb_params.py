import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import time
from pathlib import Path


RESULT_RE = re.compile(
    r"^(.*?) R=(\d+) cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)$",
    re.MULTILINE,
)


def run_one(exe, text, option, depth, cap, seeds, keep, adaptive):
    env = os.environ.copy()
    env.update({
        "ORACLE_FULL": "1",
        "ORACLE_COMB_OPTION": str(option),
        "ORACLE_STRIP_CHOICES": "1",
        "ORACLE_COMB_DEPTH": str(depth),
        "ORACLE_COMB_CAP_VALUE": str(cap),
        "ORACLE_COMB_SEEDS": str(seeds),
        "ORACLE_COMB_KEEP_PER_OPTION": str(keep),
        "ORACLE_SKIP_KNOWN": "1",
    })
    if adaptive:
        env["ORACLE_COMB_ADAPTIVE"] = "1"
    started = time.perf_counter()
    proc = subprocess.run(
        [str(exe)], input=text, text=True, capture_output=True,
        env=env, timeout=45, check=True,
    )
    matches = list(RESULT_RE.finditer(proc.stderr))
    if not matches:
        raise RuntimeError(proc.stderr)
    label, rows, cost, error, delay, loss, bounce = matches[-1].groups()
    return {
        "option": option, "depth": depth, "cap": cap,
        "label": label, "R": int(rows), "cost": int(cost),
        "E": int(error), "D": int(delay), "L": int(loss),
        "bounce": int(bounce), "runtime": time.perf_counter() - started,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--exe", type=Path, required=True)
    p.add_argument("--option", type=int, nargs="+", required=True)
    p.add_argument("--depths", type=int, nargs="+", default=range(5, 11))
    p.add_argument("--caps", type=float, nargs="+", required=True)
    p.add_argument("--seeds", type=int, default=80)
    p.add_argument("--keep", type=int, default=6)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--adaptive", action="store_true")
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    text = args.input.read_text()
    jobs = [(option, d, cap) for option in args.option for d in args.depths for cap in args.caps]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_one, args.exe, text, option, d, cap, args.seeds, args.keep, args.adaptive): (option, d, cap)
            for option, d, cap in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            print(row, flush=True)
    rows.sort(key=lambda x: x["cost"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(rows, indent=2))
    print("BEST", rows[0])


if __name__ == "__main__":
    main()
