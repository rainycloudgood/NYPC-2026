"""Exact evaluation of the rate-safe weighted-four bank on unresolved tails."""
import glob
import os
import re
import subprocess

from solution_bus_four_balanced import solve

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'outputs')
EXE = os.path.join(HERE, 'public1_offline_optimizer.exe')
MS = {627401, 320226, 437573, 632957, 284296, 598289, 294014, 559049,
      611514, 822113, 790521, 382428, 667453, 348835, 610536, 770813}


def exact(inp, grid, tag):
    ip = os.path.join(OUT, tag + '.in')
    gp = os.path.join(OUT, tag + '.grid')
    op = gp + '.out'
    with open(ip, 'w') as f:
        f.write(inp)
    with open(gp, 'w') as f:
        f.write(str(grid[0]) + '\n')
        for row in grid[1]:
            f.write(' '.join(row) + '\n')
    p = subprocess.run([EXE, ip, gp, op, '0', '0', '1'], text=True,
                       capture_output=True, check=True)
    m = re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)', p.stderr)
    return tuple(map(int, m.groups()))


for path in glob.glob(os.path.join(OUT, 'midval_*.in')):
    inp = open(path).read()
    d = list(map(int, inp.split()))
    C, T, M = d[:3]
    if M not in MS:
        continue
    A, B = d[3:3+C], d[3+C:3+2*C]
    candidates = []
    for seed in range(3):
        for compact in (True, False):
            z = solve(C, T, M, A, B, seed, compact)
            if z:
                candidates.append(z)
    if not candidates:
        print(C, M, 'NO_LAYOUT', flush=True)
        continue
    z = min(candidates, key=lambda q: (1 << (q[0]-C)) + q[2])
    score = exact(inp, (z[0], z[1]), 'balanced4_' + os.path.basename(path)[:-3])
    print(C, M, 'model', (1 << (z[0]-C)) + z[2], 'exact', score, flush=True)
