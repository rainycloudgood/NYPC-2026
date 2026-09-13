"""Recover a likely intended R=C, two-hop construction for Step-Up 15.

Each source chooses either a direct stream or one 2/3-way squirrel split.
The resulting ceil/floor pieces are assigned to burrows.  The MILP minimizes
exact delivered-count error and then total burrow input rate.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]
C = 8


def pieces(n, k):
    q, r = divmod(n, k)
    return [q + (u < r) for u in range(k)]


def solve(rate_cap=1.01):
    # One x variable for every (source, split count, piece, destination).
    keys = []
    for i, n in enumerate(A):
        for k in (1, 2, 3):
            for q, amount in enumerate(pieces(n, k)):
                for j in range(C):
                    keys.append((i, k, q, j, amount))
    nx = len(keys)
    ykeys = [(i, k) for i in range(C) for k in (1, 2, 3)]
    yid = {z: nx + q for q, z in enumerate(ykeys)}
    ep = nx + len(ykeys)
    em = ep + C
    nv = em + C
    obj = np.zeros(nv)
    obj[ep:em] = 1.0
    obj[em:] = 1.0
    # Tiny preference for fewer pieces after minimizing integer error.
    for q, (_, k) in enumerate(ykeys):
        obj[nx + q] = k * 1e-4
    integ = np.zeros(nv)
    integ[:nx + len(ykeys)] = 1
    lb = np.zeros(nv)
    ub = np.full(nv, np.inf)
    ub[:nx + len(ykeys)] = 1

    rows = []
    rhs = []
    # Choose one split count per source.
    for i in range(C):
        row = {}
        for k in (1, 2, 3): row[yid[i, k]] = 1
        rows.append(row); rhs.append(1)
    # Every active piece is assigned once.
    for i in range(C):
        for k in (1, 2, 3):
            for q in range(k):
                row = {yid[i, k]: -1}
                for v, z in enumerate(keys):
                    if z[:3] == (i, k, q): row[v] = 1
                rows.append(row); rhs.append(0)
    # Delivered amount at each burrow, with absolute-error slacks.
    for j in range(C):
        row = {ep + j: -1, em + j: 1}
        for v, (_, _, _, jj, amount) in enumerate(keys):
            if jj == j: row[v] = amount
        rows.append(row); rhs.append(B[j])

    Aeq = lil_matrix((len(rows), nv))
    for r, row in enumerate(rows):
        for c, v in row.items(): Aeq[r, c] = v
    # Burrow fluid-rate cap.
    Arate = lil_matrix((C, nv))
    for v, (_, k, _, j, _) in enumerate(keys): Arate[j, v] = 1.0 / k
    cons = [LinearConstraint(Aeq.tocsr(), rhs, rhs),
            LinearConstraint(Arate.tocsr(), -np.inf, np.full(C, rate_cap))]
    res = milp(obj, integrality=integ, bounds=Bounds(lb, ub), constraints=cons,
               options={"time_limit": 30, "mip_rel_gap": 0.0})
    if res.x is None:
        print("NO SOLUTION", res.message); return
    got = [0] * C; rate = [0.0] * C; chosen = [[] for _ in range(C)]
    for v, (i, k, q, j, amount) in enumerate(keys):
        if res.x[v] > 0.5:
            got[j] += amount; rate[j] += 1.0 / k
            chosen[i].append((k, q, amount, j))
    print("status", res.message)
    print("E", sum(abs(got[j] - B[j]) for j in range(C)))
    print("got", got)
    print("rate", rate)
    for i, z in enumerate(chosen): print(i, z)


if __name__ == "__main__":
    for cap in (1.0, 1.25, 1.5, 2.0):
        print("\nCAP", cap); solve(cap)
