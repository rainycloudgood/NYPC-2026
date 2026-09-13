"""Parallel official-semantics evaluator for saved public candidates."""
import concurrent.futures
import os
import sys

import validate as V
from challenge_submission_aggressive import KNOWN_CASES

BASE = os.path.join(os.path.dirname(__file__), 'outputs')


def evaluate(job):
    case, name = job
    A, B, _, _ = KNOWN_CASES[case-1]
    C, T, M = len(A), 2_000_000, max(A)
    q = open(os.path.join(BASE, name)).read().split()
    R, body = int(q[0]), q[1:]
    if len(body) != R*C:
        return name, None, 'shape'
    cells = {(r,c): V.parse_cell(body[(r-1)*C+c])
             for r in range(1,R+1) for c in range(C)}
    bp,last,bounces,left = V.simulate(C,T,M,A,B,R,cells)
    L=sum(B)-sum(bp); E=sum(abs(bp[i]-B[i]) for i in range(C));D=T if L else last-M
    return name,(1<<(R-C))+max(E,D)+T*L,(R,E,D,L,bounces,bp)


if __name__ == '__main__':
    case=int(sys.argv[1]);names=sys.argv[2:]
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(8,len(names))) as ex:
        rows=list(ex.map(evaluate,((case,x) for x in names)))
    for row in sorted(rows,key=lambda x:x[1] if x[1] is not None else 10**40):
        print(row)
