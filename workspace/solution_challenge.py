"""Adaptive NYPC challenge submission: whole streams vs half streams."""

import sys

import solution
import solution_split


def whole_error(A, B):
    C = len(A)
    full = 1 << C
    inf = 10**30
    dp = [inf] * full
    dp[0] = 0
    for mask in range(full):
        i = mask.bit_count()
        if i == C:
            continue
        for j in range(C):
            if not (mask >> j) & 1:
                nm = mask | (1 << j)
                dp[nm] = min(dp[nm], dp[mask] + abs(A[i] - B[j]))
    return dp[-1]


def split_error(A, B):
    pieces, target = solution_split.assign_halves(A, B)
    got = [0] * len(B)
    for p, (amount, _src, _half) in enumerate(pieces):
        got[target[p]] += amount
    return sum(abs(got[j] - B[j]) for j in range(len(B)))


def solve(C, T, M, A, B):
    ew = whole_error(A, B)
    # solution.solve normally uses R=C (base 1); in the rare all-cross case it
    # uses C+1 (base 2).  Using 2 is a safe comparison upper bound.
    whole_est = 2 + max(ew, 2)

    es = split_error(A, B)
    split_est = (1 << (C + 1)) + max(es, 4)  # R=2C+1, measured D=4
    if split_est < whole_est:
        return solution_split.solve(C, T, M, A, B), 'split', whole_est, split_est
    return solution.solve(C, T, M, A, B), 'whole', whole_est, split_est


def main():
    data = list(map(int, sys.stdin.read().split()))
    C, T, M = data[:3]
    A = data[3:3+C]
    B = data[3+C:3+2*C]
    (R, grid), _mode, _cw, _cs = solve(C, T, M, A, B)
    print(R)
    for row in grid:
        print(*row)


if __name__ == '__main__':
    main()
