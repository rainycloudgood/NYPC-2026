import sys


def solve(C, T, M, A, B):
    R = C + 1

    # ---- 할당 문제: sigma[i] = 굴 인덱스, Σ|A_i - B_sigma(i)| 최소화 ----
    INF = float('inf')
    FULL = 1 << C
    dp = [INF] * FULL
    dp[0] = 0
    choice = [[-1] * FULL for _ in range(C)]
    for mask in range(FULL):
        if dp[mask] == INF:
            continue
        i = bin(mask).count('1')  # 다음에 배정할 열
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
    # 역추적
    sigma = [-1] * C
    mask = FULL - 1
    for i in range(C - 1, -1, -1):
        j = choice[i][mask]
        sigma[i] = j
        mask ^= (1 << j)

    # ---- 배치도 구성 ----
    grid = [['X'] * C for _ in range(R)]  # grid[r-1][c], 행 1..R

    next_slot = 2  # 전용 행 슬롯: 2..R (총 C개)
    for i in range(C):
        j = sigma[i]
        if A[i] == 0:
            continue  # 스트림 없음
        if j == i:
            grid[0][i] = f'{R}D'  # 굴 i 직송 (거리 R ≥ 2)
            continue
        r = next_slot
        next_slot += 1
        assert 2 <= r <= R
        # (1,i) → (r,i): 거리 1이면 다람쥐, 아니면 햄스터
        grid[0][i] = 'D' if r == 2 else f'{r - 1}D'
        d = j - i
        if abs(d) >= 2:
            grid[r - 1][i] = f'{abs(d)}{"R" if d > 0 else "L"}'
        else:
            grid[r - 1][i] = 'R' if d > 0 else 'L'  # 인접은 다람쥐 1방향
        # (r,j) → 굴 j: 거리 1이면 다람쥐, 아니면 햄스터
        grid[r - 1][j] = 'D' if r == R else f'{R + 1 - r}D'

    return R, grid


def main():
    data = sys.stdin.read().split()
    C = int(data[0]); T = int(data[1]); M = int(data[2])
    A = [int(x) for x in data[3:3 + C]]
    B = [int(x) for x in data[3 + C:3 + 2 * C]]

    R, grid = solve(C, T, M, A, B)

    out = [str(R)]
    for row in grid:
        out.append(' '.join(row))
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
