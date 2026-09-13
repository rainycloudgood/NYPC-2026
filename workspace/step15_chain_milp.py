"""MILP lower-bound search for a fresh 8x8 chain-split design for test 15."""

import itertools
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]
C = 8


def chain(source, depth):
    n, rate, pieces = A[source], 1.0, []
    for _ in range(depth):
        hi = (n + 1) // 2
        pieces.append((hi, rate / 2, source))
        n -= hi
        rate /= 2
    pieces.append((n, rate, source))
    return pieces


def solve(depths, cap=1.5, limit=0.5):
    pieces = sum((chain(i, d) for i, d in enumerate(depths)), [])
    p = len(pieces); nx = p * C; nv = nx + 2 * C
    objective = np.zeros(nv);objective[nx:] = 1
    integrality = np.zeros(nv);integrality[:nx] = 1
    lower = np.zeros(nv);upper = np.full(nv, np.inf);upper[:nx] = 1

    # Piece assignment equalities and burrow balance equalities.
    eq = lil_matrix((p + C, nv));rhs = np.zeros(p + C)
    for q in range(p):
        for j in range(C):eq[q, q*C+j] = 1
        rhs[q] = 1
    for j in range(C):
        for q, (amount, _, _) in enumerate(pieces):eq[p+j, q*C+j] = amount
        eq[p+j, nx+j] = -1;eq[p+j, nx+C+j] = 1;rhs[p+j] = B[j]

    # At most cap seeds/second into every burrow.
    rate = lil_matrix((C, nv))
    for j in range(C):
        for q, (_, r, _) in enumerate(pieces):rate[j, q*C+j] = r
    constraints = [LinearConstraint(eq.tocsr(), rhs, rhs),
                   LinearConstraint(rate.tocsr(), -np.inf, np.full(C, cap))]
    result = milp(objective, integrality=integrality, bounds=Bounds(lower, upper),
                  constraints=constraints, options={"time_limit": limit, "mip_rel_gap": 0.0})
    if result.x is None:return None
    dest = [int(np.argmax(result.x[q*C:(q+1)*C])) for q in range(p)]
    got = [0]*C;rates=[0.0]*C
    for piece,j in zip(pieces,dest):got[j]+=piece[0];rates[j]+=piece[1]
    error=sum(abs(got[j]-B[j]) for j in range(C))
    return error,pieces,dest,got,rates,result.message


def main():
    tests = [(3,)*8]
    # Exactly 28 splitter cells: four depth-4 and four depth-3 chains.  Together
    # with 36 terminal pieces this saturates the 64-cell accounting bound.
    for deep in itertools.combinations(range(8),4):
        d=[3]*8
        for i in deep:d[i]=4
        tests.append(tuple(d))
    best=None
    for k,depths in enumerate(tests):
        result=solve(depths)
        if result and (best is None or result[0]<best[0]):
            best=(result[0],depths,*result[1:])
            print("BEST",best[0],"depths",depths,"got",best[4],"rates",best[5],flush=True)
            if best[0] <= 2:break
    if best:
        error,depths,pieces,dest,got,rates,message=best
        print("FINAL E",error,"depths",depths,"pieces",len(pieces),"message",message)
        for q,(piece,j) in enumerate(zip(pieces,dest)):
            print(q,piece,"->",j)


if __name__=="__main__":main()
