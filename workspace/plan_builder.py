# LP 수송 계획(plan_<i>.json)을 따르는 가젯 빌더
#
# gadget_builder와의 차이:
#  * 계단(NW) 대신 스케줄 제약 LP가 만든 다대다 계획을 실현한다.
#  * 고립 탐색을 '전역 기하 + 해당 열 씨앗만 마스킹'으로 수행 — 시뮬 속도는
#    고립 수준(활성 칸이 적음), 기하 왜곡/이식 손실은 0. 남의 칸은 X로 가려
#    기생 라우팅을 차단한다.
#  * 원거리 목표 열에는 가장 깊은 미점유 칸 2개씩을 착지 후보로 개방.
#
# usage: python plan_builder.py <테스트번호> [열당 초, 기본 240]
# 결과: outputs/seed_<i>_plan.txt

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gadget_builder import eval_masked, sa_search
from optimizer import OUT_DIR, evaluate, read_input


def main():
    idx = int(sys.argv[1])
    per_col = float(sys.argv[2]) if len(sys.argv) > 2 else 240.0
    C, T, M, A, B = read_input(idx)
    R = C
    rng = random.Random()

    with open(os.path.join(OUT_DIR, f'plan_{idx}.json')) as f:
        Q = json.load(f)   # Q[i][j] = 열 i -> 굴 j 수량

    body = ['X'] * (R * C)
    owner = {}

    def cum_targets(i):
        A_mask = [A[k] if k <= i else 0 for k in range(C)]
        B_target = [sum(Q[k][j] for k in range(i + 1)) for j in range(C)]
        return A_mask, B_target

    def free_cells(i, targets):
        free = []
        for r0 in range(R):
            p = r0 * C + i
            if p not in owner:
                free.append(p)
        for j in targets:
            if j == i:
                continue
            # 목표 열 전체 개방 (급수 칸 (1,j) 제외).
            # 햄스터 수평 투척은 던진 행에 착지하므로 행을 제한하면
            # 원거리 배송이 기하적으로 불가능해진다. 과점은 사용 칸
            # 페널티가 억제한다.
            for r0 in range(1, R):
                p = r0 * C + j
                if p not in owner:
                    free.append(p)
        return free

    def build_col(i, budget):
        nonlocal body
        targets = [j for j in range(C) if Q[i][j] > 0]
        A_mask, B_target = cum_targets(i)
        had_old = any(o == i for o in owner.values())
        snap_body, snap_owner = list(body), dict(owner)
        snap_sc = eval_masked(C, T, M, A_mask, B_target, R, body)
        for p, o in list(owner.items()):
            if o == i:
                body[p] = 'X'
                del owner[p]
        free = free_cells(i, targets)
        # --- 1단계: 이 열 씨앗만 켜고 탐색 (남의 칸은 X로 가림) ---
        A_solo = [A[i] if k == i else 0 for k in range(C)]
        B_solo = list(Q[i])
        veiled = ['X' if p in owner else body[p] for p in range(R * C)]

        if len(targets) >= 3 and Q[i][i] > 0:
            # 3분할: 2단 직렬 2분할로 분해.
            # 상단(1..h행)은 가장 먼 목표만 떼어내고 나머지는 자기 굴로 벨트,
            # 하단(h+1..R행)은 그 벨트 스트림을 남은 두 목표로 재분할한다.
            far = max((j for j in targets if j != i), key=lambda j: abs(j - i))
            mids = [j for j in targets if j not in (i, far)]
            h = R // 2
            up_cells = [p for p in free
                        if (p % C == i and p // C < h) or p % C == far]
            low_cells = [p for p in free
                         if (p % C == i and p // C >= h)
                         or (p % C != i and p % C != far)]
            # 하단 벨트 초기화 (rest -> 자기 굴)
            base = list(veiled)
            for p in range(R * C):
                if p % C == i and p // C >= h and p in free:
                    base[p] = 'D'
            B_A = [0] * C
            B_A[far] = Q[i][far]
            B_A[i] = A[i] - Q[i][far]
            bestA = bestA_sc = None
            for head in (f'{R}D', 'DR', 'RD', 'D'):
                g = list(base)
                g[i] = head
                sc = eval_masked(C, T, M, A_solo, B_A, R, g)
                if bestA_sc is None or sc < bestA_sc:
                    bestA, bestA_sc = g, sc
            gA, scA = sa_search(C, T, M, A_solo, B_A, R, bestA, up_cells,
                                budget * 0.3, rng)
            if scA < bestA_sc:
                bestA, bestA_sc = gA, scA
            print(f'  (1단 far=굴{far + 1} max(E,D)={bestA_sc[0]:.1f})',
                  file=sys.stderr)
            best1, best1_sc = sa_search(C, T, M, A_solo, B_solo, R, bestA,
                                        low_cells, budget * 0.3, rng)
        else:
            best1 = best1_sc = None
            for head in (f'{R}D', 'DR', 'RD', 'D'):
                g = list(veiled)
                g[i] = head
                sc = eval_masked(C, T, M, A_solo, B_solo, R, g)
                if best1_sc is None or sc < best1_sc:
                    best1, best1_sc = g, sc
            g, sc = sa_search(C, T, M, A_solo, B_solo, R, best1, free,
                              budget * 0.55, rng)
            if sc < best1_sc:
                best1, best1_sc = g, sc
        print(f'  (단독 max(E,D)={best1_sc[0]:.1f})', file=sys.stderr)
        # 가림막을 실제 조립체로 복원한 이식본
        merged = list(body)
        for p in free:
            merged[p] = best1[p]
        # --- 2단계: 누적 환경 보정 ---
        seeds = [merged]
        g0 = list(body)
        g0[i] = f'{R}D'
        seeds.append(g0)
        best = best_sc = None
        for g in seeds:
            sc = eval_masked(C, T, M, A_mask, B_target, R, g)
            if best_sc is None or sc < best_sc:
                best, best_sc = g, sc
        if best_sc[0] > 2:
            g, sc = sa_search(C, T, M, A_mask, B_target, R, best, free,
                              budget * 0.45, rng)
            if sc < best_sc:
                best, best_sc = g, sc
        if had_old and best_sc[0] > snap_sc[0] + 0.6:
            body = snap_body
            owner.clear()
            owner.update(snap_owner)
            print(f'열 {i + 1}: 재탐색 실패 -> 이전 유지 '
                  f'(max(E,D)={snap_sc[0]:.1f})', file=sys.stderr)
            return snap_sc
        print(f'열 {i + 1}: A={A[i]} -> '
              + ', '.join(f'굴{j + 1}:{Q[i][j]}' for j in targets)
              + f'  누적 max(E,D)={best_sc[0]:.1f} E={best_sc[2]} D={best_sc[1]}',
              file=sys.stderr)
        for p in free:
            if best[p] != 'X':
                owner[p] = i
        body = best
        return best_sc

    for i in range(C):
        if A[i] == 0:
            continue
        build_col(i, per_col)

    # 수리 패스 (잔차 재계산, 왼쪽부터, 2라운드)
    def residuals():
        res = {}
        prev = 0.0
        for i in range(C):
            if A[i] == 0:
                continue
            A_mask, B_target = cum_targets(i)
            e = eval_masked(C, T, M, A_mask, B_target, R, body)[0]
            res[i] = e - prev
            prev = e
        return res

    for rnd in range(2):
        res = residuals()
        bad = [i for i in sorted(res) if res[i] > 4]
        if not bad:
            break
        for i in bad:
            print(f'--- 수리 R{rnd + 1}: 열 {i + 1} (잔차 {res[i]:.0f}) ---',
                  file=sys.stderr)
            build_col(i, per_col * 2)

    sc = evaluate(C, T, M, A, B, R, body)
    print(f'[조립 결과] cost={sc[0]} E={sc[1]} D={sc[2]}', file=sys.stderr)

    dst = os.path.join(OUT_DIR, f'seed_{idx}_plan.txt')
    with open(dst, 'w') as f:
        f.write(str(R) + '\n')
        for r in range(R):
            f.write(' '.join(body[r * C:(r + 1) * C]) + '\n')
    print(dst)


if __name__ == '__main__':
    main()
