"""Detailed simulator diagnostics for one saved output."""

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V


def load(inp_path, out_path):
    data = list(map(int, open(inp_path).read().split()))
    C, T, M = data[:3]
    A = data[3:3 + C]
    B = data[3 + C:3 + 2 * C]
    out = open(out_path).read().split()
    R = int(out[0])
    body = out[1:]
    cells = {}
    for r in range(1, R + 1):
        for c in range(C):
            cells[(r, c)] = V.parse_cell(body[(r - 1) * C + c])
    return C, T, M, A, B, R, cells


def simulate(C, T, M, A, B, R, cells):
    NC = R * C
    caps, targ = [0] * NC, [()] * NC
    for r in range(1, R + 1):
        for c in range(C):
            cell = cells[(r, c)]
            i = (r - 1) * C + c
            if cell[0] == 'H':
                _, dist, hd = cell
                dr, dc = V.DIRS[hd]
                tr, tc = r + dr * dist, c + dc * dist
                targ[i] = ((NC + tc) if tr == R + 1 else (tr - 1) * C + tc,)
                caps[i] = 1
            else:
                ts = []
                for ch in cell[1]:
                    dr, dc = V.DIRS[ch]
                    tr, tc = r + dr, c + dc
                    ts.append((NC + tc) if tr == R + 1 else (tr - 1) * C + tc)
                targ[i], caps[i] = tuple(ts), len(ts)

    ptr, cnt, nz = [0] * NC, [0] * (NC + C), set()
    Bp, last = [0] * C, [0] * C
    bounce_target, bounce_sender = collections.Counter(), collections.Counter()
    dropped = 0
    drop_from = [M - a + 1 for a in A]
    for t in range(1, T + 1):
        if dropped >= sum(A) and not nz and not any(cnt[NC:]):
            break
        for i, a in enumerate(A):
            if a and drop_from[i] <= t <= M:
                if cnt[i] == 0:
                    nz.add(i)
                cnt[i] += 1
                dropped += 1
        recv = {}
        for i in list(nz):
            s, k = cnt[i], len(targ[i])
            if not caps[i]:
                continue
            amt = min(s, caps[i])
            for j in range(amt):
                recv.setdefault(targ[i][(ptr[i] + j) % k], []).append(i)
            if k > 1:
                ptr[i] = (ptr[i] + amt) % k
            cnt[i] -= amt
            if cnt[i] == 0:
                nz.discard(i)
        over = {target for target in recv if cnt[target] > 0}
        for target, senders in recv.items():
            if target in over:
                bounce_target[target] += len(senders)
                for sender in senders:
                    bounce_sender[sender] += 1
                    if cnt[sender] == 0:
                        nz.add(sender)
                    cnt[sender] += 1
            else:
                cnt[target] += len(senders)
                if target < NC:
                    nz.add(target)
        for c in range(C):
            if cnt[NC + c]:
                cnt[NC + c] -= 1
                Bp[c] += 1
                last[c] = t
    return Bp, last, bounce_target, bounce_sender


def label(i, C, R):
    return f'burrow {i - R*C + 1}' if i >= R*C else f'cell ({i // C + 1},{i % C + 1})'


def main():
    args = sys.argv[1:]
    if len(args) == 1 and args[0].isdigit():
        base = os.path.dirname(os.path.abspath(__file__))
        args = [rf'C:\Users\<user>\Downloads\input_{args[0]}.txt',
                os.path.join(base, 'outputs', f'output_{args[0]}.txt')]
    C, T, M, A, B, R, cells = load(*args)
    Bp, last, bt, bs = simulate(C, T, M, A, B, R, cells)
    print(f'R={R} Bp={Bp}')
    print(f'error={[Bp[i] - B[i] for i in range(C)]}')
    print(f'last={last} D={max(last) - M}')
    print('top bounce targets:')
    for i, n in bt.most_common(12):
        print(f'  {label(i, C, R):18} {n}')
    print('top bounced senders:')
    for i, n in bs.most_common(12):
        print(f'  {label(i, C, R):18} {n}')


if __name__ == '__main__':
    main()
