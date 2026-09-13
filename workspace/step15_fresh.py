# Fresh from-scratch builder for step-up test 15.
# Core idea: build an EXACT integer transport (E=0), realize each column with a
# ceil/floor split tree (timing-independent exactness), wire leaves to holes.
# Validator (official semantics) is the oracle.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V

C, T, M = 8, 2000, 999
A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]


def build_grid(R, tokens):
    """tokens: dict (r,c)->str. Missing => 'X'. Returns flat body list."""
    body = []
    for r in range(1, R + 1):
        for c in range(C):
            body.append(tokens.get((r, c), 'X'))
    return body


def evaluate(R, tokens, verbose=False):
    body = build_grid(R, tokens)
    cells = {}
    for r in range(1, R + 1):
        for c in range(C):
            tok = body[(r - 1) * C + c]
            ok, why = V.valid_cell(tok, r, c, R, C)
            if not ok:
                return None, f'INVALID ({r},{c+1}) {tok!r}: {why}'
            cells[(r, c)] = V.parse_cell(tok)
    Bp, t_last, bounces, leftover = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B) - sum(Bp)
    E = sum(abs(Bp[i] - B[i]) for i in range(C))
    D = T if L > 0 else t_last - M
    cost = (1 << (R - C)) + max(E, D) + T * L
    info = dict(Bp=Bp, L=L, E=E, D=D, cost=cost, bounces=bounces, leftover=leftover, t_last=t_last)
    return cost, info


def emit(R, tokens, path):
    body = build_grid(R, tokens)
    with open(path, 'w') as f:
        f.write(str(R) + '\n')
        for r in range(R):
            f.write(' '.join(body[r * C:(r + 1) * C]) + '\n')


# ---- sanity test: identity straight pipes ----
if __name__ == '__main__':
    R = 8
    tok = {}
    for c in range(C):
        for r in range(1, R + 1):
            tok[(r, c)] = 'D'   # straight down -> hole c
    cost, info = evaluate(R, tok)
    print('identity:', cost, info)
