# 씨앗 운반 - 배치도 생성기 v3 (공식 규칙 준수판)
#
# 입력: C T M / A[0..C-1] / B[0..C-1]
# 출력: R / R줄 × C개 토큰 (공백 구분)
#
# 공식 규칙 (예제 코드로 확인된 사항)
# ------------------------------------
# * 다람쥐: U/D/L/R 중 서로 다른 방향들을 골라 나열 (중복 불가, 최대 4개).
#   초당 방향당 1개씩만 보냄. 반복 문자열("DD", "RRD" 등)은 형식 위반.
# * 햄스터: 같은 행/열의 거리 2 이상 칸으로 초당 1개. 굴로 직접 던질 수 있고
#   중간 칸을 건너뛴다(간섭 없음).
# * 과부하: 보내기 후 씨앗이 하나라도 남으면 그 칸은 그 턴에 받은 씨앗을
#   전부 돌려보낸다. 굴도 초당 1개만 저장하므로 초과 유입 시 과부하된다.
#
# 전략: "열 스트림 통째 배정 + 햄스터 릴레이 직송"
# ------------------------------------------------
# 꽃 i의 생산은 초당 1개(창 [M-A_i+1, M])이므로, 스트림을 자르지 않고 통째로
# 어느 굴에 보낼지(순열 σ)만 정하면 모든 경로가 초당 1개 이하로 유지되어
# 과부하/롤백이 원천적으로 없다 → L=0 보장, D≈3.
#   σ = min Σ|A_i - B_σ(i)| (비트마스크 DP 할당 문제) → E 최소화.
#
# 경로 (스트림 i, 목적지 j=σ(i)):
#   j == i : (1,i) 햄스터 "R D" (거리 R ≥ 2) → 굴 i 직송
#   j != i : 전용 행 r_i (스트림마다 유일, 2..R) 사용
#     (1,i)      r_i=2: 다람쥐 "D" / r_i≥3: 햄스터 "(r_i-1)D" → (r_i, i)
#     (r_i, i)   |j-i|≥2: 햄스터 "(|j-i|)R/L", |j-i|=1: 다람쥐 "R"/"L"
#     (r_i, j)   r_i=R: 다람쥐 "D" / 그 외: 햄스터 "(R+1-r_i)D" → 굴 j
#   나머지 칸은 전부 "X" (씨앗이 지나가지 않으므로 안전).
#
# R = C+1: 슬롯 2..R = C개 → 전부 교차여도 수용. 2^(R-C) = 2.
# 공식 의미론에선 수확 당일 발송이 가능해 직송 D=0, 릴레이 D=2.
# 비용 ≈ 2 + max(E_assignment, 2).
#
# 검증: 공식 예제 코드의 simulate()를 그대로 옮긴 체커로 대조.

import sys


def solve(C, T, M, A, B):
    R = C + 1  # sigma 계산 후 교차 스트림 수에 맞춰 축소

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
    # 교차 스트림(j != i)은 전용 행 슬롯(2..R)이 1개씩 필요.
    # 슬롯 수 = R-1 이므로, 교차가 C-1개 이하면 R=C로 충분 (기본비용 1).
    n_cross = sum(1 for i in range(C) if A[i] > 0 and sigma[i] != i)
    R = C if n_cross <= C - 1 else C + 1

    grid = [['X'] * C for _ in range(R)]  # grid[r-1][c], 행 1..R

    next_slot = 2  # 전용 행 슬롯: 2..R
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
