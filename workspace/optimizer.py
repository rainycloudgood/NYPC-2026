# 씨앗 운반 국소탐색 최적화기 (output-only 전용, 오프라인)
#
# usage: python optimizer.py <테스트번호> [초, 기본 120] [시드(선택)]
#
# outputs/output_<i>.txt 를 시드로 읽어 무작위 장치 교체 탐색을 돌리고,
# 개선되면 같은 파일에 다시 쓴다 (원본은 .bak로 1회 백업).
# 수용 규칙: 비용 같거나 낮으면 수용(평지 이동 허용 — 미사용 칸에 장치를
# 미리 놓는 중립 변이가 나중에 연결되며 게이트/분배기가 조립된다).

import math
import os
import random
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V

_HERE = os.path.dirname(os.path.abspath(__file__))
# Downloads의 입력 파일이 사라지는 현상 대비: 로컬 미러(inputs/)를 우선 사용.
IN_DIR = os.path.join(_HERE, 'inputs')
if not os.path.exists(os.path.join(IN_DIR, 'input_15.txt')):
    IN_DIR = r'C:\Users\<user>\Downloads'
OUT_DIR = os.path.join(_HERE, 'outputs')


def read_input(i):
    path = os.path.join(IN_DIR, f'input_{i}.txt')
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'inputs', f'input_{i}.txt')
    data = open(path).read().split()
    it = iter(data)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]
    return C, T, M, A, B


def read_grid(path):
    out = open(path).read().split()
    R = int(out[0])
    return R, out[1:]


def evaluate(C, T, M, A, B, R, body):
    cells = {}
    for r in range(1, R + 1):
        for c in range(C):
            cells[(r, c)] = V.parse_cell(body[(r - 1) * C + c])
    Bp, t_last, bounces, leftover = V.simulate(C, T, M, A, B, R, cells)
    L = sum(B) - sum(Bp)
    E = sum(abs(Bp[i] - B[i]) for i in range(C))
    D = T if L > 0 else t_last - M
    cost = (1 << (R - C)) + max(E, D) + T * L
    return (cost, E, D, bounces)


def rank(sc):
    """Cost 동점에서는 지연 병목을 먼저 제거한다.

    예전 튜플 비교는 E를 D보다 먼저 비교해서, max(E,D)가 D인 판에서도
    E만 줄이며 같은 Cost에 머무는 문제가 있었다.
    """
    cost, E, D, bounces = sc
    return cost, D, E, bounces


def random_token(r, c, C, R, rng):
    x = rng.random()
    if x < 0.5:  # 다람쥐
        ds = ['D']
        if r >= 2:
            ds.append('U')
        if c >= 1:
            ds.append('L')
        if c <= C - 2:
            ds.append('R')
        k = rng.randint(1, len(ds))
        return ''.join(rng.sample(ds, k))
    if x < 0.85:  # 햄스터
        opts = []
        if R + 1 - r >= 2:
            opts += [('D', d) for d in range(2, R + 2 - r)]
        if r - 1 >= 2:
            opts += [('U', d) for d in range(2, r)]
        if c >= 2:
            opts += [('L', d) for d in range(2, c + 1)]
        if C - 1 - c >= 2:
            opts += [('R', d) for d in range(2, C - c)]
        if not opts:
            return 'D'
        if R + 1 - r >= 2 and rng.random() < 0.3:
            return f'{R + 1 - r}D'  # 굴 직투 우대
        ch, d = rng.choice(opts)
        return f'{d}{ch}'
    if x < 0.95:
        return 'D'
    return 'X'


def mutate_one(cand, p, C, R, rng):
    """한 칸 변이. 대체 외에 방향 재배열/거리 조절/맞교환/복사 연산자를 섞어
    무작위 대체만으로는 닿기 힘든 이웃해로 이동한다. 결과는 항상 유효."""
    r, c = p // C + 1, p % C
    tok = cand[p]
    x = rng.random()
    if x < 0.45:
        cand[p] = random_token(r, c, C, R, rng)
        return
    if x < 0.60:
        # 다람쥐 방향 재배열(순서 = 라운드로빈 위상) / 방향 하나 빼기
        if tok != 'X' and not tok[0].isdigit() and len(tok) > 1:
            ds = list(tok)
            rng.shuffle(ds)
            if len(ds) > 1 and rng.random() < 0.3:
                ds.pop()
            cand[p] = ''.join(ds)
            return
        cand[p] = random_token(r, c, C, R, rng)
        return
    if x < 0.72:
        # 햄스터 거리 ±1 (타이밍/착지점 미세조정)
        if tok != 'X' and tok[0].isdigit():
            i = 0
            while tok[i].isdigit():
                i += 1
            nd = int(tok[:i]) + (1 if rng.random() < 0.5 else -1)
            cand2 = f'{nd}{tok[i:]}'
            if nd >= 2 and V.valid_cell(cand2, r, c, R, C)[0]:
                cand[p] = cand2
                return
        cand[p] = random_token(r, c, C, R, rng)
        return
    q = rng.randrange(R * C)
    r2, c2 = q // C + 1, q % C
    if x < 0.88:
        # 두 칸 장치 맞교환
        a, b = cand[p], cand[q]
        if V.valid_cell(b, r, c, R, C)[0] and V.valid_cell(a, r2, c2, R, C)[0]:
            cand[p], cand[q] = b, a
            return
    else:
        # 장치 복사 p -> q
        if V.valid_cell(cand[p], r2, c2, R, C)[0]:
            cand[q] = cand[p]
            return
    cand[p] = random_token(r, c, C, R, rng)


