# 데이터 1 전용: min-D LP 유량 + treegen 정확분할 트리 성형 + C++ 시뮬 평가
#
# usage: python public1_treegen_driver.py [seeds_per_R=60] [Rlist=13,15,17,19]
import os, sys, subprocess, random, tempfile
import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import treegen as TG

EXE = os.path.join(HERE, 'public1_offline_optimizer.exe')
INP = os.path.join(HERE, 'public_1_input.txt')


def read_input(path):
    d = list(map(int, open(path).read().split()))
    C, T, M = d[:3]
    A = d[3:3+C]; B = d[3+C:3+2*C]
    return C, T, M, A, B


def lp_min_d_flows(A, B, M):
    C = len(A)
    fi = lambda i, j: i*C + j
    starts = sorted(set(M - a for a in A))
    bps = starts + [M]
    segs = []
    for k in range(len(bps)-1):
        t0, t1 = bps[k], bps[k+1]
        L = t1 - t0
        active = [i for i in range(C) if M - A[i] <= t0]
        segs.append((active, L))
    S = len(segs)
    nf = C*C
    nb = C*S
    n = nf + nb + 1
    zi = nf + nb
    bidx = lambda j, k: nf + j*S + k
    c = [0]*nf + [0]*nb + [1]
    Ae = []; be = []
    for i in range(C):
        r = [0]*n
        for j in range(C):
            r[fi(i, j)] = 1
        Ae.append(r); be.append(A[i])
    for j in range(C):
        r = [0]*n
        for i in range(C):
            r[fi(i, j)] = 1
        Ae.append(r); be.append(B[j])
    Au = []; bu = []
    for j in range(C):
        for k in range(S):
            active, L = segs[k]
            r = [0]*n
            r[bidx(j, k)] = -1
            if k > 0:
                r[bidx(j, k-1)] = 1
            for i in active:
                r[fi(i, j)] += L/A[i]
            Au.append(r); bu.append(L)
        for k in range(S):
            r = [0]*n
            r[bidx(j, k)] = 1
            r[zi] = -1
            Au.append(r); bu.append(0.0)
    res = linprog(c=c, A_eq=Ae, b_eq=be, A_ub=Au, b_ub=bu,
                  bounds=[(0, None)]*n, method='highs')
    assert res.success, res.message
    f = np.round(np.array(res.x[:nf]).reshape(C, C)).astype(int)
    # exact integer repair: ensure row sums == A, col sums == B
    for i in range(C):
        diff = A[i] - int(f[i].sum())
        if diff:
            j = int(np.argmax(f[i]))
            f[i][j] += diff
    demands = []
    for i in range(C):
        demands.append([[j, int(f[i][j])] for j in range(C) if f[i][j] > 0])
    return demands, float(res.x[zi])


def score(R, grid):
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, dir=HERE) as tf:
        tf.write(str(R) + '\n')
        for row in grid:
            tf.write(' '.join(row) + '\n')
        gpath = tf.name
    opath = gpath + '.out'
    try:
        p = subprocess.run([EXE, INP, gpath, opath, '0', '0', '1'],
                           capture_output=True, text=True, timeout=60)
        line = p.stderr.strip().splitlines()[0] if p.stderr.strip() else ''
        # parse "START cost=.. E=.. D=.. L=.. bounce=.."
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
        for pth in (gpath, opath):
            try:
                os.remove(pth)
            except OSError:
                pass


def main():
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    Rlist = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else [13, 15, 17, 19]
    C, T, M, A, B = read_input(INP)
    demands, projD = lp_min_d_flows(A, B, M)
    npiece = sum(len(x) for x in demands)
    print(f'LP min-D flows: {npiece} pieces, projected D={projD:.0f}', file=sys.stderr)

    best = None
    built = 0
    for R in Rlist:
        base = 1 << (R - C)
        for s in range(seeds):
            rng = random.Random(9000 + R*1000 + s)
            gr = TG.Grid(C, R)
            order = [i for i in range(C) if A[i] > 0]
            rng.shuffle(order)
            ok = True
            for i in order:
                tree = TG.plan_tree(A[i], [d[:] for d in demands[i]], rng)
                if not TG.place_stream(gr, 0, i, tree, rng):
                    ok = False
                    break
            if not ok:
                continue
            built += 1
            d = score(R, gr.g)
            if not d or 'cost' not in d:
                continue
            if d.get('L', 1) != 0:
                continue
            key = (d['cost'], d.get('E', 0), d.get('bounce', 0))
            if best is None or key < best[0]:
                best = (key, R, [row[:] for row in gr.g], d)
                print(f'  R={R} s={s}: cost={d["cost"]} E={d.get("E")} '
                      f'D={d.get("D")} bounce={d.get("bounce")}', file=sys.stderr)
    print(f'built={built}', file=sys.stderr)
    if best is None:
        print('no valid grid built', file=sys.stderr)
        return
    key, R, grid, d = best
    print(f'\nBEST cost={d["cost"]} E={d.get("E")} D={d.get("D")} '
          f'L={d.get("L")} bounce={d.get("bounce")} R={R}', file=sys.stderr)
    out = os.path.join(HERE, 'outputs', 'public1_treegen_best.txt')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        f.write(str(R) + '\n')
        for row in grid:
            f.write(' '.join(row) + '\n')
    print('saved ->', out, file=sys.stderr)


if __name__ == '__main__':
    main()
