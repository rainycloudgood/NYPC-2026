# 15개 테스트 일괄 검증: outputs/output_i.txt vs Downloads/input_i.txt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V

BASE = [None, 1, 3, 3, 2, 2, 3, 3, 2, 2, 3, 3, 4, 3, 5, 3]
MAXS = [None] + [50000, 50000, 50000, 50000, 50000, 100000, 50000, 50000,
                 50000, 100000, 50000, 100000, 50000, 100000, 100000]

_HERE = os.path.dirname(os.path.abspath(__file__))
IN_DIR = os.path.join(_HERE, 'inputs')
if not os.path.exists(os.path.join(IN_DIR, 'input_15.txt')):
    IN_DIR = r'C:\Users\<user>\Downloads'
OUT_DIR = os.path.join(_HERE, 'outputs')


def check(i, out_path=None):
    inp = open(os.path.join(IN_DIR, f'input_{i}.txt')).read().split()
    out_path = out_path or os.path.join(OUT_DIR, f'output_{i}.txt')
    out = open(out_path).read().split()
    it = iter(inp)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    R = int(out[0])
    assert C <= R <= C + 20, f'R={R} 범위 위반'
    body = out[1:]
    assert len(body) == R * C, '토큰 개수 오류'
    cells = {}
    for r in range(1, R + 1):
        for c in range(C):
            tok = body[(r - 1) * C + c]
            ok, why = V.valid_cell(tok, r, c, R, C)
            assert ok, f'({r},{c + 1}) {tok!r}: {why}'
            cells[(r, c)] = V.parse_cell(tok)
    Bp, t_last, bounces, leftover = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B) - sum(Bp)
    E = sum(abs(Bp[i] - B[i]) for i in range(C))
    D = T if L > 0 else t_last - M
    cost = (1 << (R - C)) + max(E, D) + T * L
    return cost, E, D, L


def score(cost, i):
    if cost <= BASE[i]:
        return MAXS[i]
    return int(MAXS[i] * 0.9 ** (cost / BASE[i] - 1))


if __name__ == '__main__':
    total = 0
    maxtotal = 0
    for i in range(1, 16):
        cost, E, D, L = check(i)
        s = score(cost, i)
        total += s
        maxtotal += MAXS[i]
        mark = ' <-- 만점' if cost <= BASE[i] else ''
        print(f'테스트 {i:2d}: cost={cost:>6} (기준 {BASE[i]})  E={E:<5} D={D:<4} '
              f'점수 {s:>6}/{MAXS[i]}{mark}')
    print(f'\n총점 {total} / {maxtotal}  ({100 * total / maxtotal:.1f}%)')
