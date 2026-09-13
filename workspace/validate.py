# 씨앗 운반 검증기 v2 — 공식 sample_code.py의 simulate()와 동일 의미론
#
# 공식 의미론 (checker.cpp의 엄격 해석과 다른 점):
#  * 그 초에 수확된 씨앗은 같은 초의 '씨앗 보내기'에서 바로 보낼 수 있다.
#  * 굴도 과부하된다: 저장(초당 1개) 후 씨앗이 남아 있으면
#    그 턴에 받은 씨앗을 전부 보낸 칸으로 돌려보낸다.
#  * 과부하 판단은 '보내기가 끝난 뒤 씨앗이 남아 있는가'로 한다.
#
# usage: python validate.py <input_file> <output_file>

import sys

DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


def parse_cell(tok):
    if tok == 'X':
        return ('S', '')
    if tok[0].isdigit():
        i = 0
        while i < len(tok) and tok[i].isdigit():
            i += 1
        return ('H', int(tok[:i]), tok[i:])
    return ('S', tok)


def valid_cell(tok, r, c, R, C):
    """r: 1..R, c: 0..C-1. 반환: (ok, 이유)"""
    def inside(tr, tc):
        return 1 <= tr <= R + 1 and 0 <= tc < C
    if tok == 'X':
        return True, ''
    if tok[0].isdigit():
        i = 0
        while i < len(tok) and tok[i].isdigit():
            i += 1
        if i == len(tok) or len(tok) - i != 1 or tok[i] not in DIRS:
            return False, '햄스터 토큰 형식 오류'
        dist = int(tok[:i])
        if dist <= 1:
            return False, f'햄스터 거리 {dist} (인접하지 않은 칸만 가능, 2 이상)'
        dr, dc = DIRS[tok[i]]
        tr, tc = r + dr * dist, c + dc * dist
        if tr == 0:
            return False, '햄스터가 꽃으로 던짐'
        if not inside(tr, tc):
            return False, f'햄스터 목표 ({tr},{tc + 1}) 격자 밖'
        return True, ''
    seen = set()
    for ch in tok:
        if ch not in DIRS:
            return False, f'잘못된 방향 문자 {ch!r}'
        if ch in seen:
            return False, f'다람쥐 방향 {ch} 중복 (같은 방향은 1번만)'
        seen.add(ch)
        dr, dc = DIRS[ch]
        tr, tc = r + dr, c + dc
        if tr == 0:
            return False, '다람쥐가 꽃으로 보냄'
        if not inside(tr, tc):
            return False, f'다람쥐 목표 ({tr},{tc + 1}) 격자 밖'
    return True, ''


