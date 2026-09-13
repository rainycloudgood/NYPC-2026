# Enumerate srow staggering with sensible fixed split directions.
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import step15_maze as Z
from step15_maze import build, evaluate, emit, C

# sensible dirs mapping holes [i-1, i, i+1] -> directions
def dirperm_for(i):
    if i == 0:   return ('U', 'D', 'R')   # hole7 via U, hole0 D, hole1 R
    if i == C-1: return ('L', 'D', 'U')   # hole6 L, hole7 D, hole0 via U
    return ('L', 'D', 'R')

DP = [dirperm_for(i) for i in range(C)]

def run(R, rowset):
    best = None
    cnt = 0
    for srow in itertools.product(rowset, repeat=C):
        occ = build(R, list(srow), DP)
        if occ is None:
            continue
        cost, info = evaluate(R, list(srow) and occ)
        if cost is None:
            continue
        cnt += 1
        if best is None or cost < best[0]:
            best = (cost, list(srow), dict(E=info['E'], D=info['D'], L=info['L'], b=info['bounces']), dict(occ))
    return best, cnt

if __name__ == '__main__':
    for R in [8, 9, 10]:
        rowset = tuple(range(2, min(R-1, 6)))
        best, cnt = run(R, rowset)
        if best:
            print(f'R={R}: valid={cnt} BEST cost={best[0]} {best[2]} srow={best[1]}')
            emit(R, best[3], f'outputs/_cand/enum_R{R}.txt')
        else:
            print(f'R={R}: no valid ({cnt})')
