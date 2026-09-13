"""Exact equal-piece assignment lower bound for small challenge cases."""

import functools
import itertools
import sys


def pieces_for(a, k):
    q, r = divmod(a, k)
    return [q + (i < r) for i in range(k)]


def solve(A, B, k):
    pieces = [x for a in A for x in pieces_for(a, k)]
    n = len(pieces)
    groups = []
    for ids in itertools.combinations(range(n), k):
        mask = sum(1 << i for i in ids)
        groups.append((mask, sum(pieces[i] for i in ids)))
    by_first = [[] for _ in range(n)]
    for mask, amount in groups:
        first = (mask & -mask).bit_length() - 1
        by_first[first].append((mask, amount))

    @functools.lru_cache(None)
    def dp(bmask, used):
        if bmask == (1 << len(B)) - 1:
            return (0, ()) if used == (1 << n) - 1 else (10**30, ())
        remain = ((1 << n) - 1) ^ used
        first = (remain & -remain).bit_length() - 1
        best = (10**30, ())
        for mask, amount in by_first[first]:
            if mask & used:
                continue
            for j in range(len(B)):
                if (bmask >> j) & 1:
                    continue
                tail, choice = dp(bmask | (1 << j), used | mask)
                val = abs(amount - B[j]) + tail
                if val < best[0]:
                    best = (val, ((j, amount),) + choice)
        return best
    e, pairs = dp(0, 0)
    got = [0] * len(B)
    for j, amount in pairs:
        got[j] = amount
    return e, tuple(got)


def main():
    data = list(map(int, open(sys.argv[1]).read().split()))
    C = data[0]
    A = data[3:3+C]
    B = data[3+C:3+2*C]
    for k in range(1, int(sys.argv[2]) + 1):
        e, got = solve(A, B, k)
        print(f'k={k} E={e} got={got}')


if __name__ == '__main__':
    main()
