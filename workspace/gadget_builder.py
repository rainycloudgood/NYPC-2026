# 열별 분할 가젯 '누적' 탐색 + 조립 (근본 구조 변경판 v2)
#
# 아이디어: A→B 수송 계획을 NW-corner로 풀면 (경계 유량이 전부 같은 방향일 때)
# 각 열 i는 "자기 굴에 u_i, 오른쪽 굴에 v_i"만 보내면 된다.
#
# v1의 교훈: 가젯을 고립 샌드박스에서 찾으면 개별로는 완벽해도 조립 시
# 씨앗 흐름끼리 충돌해 깨진다. → v2는 열 i를 탐색할 때 "지금까지 조립된
# 전부 + 열 i의 꽃"을 켠 전체 격자에서 평가한다(누적 접두사 인스턴스).
# 변이는 열 i, i+1의 미점유 칸에만 허용. 그러면 조립 오차가 0이 된다.
#
# usage: python gadget_builder.py <테스트번호> [열당 초, 기본 180]
# 결과: outputs/seed_<i>_gadget.txt (+ 전역 비용 출력)

import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate as V
from optimizer import OUT_DIR, evaluate, random_token, read_input


def nw_flows(C, A, B):
    """NW-corner 수송계획. 반환: flows[i] = [(굴 j, 수량), ...]"""
    flows = [[] for _ in range(C)]
    i = j = 0
    a = A[0]
    b = B[0]
    while True:
        q = min(a, b)
        if q > 0:
            flows[i].append((j, q))
        a -= q
        b -= q
        if a == 0:
            i += 1
            if i == C:
                break
            a = A[i]
        if b == 0:
            j += 1
            if j == C:
                break
            b = B[j]
    return flows


def eval_masked(C, T, M, A_mask, B_target, R, body):
    """전체 폭 격자에서 A 일부만 켠 채 평가. 행 페널티 제외."""
    cells = {}
    for r in range(1, R + 1):
        for c in range(C):
            cells[(r, c)] = V.parse_cell(body[(r - 1) * C + c])
    Bp, t_last, bounces, leftover = V.simulate(C, T, M, A_mask, B_target, R, cells)
    L = sum(B_target) - sum(Bp)
    E = sum(abs(Bp[k] - B_target[k]) for k in range(C))
    D = T if L > 0 else t_last - M
    return (max(E, D) + T * abs(L), D, E, bounces)


def mutate_free(cand, free, C, R, rng):
    """지정된 칸 목록 안에서 한 칸 변이."""
    p = rng.choice(free)
    r, c = p // C + 1, p % C
    tok = cand[p]
    x = rng.random()
    if x < 0.55:
        cand[p] = random_token(r, c, C, R, rng)
        return
    if x < 0.68 and tok != 'X' and not tok[0].isdigit() and len(tok) > 1:
        ds = list(tok)
        rng.shuffle(ds)
        if len(ds) > 1 and rng.random() < 0.3:
            ds.pop()
        cand[p] = ''.join(ds)
        return
    if x < 0.80 and tok != 'X' and tok[0].isdigit():
        i = 0
        while tok[i].isdigit():
            i += 1
        nd = int(tok[:i]) + (1 if rng.random() < 0.5 else -1)
        c2 = f'{nd}{tok[i:]}'
        if nd >= 2 and V.valid_cell(c2, r, c, R, C)[0]:
            cand[p] = c2
            return
        cand[p] = random_token(r, c, C, R, rng)
        return
    q = rng.choice(free)
    r2, c2 = q // C + 1, q % C
    a, b = cand[p], cand[q]
    if x < 0.92:
        if V.valid_cell(b, r, c, R, C)[0] and V.valid_cell(a, r2, c2, R, C)[0]:
            cand[p], cand[q] = b, a
            return
    if V.valid_cell(a, r2, c2, R, C)[0]:
        cand[q] = a
        return
    cand[p] = random_token(r, c, C, R, rng)


