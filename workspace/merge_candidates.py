# 후보 병합기 (단일 스레드 — 파일 경쟁 없음)
# outputs/_cand/cand_<idx>_*.txt 후보들 + 현재 outputs/output_<idx>.txt 를
# 파이썬 공식 시뮬로 재검증·채점해 테스트별 최선을 outputs/output_<idx>.txt 에 기록.
#
# usage: python merge_candidates.py [idx ...]   (인자 없으면 1..15 전부)
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate as V
import batch_check as bc

CAND = os.path.join(HERE, 'outputs', '_cand')


def cost_of(idx, path):
    """공식 시뮬로 (cost, D, E, bounces). 유효하지 않으면 None."""
    try:
        C, T, M, A, B = bc_read(idx)
        o = open(path).read().split()
        R = int(o[0]); body = o[1:]
        if not (C <= R <= C + 20) or len(body) != R * C:
            return None
        cells = {}
        for r in range(1, R + 1):
            for c in range(C):
                tok = body[(r - 1) * C + c]
                ok, _ = V.valid_cell(tok, r, c, R, C)
                if not ok:
                    return None
                cells[(r, c)] = V.parse_cell(tok)
        Bp, tl, bnc, lf = V.simulate(C, T, M, A, B, R, cells)
        L = sum(B) - sum(Bp)
        E = sum(abs(Bp[i] - B[i]) for i in range(C))
        D = T if L > 0 else tl - M
        cost = (1 << (R - C)) + max(E, D) + T * L
        return (cost, D, E, bnc, R, body)
    except Exception:
        return None


def bc_read(idx):
    inp = open(os.path.join(HERE, 'inputs', f'input_{idx}.txt')).read().split()
    it = iter(inp)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def main():
    idxs = [int(x) for x in sys.argv[1:]] or list(range(1, 16))
    for idx in idxs:
        out = os.path.join(HERE, 'outputs', f'output_{idx}.txt')
        best = cost_of(idx, out)
        best_src = 'current'
        for cand in glob.glob(os.path.join(CAND, f'cand_{idx}_*.txt')):
            r = cost_of(idx, cand)
            if r is None:
                continue
            if best is None or r[:4] < best[:4]:
                best, best_src = r, os.path.basename(cand)
        if best is None:
            print(f'테스트 {idx}: 유효 후보 없음')
            continue
        cur = cost_of(idx, out)
        if best_src != 'current' and (cur is None or best[:4] < cur[:4]):
            cost, D, E, bnc, R, body = best
            Ccols = len(body) // R
            with open(out, 'w') as f:
                f.write(str(R) + '\n')
                for r in range(R):
                    f.write(' '.join(body[r * Ccols:(r + 1) * Ccols]) + '\n')
            print(f'테스트 {idx}: 갱신 cost {cur[0] if cur else "?"} -> {cost}  ({best_src})')
        else:
            print(f'테스트 {idx}: 유지 cost {cur[0] if cur else "?"}')


if __name__ == '__main__':
    main()
