"""Reproduce the official intermediate-data distribution and benchmark strategies.

The composition sampler is exactly the statement's stars-and-bars construction.
This tool is offline only; nothing here is included in the submitted program.
"""
import argparse
import random
import statistics

from challenge_submission_rating_v4_stable import whole_error, split_error
from thirds_planner import assign_thirds
from solution_thirds_layout import solve as solve_thirds
from solution_mixed import solve as solve_mixed
from solution_maxhalf import solve as solve_maxhalf

TOTAL = 1_000_000
BINS = {
    5: ((200000,421816),(421817,479291),(479292,539215),(539216,618806),(618807,1000000)),
    6: ((166667,376195),(376196,427656),(427657,481244),(481245,554261),(554262,1000000)),
    7: ((142858,340734),(340735,387307),(387308,435920),(435921,502939),(502940,1000000)),
    8: ((125000,312245),(312246,354780),(354781,399301),(399302,461116),(461117,1000000)),
    9: ((111112,288765),(288766,327921),(327922,368995),(368996,426322),(426323,1000000)),
    10:((100000,269020),(269021,305310),(305311,343441),(343442,396873),(396874,1000000)),
}


def composition(c, rng):
    cuts = sorted(rng.sample(range(1, TOTAL + c), c - 1))
    x = [0] + cuts + [TOTAL + c]
    return [x[i + 1] - x[i] - 1 for i in range(c)]


def official_case(c, band, rng):
    lo, hi = BINS[c][band]
    while True:
        x, y = composition(c, rng), composition(c, rng)
        a, b = (x, y) if max(x) >= max(y) else (y, x)
        if lo <= max(a) <= hi:
            return a, b


def costs(c, a, b, iterations):
    ew = whole_error(a, b)
    es = split_error(a, b)
    # R=2C+4 for the current thirds layout, hence R-C=C+4.
    et = assign_thirds(a, b, restarts=8, steps=iterations)[0]
    return 2 + max(ew, 2), (1 << (c + 1)) + max(es, 4), (1 << (c + 4)) + max(et, 4)


def current_costs(c, a, b, iterations, tries, use_mixed, use_maxhalf):
    ew, es = whole_error(a, b), split_error(a, b)
    w = 2 + max(ew, 2)
    h = (1 << (c + 1)) + max(es, 4)
    safe = min(w, h)
    z = solve_thirds(c, 2_000_000, max(a), a, b,
                     restarts=8, steps=iterations, tries=tries)
    third = (1 << (c + 4)) + max(z[2], 4) if z else 10**30
    mz = solve_mixed(c, 2_000_000, max(a), a, b) if use_mixed else None
    mixed = (1 << (c + 1)) + max(mz[2], 4) if mz else 10**30
    hz = solve_maxhalf(c, 2_000_000, max(a), a, b) if use_maxhalf else None
    halfmax = (1 << (c + 4)) + max(hz[2], 4) if hz else 10**30
    return safe, third, mixed, halfmax, min(safe, third, mixed, halfmax), z is not None, mz is not None, hz is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-n', '--samples', type=int, default=8)
    ap.add_argument('--iterations', type=int, default=24000)
    ap.add_argument('--seed', type=int, default=20260712)
    ap.add_argument('--tries', type=int, default=2)
    ap.add_argument('--c', type=int, choices=range(5, 11))
    ap.add_argument('--band', type=int, choices=range(5),
                    help='benchmark only one official M band')
    ap.add_argument('--mixed', action='store_true')
    ap.add_argument('--maxhalf', action='store_true')
    args = ap.parse_args()
    rng = random.Random(args.seed)
    print('C bin safe_med third_med maxhalf final_med T_win H_win Tlay Hlay')
    cs = [args.c] if args.c else range(5, 11)
    for c in cs:
        bands = [args.band] if args.band is not None else range(5)
        for band in bands:
            rows = [current_costs(c, *official_case(c, band, rng),
                                  args.iterations, args.tries, args.mixed, args.maxhalf)
                    for _ in range(args.samples)]
            tw=sum(th < min(s,mx,h) for s,th,mx,h,f,to,mo,ho in rows)
            hw=sum(h < min(s,th,mx) for s,th,mx,h,f,to,mo,ho in rows)
            print(f'{c:2} {band:3} {statistics.median(x[0] for x in rows):10.0f}'
                  f' {statistics.median(x[1] for x in rows):9.0f}'
                  f' {statistics.median(x[3] for x in rows):9.0f}'
                  f' {statistics.median(x[4] for x in rows):9.0f}'
                  f' {tw:2}/{args.samples:<2} {hw:2}/{args.samples:<2}'
                  f' {sum(x[5] for x in rows):2}/{args.samples:<2}'
                  f' {sum(x[7] for x in rows):2}/{args.samples:<2}')


if __name__ == '__main__':
    main()
