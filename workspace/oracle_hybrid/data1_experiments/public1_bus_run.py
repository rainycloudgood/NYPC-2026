import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import public1_bus_builder as BB
from public1_treegen_driver import read_input, lp_min_d_flows, INP, EXE


def score(R, grid):
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, dir=HERE) as tf:
        tf.write(str(R)+'\n')
        for row in grid:
            tf.write(' '.join(row)+'\n')
        gp = tf.name
    op = gp+'.out'
    try:
        p = subprocess.run([EXE, INP, gp, op, '0', '0', '1'],
                           capture_output=True, text=True, timeout=120)
        line = p.stderr.strip().splitlines()[0] if p.stderr.strip() else ''
        d = {}
        for part in line.replace(',', ' ').split():
            if '=' in part:
                k, v = part.split('=', 1)
                try:
                    d[k] = int(v)
                except ValueError:
                    pass
        return d
    finally:
        for x in (gp, op):
            try:
                os.remove(x)
            except OSError:
                pass


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    Rlist = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [16, 18, 20]
    C, T, M, A, B = read_input(INP)
    demands, projD = lp_min_d_flows(A, B, M)
    print(f'pieces={sum(len(x) for x in demands)} projD={projD:.0f}', file=sys.stderr)
    best = None
    built = 0
    for R in Rlist:
        b_built = 0
        for s in range(seeds):
            g = BB.build(C, R, A, demands, 5000+R*97+s)
            if g is None:
                continue
            built += 1
            b_built += 1
            d = score(R, g)
            if not d or 'cost' not in d or d.get('L', 1) != 0:
                continue
            key = (d['cost'], d.get('bounce', 0))
            if best is None or key < best[0]:
                best = (key, R, [row[:] for row in g], d)
                print(f'  R={R}(split={R-C}) s={s}: cost={d["cost"]} '
                      f'E={d.get("E")} D={d.get("D")} bounce={d.get("bounce")}', file=sys.stderr)
        print(f'R={R}: built {b_built}/{seeds}', file=sys.stderr)
    if best is None:
        print('none built', file=sys.stderr)
        return
    key, R, grid, d = best
    print(f'\nBEST cost={d["cost"]} E={d.get("E")} D={d.get("D")} L={d.get("L")} '
          f'bounce={d.get("bounce")} R={R}', file=sys.stderr)
    out = os.path.join(HERE, 'outputs', 'public1_bus_best.txt')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        f.write(str(R)+'\n')
        for row in grid:
            f.write(' '.join(row)+'\n')
    print('saved ->', out, file=sys.stderr)


if __name__ == '__main__':
    main()
