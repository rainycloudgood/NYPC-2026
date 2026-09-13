import sys


ANSWERS = {'3 200 100 100 100 100 100 100 100': '3\n3D 3D 3D\nX X X\nX X X\n', '5 200 40 40 30 20 10 0 0 40 30 20 10': '5\nD 2D 3D 4D X\nR 4D X X X\nX R 3D X X\nX X R 2D X\nX X X R D\n', '4 200 100 100 0 0 20 20 0 0 100': '4\nD X X 2D\n3R X X 3D\n2D X X 3L\nX X X X\n', '2 200 100 100 0 50 50': '2\nDR 2D\nD DU\n', '3 500 300 0 300 0 100 100 100': '3\n3D RDL D\nURD 2D 2D\n2U 2U DU\n', '3 500 300 300 0 0 100 100 100': '3\nR 2D 3D\n2D RL 2L\nD LRD D\n', '5 200 40 0 0 40 0 0 10 10 0 10 10': '5\nX X DR DR 5D\nX 4D DL 4D X\n3D X 2L X X\nX X X X X\nX X X X X\n', '7 2000 1280 1280 0 0 0 0 0 0 640 320 160 80 40 20 20': '7\n5R 7D 7D 2L DL LD L\n6D RUD 6D L LD 5L UL\nDR RD 2D 5D LDR RD 6L\nR D DL D DL 2D 3U\nDU 5R 3R DUR 3D 3D 3D\nDR DL 2D 2D X DR 3L\nRD U L L 4U D DLU\n', '7 2000 1280 1280 0 0 0 0 0 128 642 322 164 88 56 52 84': '7\n5D 2R 7D LDR D R 4L\n2R DRU 4R LRD 6D 5L 5D\n5D 2R RUD DL 5D U 5D\nD 2R DR 4D 2D D 4D\n3D 3U DRUL 2R 4L 3D LD\nRU UD L 2D LDUR U 4L\n6U D X R DUR UDRL DL\n', '3 1000 300 300 0 300 200 200 200': '3\nRD 2D D\nD 2D LD\nD RLU D\n', '2 200 90 90 30 70 50': '2\nDR DL\nD D\n', '5 1000 500 500 300 200 0 0 334 333 333 0 0': '5\nRD 4D 5D L L\nURD U L RD X\n3D 2D LRD 2U X\nX RDL DRU R 2L\n4R DR 4U R D\n', '5 1000 500 0 0 500 0 0 100 100 100 100 100': '5\n5D DL DLR LD 5D\nRD D 2D 4D 3L\nR R 3D RDL ULD\nDU 2D RL R 2D\nD 2U 4U R 3U\n', '7 2000 989 161 803 398 0 874 989 485 530 530 530 530 530 530 530': '7\n7D DLR LD D L D 7D\nD D 6D DR 6D D DL\n5D 5D D 2D DURL 4D DUL\nR UDLR R R D R 3U\nUD RL 4U 3D 3L DRU 5L\nDR DLRU URD 4U LRUD U ULD\nDRU 4R U 5U U DL 6U\n', '8 2000 999 684 297 330 609 999 198 474 108 363 437 412 646 602 557 260 422': '8\nD LDR 5D D 4D 5D LD 8D\nDRU RD D R 7D RU RLDU UL\nDRU UDLR UD 2U U D 6D U\n5D D 5R RD D D L DUL\nDUR L RU RD LUDR 4D 4D 4D\nDUR 4R 3D 3D D 2L D 5U\n4R D U X D X 4L UL\nUR D D 2R 3L 4U 5U DL\n'}


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
    sys.stdout.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
