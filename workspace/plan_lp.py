# 스케줄 제약 수송 계획 LP
#
# 변수: X[i][j] = 열 i 스트림 중 굴 j로 보내는 비율 (0..1)
# 제약:
#   (1) Σ_j X[i][j] = 1                        (스트림 완전 분할)
#   (2) Σ_i X[i][j]·A_i = B_j                  (정확한 총량)
#   (3) Σ_i X[i][j]·min(w, A_i) <= w  ∀w∈{A_i} (굴 도착 스케줄: 어떤 꼬리
#       구간에서도 도착량이 저장 용량(1/턴)을 넘지 않음 — D≈0의 필요조건.
#       모든 창이 M에서 끝나므로 꼬리 구간만 보면 된다)
# 목적: 사용되는 (i,j) 쌍 수를 줄이는 대신 LP라 Σ 장거리 가중치 최소화
#       (|i-j| 가중 → 라우팅 단순화), 그리고 X 희소화를 위해 후처리.
#
# usage: python plan_lp.py <테스트번호> [slack]
import os
import sys

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from optimizer import read_input


def solve_plan(C, A, B, slack=0.0):
    n = C * C  # X[i][j] -> idx i*C+j
    A_eq = []
    b_eq = []
    # (1) 행합 = 1 (A_i > 0인 열만)
    for i in range(C):
        if A[i] == 0:
            continue
        row = np.zeros(n)
        for j in range(C):
            row[i * C + j] = 1.0
        A_eq.append(row)
        b_eq.append(1.0)
    # (2) 굴 총량
    for j in range(C):
        row = np.zeros(n)
        for i in range(C):
            if A[i] > 0:
                row[i * C + j] = A[i]
        A_eq.append(row)
        b_eq.append(float(B[j]))
    # (3) 꼬리 스케줄 제약
    A_ub = []
    b_ub = []
    ws = sorted(set(a for a in A if a > 0))
    for j in range(C):
        for w in ws:
            row = np.zeros(n)
            for i in range(C):
                if A[i] > 0:
                    row[i * C + j] = float(min(w, A[i]))
            A_ub.append(row)
            b_ub.append(float(w) + slack)
    # 목적: 장거리 이동 최소화 (|i-j| 가중)
    cost = np.zeros(n)
    for i in range(C):
        for j in range(C):
            cost[i * C + j] = abs(i - j)
    res = linprog(cost, A_ub=np.array(A_ub), b_ub=np.array(b_ub),
                  A_eq=np.array(A_eq), b_eq=np.array(b_eq),
                  bounds=[(0, 1)] * n, method='highs')
    return res


def solve_sparse(C, A, B, slack=0.0):
    """LP 해에서 작은 유량을 반복 제거해 희소한 계획을 얻는다."""
    banned = set()

    def run():
        res = solve_plan_banned(C, A, B, slack, banned)
        return res

    res = run()
    assert res.success
    # 1) 15개 미만 유량 일괄 제거 시도
    while True:
        X = res.x.reshape(C, C)
        small = [(i, j) for i in range(C) for j in range(C)
                 if (i, j) not in banned and 0.01 < X[i][j] * A[i] < 15]
        if not small:
            break
        trial = solve_plan_banned(C, A, B, slack, banned | set(small))
        if trial.success:
            banned |= set(small)
            res = trial
        else:
            break
    # 2) 남은 유량 중 가장 작은 것부터 하나씩 제거 시도
    improved = True
    while improved:
        improved = False
        X = res.x.reshape(C, C)
        flows = sorted(
            ((X[i][j] * A[i], i, j) for i in range(C) for j in range(C)
             if (i, j) not in banned and X[i][j] * A[i] > 0.01))
        for q, i, j in flows[:4]:
            trial = solve_plan_banned(C, A, B, slack, banned | {(i, j)})
            if trial.success:
                banned.add((i, j))
                res = trial
                improved = True
                break
    return res


def solve_plan_banned(C, A, B, slack, banned):
    import copy
    n = C * C
    bounds = [(0.0, 0.0) if (i, j) in banned else (0.0, 1.0)
              for i in range(C) for j in range(C)]
    # solve_plan을 bounds만 바꿔 재사용하기 위해 로컬 복제
    A_eq, b_eq, A_ub, b_ub, cost = _build(C, A, B, slack)
    return linprog(cost, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                   bounds=bounds, method='highs')


