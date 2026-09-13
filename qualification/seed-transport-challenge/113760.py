# 씨앗 운반 - 배치도 생성기 (Python)
#
# 입력: C T M / A[0..C-1] / B[0..C-1]
# 출력: R / R줄 × C개 토큰 (공백 구분)
#
# 핵심 아이디어
# -------------
# 다람쥐의 방향 문자열은 씨앗 1개 처리마다 포인터가 1칸 전진하며 순환한다.
# 어떤 칸이 최종적으로 처리하는 씨앗의 총 개수 N은 (과부하가 없다면) 유량
# 보존으로 미리 정확히 계산할 수 있고, 그 칸이 옆으로 보내는 개수는
# "패턴 P를 무한 반복한 앞 N글자 중 옆방향 문자의 개수" — 즉 (P, N)만으로
# 결정되며 도착 타이밍과 무관하다. 따라서 짧은 주기 패턴으로도 정확히
# Q개를 옆으로 보낼 수 있다:
#   k=len(P), a=N//k, m=N%k 일 때, P의 옆방향 문자 p개 중 x개를 앞 m칸에
#   배치하면 옆으로 보내는 총 개수 = a*p + x  (정확)
#
# 구조
# ----
# R = C (2^(R-C)=1 최소화). diff/prefix로 각 열 경계의 순유량 F[b]를 구하고,
# 같은 부호로 연속된 경계들을 run으로 묶어 경계마다 전용 행을 배정한다
# (오른쪽 run은 오름차순, 왼쪽 run은 내림차순 — 연쇄 이동의 의존성 때문).
# 경계 담당 칸만 패턴 분배기이고 나머지는 전부 "D"×16 통과 칸.
# 통과 용량 16 > 최악 초당 부하(≤C+2)이므로 과부하가 원천적으로 없다.
#
# 분배기 칸의 통과량 N (정확한 정수):
#   오른쪽 경계 b (칸=열 b-1): N = A[b-1] + F[b-1]  (부호 포함! 위쪽 행에서
#     왼쪽 경계 b-1이 이 열에서 빼간 만큼 빼야 한다)
#   왼쪽 경계 b (칸=열 b): N = A[b] + (F[b+1]<0 이면 -F[b+1], 아니면 0)
#     (F[b+1]>0인 경우 그 분배기는 나중 run = 아래쪽 행이므로 영향 없음)
#
# 검증: 문제 명세 그대로의 시뮬레이터(포인터 순환, 과부하/롤백, 굴 초당
# 1개 저장 포함)로 대조 — 스케일 3천/2만/100만 랜덤 케이스 전부
# L=0, E=0, 과부하 0 확인. 남은 비용은 D(굴 대기열로 인한 지연)뿐.

import sys

W_PASS = 16   # 통과 칸 "D" 반복 수 (용량)
MIN_K = 16    # 분배기 최소 패턴 길이
KMAX = 4000   # 분배기 기본 최대 패턴 길이


def sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def arrange(k, m, x, p, mino, majo):
    """앞 m칸에 minority x개, 뒤 (k-m)칸에 (p-x)개를 배치한 길이 k 패턴."""
    return (mino * x + majo * (m - x)
            + mino * (p - x) + majo * ((k - m) - (p - x)))


def find_pattern(N, Q, lat):
    """N개 처리 중 정확히 Q개를 lat 방향으로, 나머지를 D로 보내는 패턴."""
    assert 0 <= Q <= N
    if N <= KMAX:
        # 정확히 한 바퀴만 도므로 버스트를 그대로 사용 가능
        return lat * Q + 'D' * (N - Q)
    for k in range(KMAX, MIN_K - 1, -1):
        a, m = divmod(N, k)
        if a == 0:
            continue
        base = Q // a
        for p in (base, base + 1, base - 1):
            if p < 0 or p > k:
                continue
            x = Q - p * a
            if x < 0 or x > m or x > p:
                continue
            if (p - x) > (k - m):
                continue
            return arrange(k, m, x, p, lat, 'D')
    # 극단적 Q(0이나 N에 매우 근접): 소수(minority) 문자 개수 기준으로
    # 패턴을 잡는다. k ~ N*p/target 로 버스트(N)보다 항상 짧거나 같다.
    if Q <= N - Q:
        target, mino, majo = Q, lat, 'D'
    else:
        target, mino, majo = N - Q, 'D', lat
    if target == 0:
        return majo * MIN_K
    for p in range(1, 4097):
        a = target // p
        if a == 0:
            break
        x = target - p * a
        lo = N // (a + 1) + 1   # floor(N/k)==a 가 되는 k 범위
        hi = N // a
        for k in (hi, max(lo, MIN_K), (lo + hi) // 2):
            if k < max(p, MIN_K) or k < lo or k > hi:
                continue
            m = N - a * k
            if x <= m and x <= p and (p - x) <= (k - m):
                return arrange(k, m, x, p, mino, majo)
    # 최후 수단: 버스트 (길지만 항상 정확)
    return lat * Q + 'D' * (N - Q)


def main():
    data = sys.stdin.read().split()
    idx = 0
    C = int(data[idx]); idx += 1
    T = int(data[idx]); idx += 1  # noqa: F841 (배치 생성에는 불필요)
    M = int(data[idx]); idx += 1  # noqa: F841
    A = [int(data[idx + i]) for i in range(C)]; idx += C
    B = [int(data[idx + i]) for i in range(C)]; idx += C

    R = C

    # F[b] = 경계 b(열 b-1 와 열 b 사이, 1<=b<=C-1)의 순유량 (+: 오른쪽)
    F = [0] * (C + 1)
    s = 0
    for i in range(C - 1):
        s += A[i] - B[i]
        F[i + 1] = s

    # 같은 부호 연속 경계 → run. run마다 행 블록 배정.
    row_of = [-1] * (C + 1)
    next_row = 1
    b = 1
    while b <= C - 1:
        if F[b] == 0:
            b += 1
            continue
        sg = sign(F[b])
        start = b
        while b + 1 <= C - 1 and F[b + 1] != 0 and sign(F[b + 1]) == sg:
            b += 1
        length = b - start + 1
        if sg > 0:
            for k in range(length):
                row_of[start + k] = next_row + k
        else:
            for k in range(length):
                row_of[b - k] = next_row + k
        next_row += length
        b += 1

    grid = [['D' * W_PASS] * C for _ in range(R)]

    for bb in range(1, C):
        r = row_of[bb]
        if r < 0:
            continue
        if F[bb] > 0:
            col = bb - 1
            Q = F[bb]
            N = A[col] + (F[bb - 1] if bb - 1 >= 1 else 0)  # 부호 포함
            lat = 'R'
        else:
            col = bb
            Q = -F[bb]
            N = A[col] + (-F[bb + 1] if bb + 1 <= C - 1 and F[bb + 1] < 0 else 0)
            lat = 'L'
        grid[r - 1][col] = find_pattern(N, Q, lat)

    out = [str(R)]
    for r in range(R):
        out.append(' '.join(grid[r]))
    sys.stdout.write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
