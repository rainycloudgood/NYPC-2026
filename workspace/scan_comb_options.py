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


def valid_strip_count(c):
    k = min(3, c // 2)

    def side_matching(chosen):
        def dfs(q, used):
            if q == len(chosen):
                return True
            i = chosen[q]
            for j in (i - 1, i + 1):
                if 0 <= j < c and i not in used and j not in used:
                    if dfs(q + 1, used | {i, j}):
                        return True
            return False

        return dfs(0, set())

    import itertools

    return sum(side_matching(x) for x in itertools.combinations(range(c), k))


def run_one(executable, inp, option):
    env = os.environ.copy()
    env["ORACLE_WIDE_COMB"] = "1"
    env["ORACLE_COMB_OPTION"] = str(option)
    started = time.perf_counter()
    proc = subprocess.run(
        [str(executable)],
        input=inp.read_text(),
        text=True,
        capture_output=True,
        env=env,
        timeout=15,
        check=True,
    )
    matches = list(RESULT_RE.finditer(proc.stderr))
    if not matches:
        raise RuntimeError(proc.stderr)
    label, r, cost, e, d, loss, bounce = matches[-1].groups()
    return {
        "option": option,
        "label": label,
        "R": int(r),
        "cost": int(cost),
        "E": int(e),
        "D": int(d),
        "L": int(loss),
        "bounce": int(bounce),
        "runtime": time.perf_counter() - started,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--prefix", default="150")
    parser.add_argument("--indices", type=int, nargs="+", required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    jobs = []
    for index in args.indices:
        inp = args.downloads / f"{args.prefix}-{index}.data.txt"
        c = int(inp.read_text().split()[0])
        for option in range(valid_strip_count(c)):
            jobs.append((index, inp, option))

    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_one, args.exe, inp, option): (index, option)
            for index, inp, option in jobs
        }
        for future in concurrent.futures.as_completed(futures):
            index, option = futures[future]
            result = future.result()
            result["index"] = index
            rows.append(result)
            print(index, option, result["cost"], result["label"], flush=True)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(rows, indent=2))
    for index in args.indices:
        case = [x for x in rows if x["index"] == index]
        best = min(case, key=lambda x: x["cost"])
        print("BEST", index, best)


if __name__ == "__main__":
    main()