def main():
    idx = int(sys.argv[1])
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    C, T, M, A, B = read_input(idx)

    out_path = os.path.join(OUT_DIR, f'output_{idx}.txt')
    seed_path = sys.argv[3] if len(sys.argv) > 3 else out_path
    R, body = read_grid(seed_path)
    NC = R * C

    # 15번의 실측 반송 hotspot. 대부분의 변이는 이 셀과 바로 주변에서 뽑되,
    # 일부 전역 변이는 유지해 새 경로를 조립할 여지를 남긴다.
    focus = []
    if idx == 15 and R == 8 and C == 8:
        hot = [(1, 2), (1, 4), (1, 6), (1, 7), (2, 3), (2, 4),
               (2, 5), (2, 7), (2, 8), (3, 4), (5, 2), (6, 1),
               (6, 2), (7, 2), (8, 2), (8, 3)]
        focus = [(r - 1) * C + (c - 1) for r, c in hot]

    cur = list(body)
    cur_sc = evaluate(C, T, M, A, B, R, cur)
    best, best_sc = list(cur), cur_sc
    print(f'[테스트 {idx}] 시드 cost={cur_sc[0]} E={cur_sc[1]} D={cur_sc[2]}',
          file=sys.stderr)

    rng = random.Random()
    focus_p = float(os.environ.get('FOCUS_P', '0.85'))
    # 혼잡(반송) 유도 가중치: 동일 cost 이웃 중 반송이 적은 쪽을 선호하게 하는
    # 미세 항. cost 정수값보다 작게 유지해 최적성은 해치지 않는다.
    congest_w = float(os.environ.get('CONGEST_W', '0.0'))
    t0 = time.time()
    it_count = 0
    stall = 0
    last_report = t0
    T_HI, T_LO = 3.0, 0.02  # 담금질 온도 (비용 단위)
    while time.time() - t0 < budget:
        it_count += 1
        frac = min((time.time() - t0) / budget, 1.0)
        temp = T_HI * (T_LO / T_HI) ** frac
        cand = list(cur)
        nmut = 1 if rng.random() < 0.7 else (2 if rng.random() < 0.8 else 3)
        for _ in range(nmut):
            p = rng.choice(focus) if focus and rng.random() < focus_p else rng.randrange(NC)
            mutate_one(cand, p, C, R, rng)
        sc = evaluate(C, T, M, A, B, R, cand)
        # 혼잡 가중 rank: cost 동점 시 반송 적은 쪽으로 강하게 끌기
        cr_sc = rank(sc)[:1] + (congest_w * sc[3],) + rank(sc)[1:]
        cr_cur = rank(cur_sc)[:1] + (congest_w * cur_sc[3],) + rank(cur_sc)[1:]
        if cr_sc <= cr_cur:
            accept = True
        else:
            # 담금질: 악화도 온도에 비례해 확률적으로 수용 (지역최적 탈출)
            d = ((sc[0] - cur_sc[0]) + congest_w * (sc[3] - cur_sc[3])
                 + 0.001 * (sc[2] - cur_sc[2]) + 0.0005 * (sc[1] - cur_sc[1]))
            accept = d < 12 * temp and rng.random() < math.exp(-max(d, 1e-9) / temp)
        if accept:
            if rank(sc) < rank(cur_sc):
                stall = 0
            cur, cur_sc = cand, sc
            if rank(sc) < rank(best_sc):
                best, best_sc = list(cand), sc
                print(f'  개선: cost={sc[0]} E={sc[1]} D={sc[2]} '
                      f'({it_count}회, {time.time() - t0:.0f}s)', file=sys.stderr)
        else:
            stall += 1
            if stall > 8000:  # 장기 정체 → 최고해에 무작위 킥을 준 지점에서 재출발
                cur = list(best)
                for _ in range(rng.randint(2, 6)):
                    p = rng.choice(focus) if focus and rng.random() < focus_p else rng.randrange(NC)
                    mutate_one(cur, p, C, R, rng)
                cur_sc = evaluate(C, T, M, A, B, R, cur)
                stall = 0
        if time.time() - last_report > 15:
            print(f'  ... {it_count}회, 현재 best cost={best_sc[0]}',
                  file=sys.stderr)
            last_report = time.time()

    # 기존 파일보다 좋아졌을 때만 갱신
    old_sc = evaluate(C, T, M, A, B, *read_grid(out_path))
    if rank(best_sc) < rank(old_sc):
        if not os.path.exists(out_path + '.bak'):
            shutil.copy(out_path, out_path + '.bak')
        with open(out_path, 'w') as f:
            f.write(str(R) + '\n')
            for r in range(R):
                f.write(' '.join(best[r * C:(r + 1) * C]) + '\n')
        print(f'[테스트 {idx}] 갱신: cost {old_sc[0]} -> {best_sc[0]} '
              f'({it_count}회 탐색)', file=sys.stderr)
    else:
        print(f'[테스트 {idx}] 개선 없음 (기존 cost={old_sc[0]}, {it_count}회 탐색)',
              file=sys.stderr)


if __name__ == '__main__':
    main()