def sa_search(C, T, M, A_mask, B_target, R, body0, free, budget, rng):
    def score(body):
        sc = eval_masked(C, T, M, A_mask, B_target, R, body)
        used = sum(1 for p in free if body[p] != 'X')
        # 칸 과점 방지용 미세 페널티 (정수 비용엔 못 미치는 타이브레이크)
        return (sc[0] + 0.02 * used, sc[1], sc[2], sc[3])

    cur = list(body0)
    cur_sc = score(cur)
    best, best_sc = list(cur), cur_sc
    t0 = time.time()
    T_HI, T_LO = 2.0, 0.02
    stall = 0
    while time.time() - t0 < budget and best_sc[0] > 1.9:
        frac = min((time.time() - t0) / budget, 1.0)
        temp = T_HI * (T_LO / T_HI) ** frac
        cand = list(cur)
        for _ in range(1 if rng.random() < 0.7 else 2):
            mutate_free(cand, free, C, R, rng)
        sc = score(cand)
        if sc <= cur_sc:
            accept = True
        else:
            d = (sc[0] - cur_sc[0]) + 0.001 * (sc[1] - cur_sc[1])
            accept = d < 12 * temp and rng.random() < math.exp(-max(d, 1e-9) / temp)
        if accept:
            cur, cur_sc = cand, sc
            if sc < best_sc:
                best, best_sc = list(cand), sc
                stall = 0
        else:
            stall += 1
            if stall > 6000:
                cur, cur_sc = list(best), best_sc
                for _ in range(rng.randint(2, 5)):
                    mutate_free(cur, free, C, R, rng)
                cur_sc = score(cur)
                stall = 0
    return best, best_sc


