# Fresh exact realizer for test 15.
# 1) banded near-doubly-stochastic integer transport (E=0, low peak colsum)
# 2) per-column ceil/floor split tree whose leaves land in the TARGET hole-column
# 3) vertical hamster drop leaf-column -> hole ; measure with official sim
import sys, os
import numpy as np
from scipy.optimize import linprog
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step15_fresh as F
from step15_fresh import evaluate, emit

C, T, M = 8, 2000, 999
A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]


def banded_transport(BW):
    """Integer exact transport, support |i-j|<=BW, minimizing peak colsum, then
    rounded/repaired to exact integer flows f[i][j] (row=A, col=B)."""
    allowed = [(i, j) for i in range(C) for j in range(C) if abs(i - j) <= BW]
    vi = {e: k for k, e in enumerate(allowed)}
    n = len(allowed) + 1
    tvar = n - 1
    Aeq = []; beq = []
    for i in range(C):
        r = [0.] * n
        for j in range(C):
            if (i, j) in vi: r[vi[(i, j)]] = 1
        Aeq.append(r); beq.append(1.0)
    for j in range(C):
        r = [0.] * n
        for i in range(C):
            if (i, j) in vi: r[vi[(i, j)]] = A[i]
        Aeq.append(r); beq.append(float(B[j]))
    Aub = []; bub = []
    for j in range(C):
        r = [0.] * n
        for i in range(C):
            if (i, j) in vi: r[vi[(i, j)]] = 1
        r[tvar] = -1; Aub.append(r); bub.append(0.0)
    c = [0.] * n; c[tvar] = 1
    res = linprog(c, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq,
                  bounds=[(0, 1)] * (n - 1) + [(0, None)], method='highs')
    X = np.zeros((C, C))
    for (i, j), k in vi.items():
        X[i, j] = res.x[k]
    # integer flows = X * A, then repair rows/cols to exact
    f = np.round(X * np.array(A)[:, None]).astype(int)
    # repair: make row sums = A and col sums = B exactly, minimal changes, keep band
    for _ in range(2000):
        rd = [A[i] - f[i].sum() for i in range(C)]
        cd = [B[j] - int(f[:, j].sum()) for j in range(C)]
        if all(x == 0 for x in rd) and all(x == 0 for x in cd):
            break
        # find i with rd>0 and j with cd>0 within band, add; symmetric for <0
        done = False
        for i in range(C):
            for j in range(C):
                if abs(i - j) > BW: continue
                if rd[i] > 0 and cd[j] > 0:
                    d = min(rd[i], cd[j]); f[i, j] += d; done = True; break
                if rd[i] < 0 and cd[j] < 0 and f[i, j] > 0:
                    d = min(-rd[i], -cd[j], f[i, j]); f[i, j] -= d; done = True; break
            if done: break
        if not done:
            # need a 3-way cycle fix; nudge along band
            for i in range(C):
                if rd[i] > 0:
                    for j in range(C):
                        if abs(i - j) <= BW and cd[j] < 0:
                            # move from another source i2 that overfills j
                            for i2 in range(C):
                                if abs(i2 - j) <= BW and f[i2, j] > 0 and rd[i2] < 0:
                                    f[i2, j] -= 1; f[i, j] += 1
                                    done = True; break
                        if done: break
                if done: break
            if not done:
                break
    assert all(f[i].sum() == A[i] for i in range(C)), ('row', [f[i].sum() for i in range(C)], A)
    assert all(int(f[:, j].sum()) == B[j] for j in range(C)), 'col'
    return f


for BW in [1, 2, 3]:
    f = banded_transport(BW)
    peak = max(sum(f[i][j] / A[i] for i in range(C)) for j in range(C))
    print(f'BW={BW} exact integer transport, peak colsum={peak:.4f}, edges={(f>0).sum()}')
    for i in range(C):
        print('  col', i, 'A=', A[i], '->', [(j, int(f[i][j])) for j in range(C) if f[i][j] > 0])
    print()
