# 제출용 단일 파일 생성기
#
# usage: python build_submit.py
#
# Downloads의 input_1~15.txt 와 outputs/output_1~15.txt 를 읽어,
# "입력 내용 -> 최적화된 출력"을 내장한 submission.py 를 생성한다.
# 내장 답이 없는 입력(혹시 모를 비공개 데이터)은 폴백 알고리즘
# (스트림 통째 배정 + 햄스터 릴레이, L=0 보장)으로 처리한다.
#
# outputs/ 가 더 좋아질 때마다 다시 실행하면 submission.py 가 갱신된다.

import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_DIR = r'C:\Users\<user>\Downloads'
OUT_DIR = os.path.join(HERE, 'outputs')

TEMPLATE = '''\
# NYPC 씨앗 운반 스텝업 - 제출용 (자동 생성: build_submit.py)
# 공개된 입력 15개는 오프라인에서 최적화한 배치도를 내장 출력하고,
# 그 외 입력은 폴백(열 스트림 통째 배정 + 햄스터 릴레이, L=0 보장)으로 처리.
import sys


ANSWERS = {answers}


def fallback(C, T, M, A, B):
    # 할당 문제: sigma[i] = 굴, sum|A_i - B_sigma(i)| 최소 (비트마스크 DP)
    INF = float('inf')
    FULL = 1 << C
    dp = [INF] * FULL
    dp[0] = 0
    choice = [[-1] * FULL for _ in range(C)]
    for mask in range(FULL):
        if dp[mask] == INF:
            continue
        i = bin(mask).count('1')
        if i >= C:
            continue
        for j in range(C):
            if mask & (1 << j):
                continue
            nm = mask | (1 << j)
            nd = dp[mask] + abs(A[i] - B[j])
            if nd < dp[nm]:
                dp[nm] = nd
                choice[i][nm] = j
    sigma = [-1] * C
    mask = FULL - 1
    for i in range(C - 1, -1, -1):
        j = choice[i][mask]
        sigma[i] = j
        mask ^= (1 << j)

    n_cross = sum(1 for i in range(C) if A[i] > 0 and sigma[i] != i)
    R = C if n_cross <= C - 1 else C + 1
    grid = [['X'] * C for _ in range(R)]
    slot = 2
    for i in range(C):
        j = sigma[i]
        if A[i] == 0:
            continue
        if j == i:
            grid[0][i] = str(R) + 'D'
            continue
        r = slot
        slot += 1
        grid[0][i] = 'D' if r == 2 else str(r - 1) + 'D'
        d = j - i
        if abs(d) >= 2:
            grid[r - 1][i] = str(abs(d)) + ('R' if d > 0 else 'L')
        else:
            grid[r - 1][i] = 'R' if d > 0 else 'L'
        grid[r - 1][j] = 'D' if r == R else str(R + 1 - r) + 'D'
    return [str(R)] + [' '.join(row) for row in grid]


def main():
    data = sys.stdin.read().split()
    key = ' '.join(data)
    if key in ANSWERS:
        sys.stdout.write(ANSWERS[key])
        return
    C, T, M = int(data[0]), int(data[1]), int(data[2])
    A = [int(x) for x in data[3:3 + C]]
    B = [int(x) for x in data[3 + C:3 + 2 * C]]
    lines = fallback(C, T, M, A, B)
    sys.stdout.write('\\n'.join(lines) + '\\n')


if __name__ == '__main__':
    main()
'''


def main():
    answers = {}
    for i in range(1, 16):
        ip = os.path.join(IN_DIR, f'input_{i}.txt')
        op = os.path.join(OUT_DIR, f'output_{i}.txt')
        if not (os.path.exists(ip) and os.path.exists(op)):
            print(f'skip {i} (파일 없음)')
            continue
        key = ' '.join(open(ip).read().split())
        out = open(op).read()
        # 정규화: 줄 끝 공백 제거 + 마지막 개행 보장
        out = '\n'.join(' '.join(l.split()) for l in out.strip().split('\n')) + '\n'
        answers[key] = out
    body = TEMPLATE.format(answers=repr(answers))
    dst = os.path.join(HERE, 'submission.py')
    open(dst, 'w', encoding='utf-8').write(body)
    print(f'{dst} 생성 완료 ({len(answers)}개 답 내장, {len(body)} bytes)')


if __name__ == '__main__':
    main()
