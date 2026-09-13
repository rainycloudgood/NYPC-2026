"""Build a standalone challenge_submission.py from the tested strategies."""

import os

BASE = os.path.dirname(os.path.abspath(__file__))


def between(text, start, end):
    return text[text.index(start):text.index(end)]


whole_src = open(os.path.join(BASE, 'solution.py'), encoding='utf-8').read()
whole_src = between(whole_src, 'def solve(', '\ndef main()')
whole_src = whole_src.replace('def solve(', 'def solve_whole(', 1)

split_src = open(os.path.join(BASE, 'solution_split.py'), encoding='utf-8').read()
split_src = between(split_src, 'def assign_halves_exact(', '\ndef main()')
split_src = split_src.replace('def solve(', 'def solve_split(', 1)

header = '''# NYPC 씨앗 운반 챌린지 - 적응형 단일 제출본 (자동 생성)\nimport random\nimport sys\nfrom itertools import combinations\n\n'''

adapter = r'''
def whole_error(A, B):
    C = len(A)
    dp = [10**30] * (1 << C)
    dp[0] = 0
    for mask in range(1 << C):
        i = mask.bit_count()
        if i == C:
            continue
        for j in range(C):
            if not (mask >> j) & 1:
                nm = mask | (1 << j)
                dp[nm] = min(dp[nm], dp[mask] + abs(A[i] - B[j]))
    return dp[-1]


def split_error(A, B):
    pieces, target = assign_halves(A, B)
    got = [0] * len(B)
    for p, (amount, _src, _half) in enumerate(pieces):
        got[target[p]] += amount
    return sum(abs(got[j] - B[j]) for j in range(len(B)))


def main():
    data = list(map(int, sys.stdin.read().split()))
    C, T, M = data[:3]
    A = data[3:3+C]
    B = data[3+C:3+2*C]
    whole_est = 2 + max(whole_error(A, B), 2)
    es = split_error(A, B)
    split_est = (1 << (C + 1)) + max(es, 4)
    if split_est < whole_est:
        R, grid = solve_split(C, T, M, A, B)
    else:
        R, grid = solve_whole(C, T, M, A, B)
    print(R)
    for row in grid:
        print(*row)


if __name__ == '__main__':
    main()
'''

out = os.path.join(BASE, 'challenge_submission.py')
with open(out, 'w', encoding='utf-8', newline='\n') as f:
    f.write(header + whole_src + '\n\n' + split_src + '\n\n' + adapter)
print(out)