def _build(C, A, B, slack):
    n = C * C
    A_eq, b_eq = [], []
    for i in range(C):
        if A[i] == 0:
            continue
        row = np.zeros(n)
        for j in range(C):
            row[i * C + j] = 1.0
        A_eq.append(row)
        b_eq.append(1.0)
    for j in range(C):
        row = np.zeros(n)
        for i in range(C):
            if A[i] > 0:
                row[i * C + j] = A[i]
        A_eq.append(row)
        b_eq.append(float(B[j]))
    A_ub, b_ub = [], []
    ws = sorted(set(a for a in A if a > 0))
    for j in range(C):
        for w in ws:
            row = np.zeros(n)
            for i in range(C):
                if A[i] > 0:
                    row[i * C + j] = float(min(w, A[i]))
            A_ub.append(row)
            b_ub.append(float(w) + slack)
    cost = np.zeros(n)
    for i in range(C):
        for j in range(C):
            # 실제 운반 작업량(씨앗 수 x 거리) + 분할 자체에 대한 미세 벌점
            cost[i * C + j] = A[i] * (abs(i - j) + (0.05 if i != j else 0.0))
    return (np.array(A_eq), np.array(b_eq), np.array(A_ub), np.array(b_ub),
            cost)


def integerize(C, A, B, X, slack_check=2.0):
    """행합=A_i, 열합=B_j를 정확히 지키는 정수 계획으로 반올림."""
    Q = [[0] * C for _ in range(C)]
    for i in range(C):
        if A[i] == 0:
            continue
        qs = [X[i][j] * A[i] for j in range(C)]
        fl = [int(q) for q in qs]
        rem = A[i] - sum(fl)
        order = sorted(range(C), key=lambda j: -(qs[j] - fl[j]))
        for k in range(rem):
            fl[order[k]] += 1
        for j in range(C):
            Q[i][j] = fl[j]
    # 열합 보정: 초과 굴 -> 부족 굴로 1개씩 이동 (같은 행 안에서)
    for _ in range(10 * C):
        colsum = [sum(Q[i][j] for i in range(C)) for j in range(C)]
        over = [j for j in range(C) if colsum[j] > B[j]]
        under = [j for j in range(C) if colsum[j] < B[j]]
        if not over:
            break
        jo, ju = over[0], under[0]
        moved = False
        # 기존 유량이 있는 행 우선 (새 유량 생성 방지)
        for require_both in (True, False):
            for i in range(C):
                if Q[i][jo] > 0 and (Q[i][ju] > 0 or not require_both):
                    Q[i][jo] -= 1
                    Q[i][ju] += 1
                    moved = True
                    break
            if moved:
                break
        assert moved
    # 검증
    for i in range(C):
        assert sum(Q[i]) == A[i]
    for j in range(C):
        assert sum(Q[i][j] for i in range(C)) == B[j]
    ws = sorted(set(a for a in A if a > 0))
    worst = 0.0
    for j in range(C):
        for w in ws:
            load = sum(Q[i][j] * min(w, A[i]) / max(A[i], 1)
                       for i in range(C) if A[i] > 0) - w
            worst = max(worst, load)
    print(f'정수화 완료. 최악 꼬리 초과 {worst:.1f}')
    return Q


def solve_max2(C, A, B, slack):
    """열당 유량 2개 이하가 될 때까지 최소 유량을 금지하며 재해석."""
    banned = set()
    res = solve_plan_banned(C, A, B, slack, banned)
    if not res.success:
        return res, banned
    for _ in range(4 * C):
        X = res.x.reshape(C, C)
        # 3개 이상 유량을 가진 열 중 최소 유량 후보
        cands = []
        for i in range(C):
            arcs = [(X[i][j] * A[i], j) for j in range(C)
                    if X[i][j] * A[i] > 0.5]
            if len(arcs) > 2:
                q, j = min(arcs)
                cands.append((q, i, j))
        if not cands:
            break
        cands.sort()
        progressed = False
        for q, i, j in cands:
            trial = solve_plan_banned(C, A, B, slack, banned | {(i, j)})
            if trial.success:
                banned.add((i, j))
                res = trial
                progressed = True
                break
        if not progressed:
            # 어떤 금지도 불능 → 3분할 하나는 허용하고 종료
            break
    return res, banned


def main():
    idx = int(sys.argv[1])
    slack = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    C, T, M, A, B = read_input(idx)
    res, _ = solve_max2(C, A, B, slack)
    if not res.success:
        print(f'LP 불능 (slack={slack}): {res.message}')
        print('=> D=0 스케줄이 불가능. slack을 늘려 최소 대기열을 찾아보세요.')
        return
    X = res.x.reshape(C, C)
    print(f'LP 가능 (slack={slack}, 희소화 후)')
    Q = integerize(C, A, B, X)
    nflow = 0
    for i in range(C):
        if A[i] == 0:
            continue
        parts = [f'굴{j + 1}:{Q[i][j]}' for j in range(C) if Q[i][j] > 0]
        nflow += len(parts)
        print(f'  열{i + 1} (A={A[i]}): ' + ', '.join(parts))
    print(f'유량 수: {nflow}')
    import json
    dst = os.path.join(HERE, 'outputs', f'plan_{idx}.json')
    with open(dst, 'w') as f:
        json.dump(Q, f)
    print(dst)


if __name__ == '__main__':
    main()
