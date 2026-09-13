"""Exact C=9 rating benchmark using the official intermediate sampler."""
import argparse
import os
import random
import re
import subprocess
import sys
import tempfile

import challenge_submission_rating_v4_stable as current
import solution_mixed

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "public1_offline_optimizer.exe")
SUB = os.path.join(HERE, "challenge_submission_rating_v4_stable.py")
TOTAL = 1_000_000
BINS = ((111112,288765),(288766,327921),(327922,368995),
        (368996,426322),(426323,1000000))


def composition(c, rng):
    cuts = sorted(rng.sample(range(1, TOTAL + c), c - 1))
    x = [0] + cuts + [TOTAL + c]
    return [x[i + 1] - x[i] - 1 for i in range(c)]


def official_case(band, rng):
    lo, hi = BINS[band]
    while True:
        x, y = composition(9, rng), composition(9, rng)
        a, b = (x, y) if max(x) >= max(y) else (y, x)
        if lo <= max(a) <= hi:
            return a, b


def grid_text(grid):
    r, g = grid[:2]
    return str(r) + "\n" + "".join(" ".join(row) + "\n" for row in g)


def exact(inp_text, out_text, td, tag):
    ip = os.path.join(td, tag + ".in")
    gp = os.path.join(td, tag + ".grid")
    op = os.path.join(td, tag + ".out")
    with open(ip, "w") as f: f.write(inp_text)
    with open(gp, "w") as f: f.write(out_text)
    p = subprocess.run([EXE, ip, gp, op, "0", "0", "1"],
                       text=True, capture_output=True, check=True)
    m = re.search(r"START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)", p.stderr)
    return tuple(map(int, m.groups()))


def current_choice(a, b):
    c=9;m=max(a);ew=current.whole_error(a,b);es=current.split_error(a,b)
    whole_est=2+max(ew,2);split_est=(1<<(c+1))+max(es,4)
    if split_est<whole_est:r,g,chosen=current.solve_split(c,2_000_000,m,a,b)+(split_est,)
    else:r,g,chosen=current.solve_whole(c,2_000_000,m,a,b)+(whole_est,)
    risk,band,_=current.outlier_risk(c,m,b,chosen)
    z=current.solve_thirds(c,2_000_000,m,a,b,tries=3 if risk==2 else 2)
    if z:
        rr,gg,e=z;est=(1<<(c+4))+max(e,4)
        if est<chosen:r,g,chosen=rr,gg,est
    if risk==2:
        z=current.solve_variable23(c,2_000_000,m,a,b,max_k=3)
        if z:
            rr,gg,e=z;est=(1<<(c+4))+max(e,4)
            if est<chosen:r,g,chosen=rr,gg,est
    return (r,g),chosen,risk,band


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", type=int, choices=range(5), default=3)
    ap.add_argument("-n", type=int, default=4)
    ap.add_argument("--seeds", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260714)
    ap.add_argument("--skip-mixed", action="store_true")
    ap.add_argument("--skip-half", action="store_true")
    args = ap.parse_args()
    rng = random.Random(args.seed)
    rows = []
    td = os.path.join(HERE, "outputs")
    run = f"c9tmp_{os.getpid()}"
    for qi in range(args.n):
        a, b = official_case(args.band, rng)
        inp = "9 2000000 %d\n%s\n%s\n" % (
            max(a), " ".join(map(str, a)), " ".join(map(str, b)))
        cg,cest,risk,band = current_choice(a,b)
        cur = exact(inp, grid_text(cg), td, f"{run}_q{qi}_cur")
        np = subprocess.run([sys.executable, SUB], input=inp, text=True,
                            capture_output=True, check=True)
        rating = exact(inp, np.stdout, td, f"{run}_q{qi}_rating")
        mixed = []
        if not args.skip_mixed:
            for seed in range(args.seeds):
                z = solution_mixed.solve_fast(9, 2_000_000, max(a), a, b, seed)
                if z:
                    mixed.append((exact(inp, grid_text(z), td,
                                        f"{run}_q{qi}_m{seed}"), z[2], seed))
        pick = min(mixed, default=None, key=lambda x: x[0][0])
        third6=current.solve_thirds(9,2_000_000,max(a),a,b,tries=6)
        t6=(exact(inp,grid_text(third6),td,f"{run}_q{qi}_t6"),
            (1<<(9+4))+third6[2]) if third6 else None
        var8=current.solve_variable23(9,2_000_000,max(a),a,b,max_k=8)
        v8=(exact(inp,grid_text(var8),td,f"{run}_q{qi}_v8"),
            (1<<(9+4))+var8[2]) if var8 else None
        half = []
        for seed in (() if args.skip_half else range(args.seeds)):
            az = current.assign_maxhalf(a, b, restarts=8, steps=20000,
                                        seed=seed)
            _, pieces, target, _, big = az
            rates = [0.0] * 9
            for pid, piece in enumerate(pieces):
                rates[target[pid]] += 1.0 / (2 if piece[1] == big else 3)
            mr = max(rates)
            z = current.solve_maxhalf(9, 2_000_000, max(a), a, b,
                                      seed=seed, restarts=8, steps=20000)
            if z:
                half.append((exact(inp, grid_text(z), td,
                                   f"{run}_q{qi}_h{seed}"), z[2], seed, mr))
        hpick = min(half, default=None, key=lambda x: x[0][0])
        hest=hpick[1]+(1<<(9+4)) if hpick else 10**30
        rows.append((cur[0], pick[0][0] if pick else 10**30,
                     hpick[0][0] if hpick else 10**30,cest,hest,
                     t6[0][0] if t6 else 10**30,v8[0][0] if v8 else 10**30,
                     rating[0]))
        print(qi, "M", max(a), "current", cur, "rating",rating,"cest", cest,
              "mixed", None if pick is None else pick,
              "maxhalf", None if hpick is None else hpick,
              "third6",t6,"var8",v8,"half_all", half)
    mwins = sum(x[1] < x[0] for x in rows)
    hwins = sum(x[2] < x[0] for x in rows)
    twins = sum(x[5] < x[0] for x in rows)
    vwins = sum(x[6] < x[0] for x in rows)
    rwins = sum(x[7] < x[0] for x in rows)
    rloss = sum(x[7] > x[0] for x in rows)
    print("mixed_wins", mwins, "maxhalf_wins", hwins,
          "third6_wins",twins,"var8_wins",vwins,"/", len(rows),
          "current", [x[0] for x in rows], "mixed", [x[1] for x in rows],
          "maxhalf", [x[2] for x in rows],
          "ratios", [round(x[4]/x[3],3) for x in rows],
          "third6",[x[5] for x in rows],"var8",[x[6] for x in rows],
          "rating",[x[7] for x in rows],"rating_wins",rwins,"losses",rloss)


if __name__ == "__main__":
    main()