def simulate(C, T, M, A, B, R, cells):
    """공식 simulate() 포트. cells[(r,c)] = ('S', dirs) | ('H', dist, dir).
    활성 칸만 순회하도록 최적화 (결과는 공식과 동일)."""
    NC = R * C  # 칸 id: (r-1)*C + c, 굴 id: NC + c

    caps = [0] * NC
    targ = [()] * NC
    for r in range(1, R + 1):
        for c in range(C):
            cell = cells[(r, c)]
            i = (r - 1) * C + c
            if cell[0] == 'H':
                _, dist, hd = cell
                dr, dc = DIRS[hd]
                tr, tc = r + dr * dist, c + dc * dist
                targ[i] = ((NC + tc) if tr == R + 1 else (tr - 1) * C + tc,)
                caps[i] = 1
            else:
                lst = []
                for ch in cell[1]:
                    dr, dc = DIRS[ch]
                    tr, tc = r + dr, c + dc
                    lst.append((NC + tc) if tr == R + 1 else (tr - 1) * C + tc)
                targ[i] = tuple(lst)
                caps[i] = len(lst)

    ptr = [0] * NC
    cnt = [0] * (NC + C)          # 칸 + 굴 대기열
    nz = set()                    # cnt>0 인 '칸' (굴 제외)
    Bp = [0] * C
    t_last = 0
    bounces = 0
    tot_a = sum(A)
    dropped = 0
    drop_from = [M - A[i] + 1 for i in range(C)]
    drop_cols = [i for i in range(C) if A[i] > 0]

    for t in range(1, T + 1):
        if dropped >= tot_a and not nz and all(cnt[NC + c] == 0 for c in range(C)):
            break
        # 1. 씨앗 수확 (이번 초에 바로 보낼 수 있음)
        for i in drop_cols:
            if drop_from[i] <= t <= M:
                if cnt[i] == 0:
                    nz.add(i)
                cnt[i] += 1
                dropped += 1
        # 2. 씨앗 보내기 (받은 씨앗은 recv에 모아 동시성 유지)
        recv = {}
        for i in list(nz):
            s = cnt[i]
            cap = caps[i]
            if cap == 0:
                continue
            amt = s if s < cap else cap
            tg = targ[i]
            k = len(tg)
            if amt == 1:
                tgt = tg[ptr[i] % k] if k > 1 else tg[0]
                recv.setdefault(tgt, []).append(i)
                if k > 1:
                    ptr[i] = (ptr[i] + 1) % k
            else:
                p = ptr[i]
                for j in range(amt):
                    recv.setdefault(tg[(p + j) % k], []).append(i)
                ptr[i] = (p + amt) % k
            cnt[i] = s - amt
            if s == amt:
                nz.discard(i)
        # 3. 씨앗 받기 (보내기 후 씨앗이 남은 칸 = 과부하 → 반송. 굴 포함)
        # 과부하 판정은 반송으로 씨앗이 되돌아오기 '전' 상태로 스냅샷해야 한다.
        over = [tgt for tgt in recv if cnt[tgt] > 0]
        over = set(over)
        for tgt, senders in recv.items():
            if tgt in over:  # 과부하 (굴은 대기열 잔량, 칸은 미발송 잔량)
                bounces += len(senders)
                for snd in senders:
                    if cnt[snd] == 0:
                        nz.add(snd)
                    cnt[snd] += 1
            else:
                cnt[tgt] += len(senders)
                if tgt < NC and senders:
                    nz.add(tgt)
        # 4. 씨앗 저장
        for c in range(C):
            i = NC + c
            if cnt[i] > 0:
                cnt[i] -= 1
                Bp[c] += 1
                t_last = t

    leftover = sum(cnt)
    return Bp, t_last, bounces, leftover


def main():
    inp = open(sys.argv[1]).read().split()
    out = open(sys.argv[2]).read().split()

    it = iter(inp)
    C, T, M = int(next(it)), int(next(it)), int(next(it))
    A = [int(next(it)) for _ in range(C)]
    B = [int(next(it)) for _ in range(C)]

    R = int(out[0])
    print(f'C={C} T={T} M={M}')
    print(f'A={A}')
    print(f'B={B}')
    if not (C <= R <= C + 20):
        print(f'[오답] R={R} 범위 위반 (C <= R <= C+20)')
        return
    body = out[1:]
    if len(body) != R * C:
        print(f'[오답] 토큰 개수 {len(body)} != R*C = {R * C}')
        return

    cells = {}
    bad = False
    for r in range(1, R + 1):
        for c in range(C):
            tok = body[(r - 1) * C + c]
            ok, why = valid_cell(tok, r, c, R, C)
            if not ok:
                print(f'[오답] ({r},{c + 1}) 토큰 {tok!r}: {why}')
                bad = True
            cells[(r, c)] = parse_cell(tok)
    if bad:
        return
    print('토큰 전부 유효 — 시뮬레이션 시작 (공식 의미론)')

    Bp, t_last, bounces, leftover = simulate(C, T, M, A, B, R, cells)

    L = sum(B) - sum(Bp)
    E = sum(abs(Bp[i] - B[i]) for i in range(C))
    D = T if L > 0 else t_last - M
    cost = (1 << (R - C)) + max(E, D) + T * L
    print(f"B' = {Bp}")
    print(f'L={L} E={E} t_last={t_last} D={D} 반송횟수={bounces} 미도착잔여={leftover}')
    print(f'Cost = 2^(R-C) + max(E,D) + T*L = {cost}')


if __name__ == '__main__':
    main()
