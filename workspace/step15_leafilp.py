# Min-E for a BALANCED equal-splitter network: each column i split into n leaves
# (values floor/ceil(A_i/n), with A_i%n ceils). Assign leaves to holes to hit B.
# Peak rate per leaf = 1/n; congestion cap: sum_i (leaves into hole j) <= n.
# Solve ILP: min E = sum_j |x_j - B_j|.
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import itertools

A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]
C = 8


def solve(n, congest=True, ret_assign=False):
    v = [a // n for a in A]
    c = [a % n for a in A]     # number of ceil(=v+1) leaves per column
    # vars: a[i][j] (leaves col i -> hole j), b[i][j] (ceil-leaves among them), e[j]
    NA = C * C
    def ai(i, j): return i * C + j
    def bi(i, j): return NA + i * C + j
    def ej(j): return 2 * NA + j
    nvar = 2 * NA + C
    cons = []
    # row: sum_j a_ij = n
    for i in range(C):
        row = np.zeros(nvar)
        for j in range(C): row[ai(i, j)] = 1
        cons.append(LinearConstraint(row, n, n))
    # ceil count: sum_j b_ij = c_i
    for i in range(C):
        row = np.zeros(nvar)
        for j in range(C): row[bi(i, j)] = 1
        cons.append(LinearConstraint(row, c[i], c[i]))
    # b_ij <= a_ij
    for i in range(C):
        for j in range(C):
            row = np.zeros(nvar); row[bi(i, j)] = 1; row[ai(i, j)] = -1
            cons.append(LinearConstraint(row, -np.inf, 0))
    # congestion: sum_i a_ij <= n
    if congest:
        for j in range(C):
            row = np.zeros(nvar)
            for i in range(C): row[ai(i, j)] = 1
            cons.append(LinearConstraint(row, -np.inf, n))
    # E: e_j >= x_j - B_j ; e_j >= B_j - x_j ; x_j = sum_i (a_ij v_i + b_ij)
    for j in range(C):
        row = np.zeros(nvar)
        for i in range(C):
            row[ai(i, j)] = v[i]; row[bi(i, j)] = 1
        r1 = row.copy(); r1[ej(j)] = -1     # x_j - e_j <= B_j
        cons.append(LinearConstraint(r1, -np.inf, B[j]))
        r2 = -row.copy(); r2[ej(j)] = -1    # -x_j - e_j <= -B_j
        cons.append(LinearConstraint(r2, -np.inf, -B[j]))
    cost = np.zeros(nvar)
    for j in range(C): cost[ej(j)] = 1
    integ = np.ones(nvar); integ[2*NA:] = 0  # e can be continuous
    lb = np.zeros(nvar); ub = np.full(nvar, float(n)); ub[2*NA:] = np.inf
    res = milp(c=cost, constraints=cons, integrality=integ, bounds=Bounds(lb, ub))
    if not res.success:
        return None
    if not ret_assign:
        return round(res.fun)
    x = np.round(res.x).astype(int)
    a = np.array([[x[ai(i, j)] for j in range(C)] for i in range(C)])
    b = np.array([[x[bi(i, j)] for j in range(C)] for i in range(C)])
    return round(res.fun), a, b, v, c


ret_assign = False
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:  # extract assignment for given n
        n = int(sys.argv[1])
        E, a, b, v, c = solve(n, congest=True, ret_assign=True)
        print(f'n={n} E={E}')
        print('v (floor per col):', v)
        print('c (#ceil per col):', c)
        # verify: flow to hole j from col i = a_ij*v_i + b_ij
        flow = np.array([[a[i][j]*v[i] + b[i][j] for j in range(C)] for i in range(C)])
        print('hole totals:', [int(flow[:, j].sum()) for j in range(C)], 'target B:', B)
        print('leaves per hole (congestion, must <=%d):' % n, [int(a[:, j].sum()) for j in range(C)])
        print('leaves per col (must =%d):' % n, [int(a[i].sum()) for i in range(C)])
        for i in range(C):
            print(f'  col{i} A={A[i]} v={v[i]} ceils={c[i]}: leaves->holes',
                  [(j, int(a[i][j]), int(b[i][j])) for j in range(C) if a[i][j] > 0])
    else:
        for n in [8, 16, 24, 32, 48, 64, 96, 128]:
            eC = solve(n, congest=True)
            eU = solve(n, congest=False)
            print(f'n={n:4d}: minE capped={eC} uncapped={eU}')