def main():
    idx = int(sys.argv[1])
    per_col = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    C, T, M, A, B = read_input(idx)
    R = C
    rng = random.Random()

    flows = nw_flows(C, A, B)
    for i, fl in enumerate(flows):
        dests = [j for j, _ in fl]
        assert all(j in (i, i + 1) for j in dests), \
            f'열 {i + 1}의 수송 {fl}가 계단 구조가 아님 — 이 빌더 적용 불가'

    body = ['X'] * (R * C)   # 누적 조립체
    owner = {}               # 전역 칸 p -> 점유한 열 i

    def col_uv(i):
        u = sum(q for j, q in flows[i] if j == i)
        v = sum(q for j, q in flows[i] if j == i + 1)
        return u, v

    def prefix_targets(i, v):
        A_mask = [A[k] if k <= i else 0 for k in range(C)]
        B_target = [0] * C
        for k in range(i + 1):
            B_target[k] = B[k]
        if v > 0:
            B_target[i + 1] = v
        return A_mask, B_target

    def isolated_gadget(i, u, v, budget):
        """C=2 고립 샌드박스에서 가젯 탐색 (시뮬이 작아 탐색량이 크다)."""
        NC2 = R * 2
        # 남의 배관(동결 칸)은 'X'로 모델링 — 실제로는 남의 유량이 흐르는
        # 칸이라, 고립 탐색이 그걸 깨끗한 중계기로 착각해 기생 라우팅하는
        # 것을 막는다 (X에 들어간 씨앗은 좌초 → SA가 강하게 회피).
        frozen = {}
        for r0 in range(R):
            for c0 in range(2):
                gp = r0 * C + i + c0
                if gp in owner:
                    frozen[r0 * 2 + c0] = 'X'
        # 로컬 p=1 = (1, i+1) 급수 칸 보호
        free2 = [p for p in range(NC2) if p not in frozen and p != 1]
        A2, B2 = [A[i], 0], [u, v]
        base = ['X'] * NC2
        for p, tok in frozen.items():
            base[p] = tok
        best = best_sc = None
        for head in (f'{R}D', 'DR', 'RD'):
            g = list(base)
            if 0 not in frozen:
                g[0] = head
            sc = eval_masked(2, T, M, A2, B2, R, g)
            if best_sc is None or sc < best_sc:
                best, best_sc = g, sc
        g, sc = sa_search(2, T, M, A2, B2, R, best, free2, budget, rng)
        if sc < best_sc:
            best, best_sc = g, sc
        return best, best_sc

    def build_col(i, budget, wide=False):
        """열 i의 가젯을 (재)탐색해 조립체에 반영. 반환: 누적 점수."""
        nonlocal body
        u, v = col_uv(i)
        A_mask, B_target = prefix_targets(i, v)
        # 회귀 방지용 스냅샷 (수리 실패 시 복원)
        had_old = any(o == i for o in owner.values())
        snap_body = list(body)
        snap_owner = dict(owner)
        snap_sc = eval_masked(C, T, M, A_mask, B_target, R, body)
        # 기존 소유 칸 철거
        for p, o in list(owner.items()):
            if o == i:
                body[p] = 'X'
                del owner[p]
        if v == 0:
            if i not in owner:
                body[i] = f'{R}D'   # (1, i) 직투
                owner[i] = i
            sc = eval_masked(C, T, M, A_mask, B_target, R, body)
            print(f'열 {i + 1}: 직투 (u={u})  누적 max(E,D)={sc[0]}',
                  file=sys.stderr)
            return sc
        cols = [i, i + 1] + ([i - 1] if wide and i >= 1 else [])
        free = [r0 * C + c for r0 in range(R) for c in cols
                if (r0 * C + c) not in owner]
        # 다음 열의 급수 칸 (1, i+1)은 절대 점유 금지 — 그 열 꽃의 입구다
        if i + 1 in free and i + 1 <= C - 1:
            free.remove(i + 1)
        # 1단계: 고립 샌드박스에서 가젯 발굴 → 조립체에 이식
        g2, sc2 = isolated_gadget(i, u, v, budget * 0.4)
        transplant = list(body)
        for r0 in range(R):
            for c0 in range(2):
                gp = r0 * C + i + c0
                if gp in owner or gp == i + 1:
                    continue
                transplant[gp] = g2[r0 * 2 + c0]
        print(f'  (고립 가젯 max(E,D)={sc2[0]:.1f})', file=sys.stderr)
        # 2단계: 누적 환경에서 이식본/헤드 시드 중 최선을 SA 보정
        seeds = [transplant]
        for head in (f'{R}D', 'DR'):
            g = list(body)
            g[i] = head
            seeds.append(g)
        best = best_sc = None
        for g in seeds:
            sc = eval_masked(C, T, M, A_mask, B_target, R, g)
            if best_sc is None or sc < best_sc:
                best, best_sc = g, sc
        attempts = 0
        while attempts < 2 and best_sc[0] > 6:
            g, sc = sa_search(C, T, M, A_mask, B_target, R, best, free,
                              budget * (0.6 if attempts == 0 else 1.2), rng)
            if sc < best_sc:
                best, best_sc = g, sc
            attempts += 1
        # 수리가 오히려 악화시켰으면 이전 가젯 복원
        if had_old and best_sc[0] > snap_sc[0] + 0.6:
            body = snap_body
            owner.clear()
            owner.update(snap_owner)
            print(f'열 {i + 1}: 수리 실패 -> 이전 가젯 유지 '
                  f'(max(E,D)={snap_sc[0]:.1f})', file=sys.stderr)
            return snap_sc
        print(f'열 {i + 1}: A={A[i]} -> ({u}, {v})  '
              f'누적 max(E,D)={best_sc[0]:.1f} E={best_sc[2]} D={best_sc[1]}'
              f'{" [wide]" if wide else ""}', file=sys.stderr)
        for p in free:
            if best[p] != 'X':
                owner[p] = i
        body = best
        return best_sc

    def residuals():
        """열별 누적 에너지 증가분 (현재 조립체 기준으로 재계산)."""
        res = {}
        prev = 0.0
        for i in range(C):
            if A[i] == 0:
                continue
            u, v = col_uv(i)
            A_mask, B_target = prefix_targets(i, v)
            e = eval_masked(C, T, M, A_mask, B_target, R, body)[0]
            res[i] = e - prev
            prev = e
        return res

    for i in range(C):
        if A[i] == 0:
            continue
        build_col(i, per_col)

    # 수리 패스: 잔차 큰 열을 왼쪽부터 재탐색, 최대 2라운드
    for rnd in range(2):
        res = residuals()
        bad = [i for i in sorted(res) if res[i] > 4]
        if not bad:
            break
        for i in bad:
            print(f'--- 수리 R{rnd + 1}: 열 {i + 1} (잔차 {res[i]:.0f}) ---',
                  file=sys.stderr)
            build_col(i, per_col * 2, wide=(rnd > 0))

    sc = evaluate(C, T, M, A, B, R, body)
    print(f'[조립 결과] cost={sc[0]} E={sc[1]} D={sc[2]}', file=sys.stderr)

    dst = os.path.join(OUT_DIR, f'seed_{idx}_gadget.txt')
    with open(dst, 'w') as f:
        f.write(str(R) + '\n')
        for r in range(R):
            f.write(' '.join(body[r * C:(r + 1) * C]) + '\n')
    print(dst)


if __name__ == '__main__':
    main()
