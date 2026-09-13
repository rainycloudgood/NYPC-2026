#!/usr/bin/env python3
"""[예시] 하한 계산 + 신뢰도 + 항별 분해  — **방법의 본보기**이지 재사용 코드가 아니다.

이 파일은 리허설 문제(배선 정리) 전용이다. 당일 문제엔 그대로 안 붙는다.
**옮겨갈 것은 코드가 아니라 이 3단 구조다:**

  ① 완화 하한 계산        (제약 일부를 무시하고 푼다. 여기선 겹침 무시 + 용량 배낭)
  ② 하한의 신뢰도 검사     (필요 자원 합 vs 가용 자원. 100% 넘으면 하한이 거짓)
                          ⚠️ 필요조건일 뿐 — 자원이 남아도 기하적으로 불가능할 수 있다
  ③ **항별 분해**          (비용을 구성 항으로 쪼개 어느 항이 지배하는지 본다)
                          ★ 배수는 지표로 쓰지 말 것. 지배 항이 곧 할 일이다

왜 이렇게까지 하나: 리허설에서 "하한 대비 22배 격차"를 쫓아 알고리즘을 구현했는데
그 하한이 **존재할 수 없는 값**이었다(빈칸보다 많은 칸 요구). 얻은 건 5%.
또 다른 입력은 "14.8배 격차"였는데 정체가 **3쌍 미연결**이었다(P가 평균길이의 65배).

검증됨: 배낭 탐욕 = 정확 DP (400회 일치) / 9개 입력 전부 하한 ≤ 실제 해.
"""
import collections
import sys

# 🔥 윈도우 콘솔은 기본 CP949 라 ─ ⚠ ★ 같은 문자에서 UnicodeEncodeError 로 **죽는다**.
#    하한을 다 계산해놓고 출력 한 줄에서 죽는다. (2026-08-15 발견)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load(path):
    L = open(path).read().split("\n")
    H, W, N, P = map(int, L[0].split())
    grid = L[1:1 + H]
    pairs = [tuple(map(int, L[1 + H + i].split())) for i in range(N)]
    return H, W, N, P, grid, pairs


def shortest(H, W, g, s, t):
    """장애물만 피한 최단 경로의 **칸 수**. 도달 불가면 None."""
    if s == t:
        return 1
    seen = {s}
    q = collections.deque([(s, 1)])
    while q:
        (r, c), d = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue
            if g[nr][nc] == '#' or (nr, nc) in seen:
                continue
            if (nr, nc) == t:
                return d + 1
            seen.add((nr, nc))
            q.append(((nr, nc), d + 1))
    return None


def knap_exact(sps, P, cap):
    """max Σ(P−sp) s.t. Σsp ≤ cap  — 정확 DP (탐욕 검증용)."""
    best = [0] * (cap + 1)
    for w in sps:
        v = P - w
        for c in range(cap, w - 1, -1):
            if best[c - w] + v > best[c]:
                best[c] = best[c - w] + v
    return max(best)


def knap_greedy(sps, P, cap):
    """sp 오름차순 탐욕.

    최적성: 목적이 Σ(P−sp_i) 최대화인데, sp 가 작을수록 **무게는 작고 가치는 크다**.
    따라서 ①개수 최대화가 항상 이득이고(각 항이 양수) ②개수 k 를 고정하면
    가장 작은 k 개가 Σsp 를 최소화한다. 두 조건을 오름차순 탐욕이 동시에 만족한다.
    """
    tot = val = 0
    for w in sorted(sps):
        if tot + w <= cap:
            tot += w
            val += P - w
    return val


def analyze(path, ours=None, unrouted=None):
    H, W, N, P, g, pairs = load(path)
    free = sum(row.count('.') for row in g)
    sp = [shortest(H, W, g, (a, b), (c, d)) for a, b, c, d in pairs]
    reach = [x for x in sp if x is not None]
    unreach = N - len(reach)

    # ① 느슨한 하한 — 겹침 제약 무시 (개별 최적의 합)
    loose = sum(x for x in reach if x < P) + P * (N - sum(1 for x in reach if x < P))

    # ② 용량 반영 하한 — Σsp ≤ free 제약 추가
    cand = [x for x in reach if x < P]
    save = knap_greedy(cand, P, free)
    tight = P * N - save

    # ③ 신뢰도: 필요 칸 / 가용 칸
    need = sum(cand)
    util = need / free if free else float("inf")

    print(f"[{path}]  H×W={H}×{W}  N={N}  P={P}  빈칸={free}")
    if unreach:
        print(f"  도달 불가 쌍 {unreach}개 (무조건 P 지불)")
    print(f"  ① 느슨한 하한(겹침 무시)   = {loose}")
    print(f"  ② 용량 반영 하한           = {tight}")
    print(f"  ③ 점유율(필요/가용)        = {util:.0%}"
          + ("   ⚠️ 100% 초과 → ①은 존재할 수 없는 값이었다" if util > 1.0 else ""))

    # ── ★ 배수가 아니라 **항별 분해**로 본다 ──────────────────────────
    # 배수는 P 가 경로 길이보다 크면 몇 쌍만 놓쳐도 폭발한다. 지표로 못 쓴다.
    n_route_lb = sum(1 for x in cand if x in cand)   # 하한이 가정하는 연결 수
    # (탐욕이 실제로 담은 개수를 다시 센다)
    tot, n_route_lb = 0, 0
    for w in sorted(cand):
        if tot + w <= free:
            tot += w; n_route_lb += 1
    lb_cells, lb_pen = tot, P * (N - n_route_lb)

    print(f"\n  ── 하한의 구성 ──")
    print(f"     배선 칸 {lb_cells}  +  미연결 벌점 {lb_pen} ({N-n_route_lb}쌍 × {P})")
    if ours is not None:
        print(f"\n  ── 우리 해의 구성 (cost={ours}) ──")
        # 미연결 수는 **채점기가 알려주는 값을 쓴다**(추정하면 어긋난다).
        # 없으면 역산하되 근사임을 밝힌다.
        if unrouted is None:
            est_un = max(0, (ours - lb_cells) // P); tag = " (추정)"
        else:
            est_un = unrouted; tag = ""
        print(f"     미연결 벌점{tag}: {est_un}쌍 × {P} = {est_un*P}"
              f"  ({est_un*P/max(ours,1):.0%})")
        gap = ours - tight
        print(f"\n  ── 격차 {gap} 의 정체 ──")
        if est_un > (N - n_route_lb):
            miss = est_un - (N - n_route_lb)
            print(f"     ★ 거의 전부 **미연결 {miss}쌍**에서 온다.")
            print(f"        → 할 일은 '경로를 {ours/max(tight,1):.1f}배 줄이기'가 아니라")
            print(f"          '{miss}쌍을 더 연결하기'다. 완전히 다른 문제다.")
        else:
            print(f"     경로 길이 쪽에서 온다 → 배선을 짧게/덜 돌아가게")
    print(f"\n  ⚠️ 배수(ours/하한)는 지표로 쓰지 말 것. P 가 경로 길이보다 크면"
          f" 몇 쌍만 놓쳐도 폭발한다\n     (이 입력: P={P}, 평균 최단길이"
          f"={sum(cand)/max(len(cand),1):.0f} → {P/max(sum(cand)/max(len(cand),1),1):.0f}배)")
    return tight, util


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    analyze(sys.argv[1],
            int(sys.argv[2]) if len(sys.argv) > 2 else None,
            int(sys.argv[3]) if len(sys.argv) > 3 else None)
