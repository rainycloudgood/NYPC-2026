# NYPC 씨앗 운반 챌린지 - 적응형 단일 제출본 (자동 생성)
import random
import itertools
import sys
from itertools import combinations

def solve_whole(C, T, M, A, B):
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



def assign_halves_exact(A, B):
    """Exact labeled pairing DP for small C (the weak C=5/6 bands)."""
    C = len(A)
    pieces = []
    for i, a in enumerate(A):
        pieces.append((a - a // 2, i, 0))
        pieces.append((a // 2, i, 1))
    n = 2 * C
    inf = 10**30
    dp = {0: (0, ())}
    for j in range(C):
        ndp = {}
        for mask, (cost, pairs) in dp.items():
            rem = [p for p in range(n) if not (mask >> p) & 1]
            for x in range(len(rem)):
                for y in range(x + 1, len(rem)):
                    p, q = rem[x], rem[y]
                    nm = mask | (1 << p) | (1 << q)
                    nc = cost + abs(pieces[p][0] + pieces[q][0] - B[j])
                    if nm not in ndp or nc < ndp[nm][0]:
                        ndp[nm] = (nc, pairs + ((p, q),))
        dp = ndp
    _cost, pairs = dp[(1 << n) - 1]
    target = [-1] * n
    for j, pair in enumerate(pairs):
        for p in pair:
            target[p] = j
    return pieces, target


def assign_halves(A, B):
    C = len(A)
    if C <= 6:
        return assign_halves_exact(A, B)
    pieces = []
    for i, a in enumerate(A):
        pieces.append((a - a // 2, i, 0))  # splitter first direction
        pieces.append((a // 2, i, 1))

    # A permutation represents two pieces assigned to each successive burrow.
    # Start greedily, then improve by pairwise swaps.  The extra penalty avoids
    # assigning both halves of source i back to burrow i, which the compact
    # two-row geometric routing cannot realize without a collision.
    remaining = list(range(2 * C))
    perm = []
    order = sorted(range(C), key=lambda j: -B[j])
    slots = [None] * C
    for j in order:
        best = None
        for x in range(len(remaining)):
            for y in range(x + 1, len(remaining)):
                p, q = remaining[x], remaining[y]
                bad = pieces[p][1] == j and pieces[q][1] == j
                key = (bad, abs(pieces[p][0] + pieces[q][0] - B[j]))
                if best is None or key < best[0]:
                    best = (key, x, y, p, q)
        _, x, y, p, q = best
        slots[j] = [p, q]
        remaining.pop(y)
        remaining.pop(x)
    for pair in slots:
        perm.extend(pair)

    def score(v):
        err = 0
        bad = 0
        for j in range(C):
            p, q = v[2 * j], v[2 * j + 1]
            err += abs(pieces[p][0] + pieces[q][0] - B[j])
            if pieces[p][1] == j and pieces[q][1] == j:
                bad += 1
        return bad * 10**9 + err

    rng = random.Random(0x5EED + C + max(A))
    cur = score(perm)
    for _ in range(30000):
        x, y = rng.sample(range(2 * C), 2)
        perm[x], perm[y] = perm[y], perm[x]
        ns = score(perm)
        if ns <= cur:
            cur = ns
        else:
            perm[x], perm[y] = perm[y], perm[x]

    # Re-optimize three burrows at a time.  For their six pieces this checks
    # every pairing exactly, so it can escape the single-swap local minima
    # above without relying on luck.
    def pair_cost(j, p, q):
        bad = pieces[p][1] == j and pieces[q][1] == j
        return (10**9 if bad else 0) + abs(pieces[p][0] + pieces[q][0] - B[j])

    for _ in range(8):
        changed = False
        for a, b, c in combinations(range(C), 3):
            ids = [perm[2 * j + z] for j in (a, b, c) for z in (0, 1)]
            old = sum(pair_cost(j, perm[2 * j], perm[2 * j + 1]) for j in (a, b, c))
            best = old
            best_pairs = None
            for ia, xa in combinations(range(6), 2):
                pa, qa = ids[ia], ids[xa]
                rem1 = [k for k in range(6) if k not in (ia, xa)]
                for u in range(4):
                    for v in range(u + 1, 4):
                        ib, xb = rem1[u], rem1[v]
                        rem2 = [k for k in rem1 if k not in (ib, xb)]
                        pb, qb = ids[ib], ids[xb]
                        pc, qc = ids[rem2[0]], ids[rem2[1]]
                        val = pair_cost(a, pa, qa) + pair_cost(b, pb, qb) + pair_cost(c, pc, qc)
                        if val < best:
                            best = val
                            best_pairs = ((pa, qa), (pb, qb), (pc, qc))
            if best_pairs is not None:
                for j, pair in zip((a, b, c), best_pairs):
                    perm[2 * j], perm[2 * j + 1] = pair
                changed = True
        if not changed:
            break

    # One wider neighborhood: repartition eight pieces among four burrows.
    # There are only 8! / 2^4 = 2520 ordered pairings per quartet.
    for _ in range(1):
        changed = False
        for js in combinations(range(C), 4):
            ids = tuple(perm[2 * j + z] for j in js for z in (0, 1))
            old = sum(pair_cost(j, perm[2 * j], perm[2 * j + 1]) for j in js)
            best = old
            best_pairs = None

            def search(k, rem, val, made):
                nonlocal best, best_pairs
                if val >= best:
                    return
                if k == 4:
                    best = val
                    best_pairs = tuple(made)
                    return
                j = js[k]
                for x in range(len(rem)):
                    for y in range(x + 1, len(rem)):
                        p, q = rem[x], rem[y]
                        nxt = rem[:x] + rem[x + 1:y] + rem[y + 1:]
                        search(k + 1, nxt, val + pair_cost(j, p, q), made + [(p, q)])

            search(0, ids, 0, [])
            if best_pairs is not None:
                for j, pair in zip(js, best_pairs):
                    perm[2 * j], perm[2 * j + 1] = pair
                changed = True
        if not changed:
            break

    target = [-1] * (2 * C)
    for j in range(C):
        target[perm[2 * j]] = j
        target[perm[2 * j + 1]] = j
    return pieces, target


def put_route(grid, r, c, j, R):
    """Route a rate<=1 stream at (r,c) horizontally, then to burrow j."""
    if c == j:
        d = R + 1 - r
        grid[r - 1][c] = 'D' if d == 1 else f'{d}D'
        return
    d = j - c
    grid[r - 1][c] = (str(abs(d)) if abs(d) >= 2 else '') + ('R' if d > 0 else 'L')
    down = R + 1 - r
    grid[r - 1][j] = 'D' if down == 1 else f'{down}D'


def solve_split(C, T, M, A, B):
    pieces, target = assign_halves(A, B)
    R = 2 * C + 1
    grid = [['X'] * C for _ in range(R)]

    by_source = [[None, None] for _ in range(C)]
    for p, (_, src, half) in enumerate(pieces):
        by_source[src][half] = target[p]

    for i, a in enumerate(A):
        if a == 0:
            continue
        s = 2 * i + 2  # splitter row; row s+1 belongs to its downward child
        side = 1 if i + 1 < C else -1
        sc = i + side
        ceil_target, floor_target = by_source[i]

        # If both halves chose the same burrow, coalesce them back into the
        # original rate-1 stream.  This removes an unnecessary old geometry
        # restriction and lets the exact pairing DP reach its true optimum.
        if ceil_target == floor_target:
            entry = s - 1
            grid[0][i] = 'D' if entry == 1 else f'{entry}D'
            put_route(grid, s, i, ceil_target, R)
            continue

        # The lateral branch may not target column i because the splitter itself
        # occupies that cell.  Put an own-column half on the downward branch.
        lateral_half = 0
        if ceil_target == i:
            lateral_half = 1
        lateral_target = by_source[i][lateral_half]
        down_target = by_source[i][1 - lateral_half]
        if lateral_target == i:
            # Assignment scoring makes this unreachable unless both halves target i.
            lateral_target, down_target = down_target, lateral_target
            lateral_half = 1 - lateral_half

        # Flower entry -> splitter.  All splitters are below row 1.
        entry = s - 1
        grid[0][i] = 'D' if entry == 1 else f'{entry}D'
        side_dir = 'R' if side > 0 else 'L'
        # First listed direction receives ceil(A/2).
        if lateral_half == 0:
            grid[s - 1][i] = side_dir + 'D'
        else:
            grid[s - 1][i] = 'D' + side_dir

        put_route(grid, s, sc, lateral_target, R)
        put_route(grid, s + 1, i, down_target, R)

    return R, grid




def whole_error(A, B):
    C = len(A)
    dp = [10**30] * (1 << C)
    dp[0] = 0
    for mask in range(1 << C):
        i = mask.bit_count()
        if i == C:
            continue
        for j in range(C):
            if not (mask >> j) & 1:
                nm = mask | (1 << j)
                dp[nm] = min(dp[nm], dp[mask] + abs(A[i] - B[j]))
    return dp[-1]


def split_error(A, B):
    pieces, target = assign_halves(A, B)
    got = [0] * len(B)
    for p, (amount, _src, _half) in enumerate(pieces):
        got[target[p]] += amount
    return sum(abs(got[j] - B[j]) for j in range(len(B)))



def split(a,k,src):
 q,r=divmod(a,k); return [(q+(i<r),src,i) for i in range(k)]

def assign_mixed(A,B,restarts=100,steps=300000):
 C=len(A); halves=split(A[0],2,0)+split(A[-1],2,C-1)
 thirds=[p for i in range(1,C-1) for p in split(A[i],3,i)]
 best=None; rng=random.Random(0xA661+C+max(A))
 for half_targets in itertools.combinations(range(C),2):
  rest=[j for j in range(C) if j not in half_targets]
  for perm4 in itertools.permutations(range(4)):
   hs=[sum(halves[perm4[2*z+t]][0] for t in range(2)) for z in range(2)]
   hcost=sum(abs(hs[z]-B[half_targets[z]]) for z in range(2))
   for _ in range(max(1,restarts//10)):
    perm=list(range(len(thirds))); rng.shuffle(perm)
    sums=[sum(thirds[perm[3*z+t]][0] for t in range(3)) for z in range(C-2)]
    cur=hcost+sum(abs(sums[z]-B[rest[z]]) for z in range(C-2))
    for _ in range(steps//restarts):
     x,y=rng.sample(range(len(thirds)),2); bx,by=x//3,y//3
     if bx==by: continue
     px,py=thirds[perm[x]][0],thirds[perm[y]][0]
     old=abs(sums[bx]-B[rest[bx]])+abs(sums[by]-B[rest[by]])
     nx,ny=sums[bx]-px+py,sums[by]-py+px
     new=abs(nx-B[rest[bx]])+abs(ny-B[rest[by]])
     if new<=old:
      perm[x],perm[y]=perm[y],perm[x];sums[bx],sums[by]=nx,ny;cur+=new-old
    if best is None or cur<best[0]: best=(cur,half_targets,perm4,tuple(rest),tuple(perm),tuple(hs),tuple(sums),halves,thirds)
 return best


def tok(d,ch): return ch if d==1 else f'{d}{ch}'

def route(g,r,c,j,R):
 if g[r-1][c]!='X': return False
 if c==j:
  g[r-1][c]=tok(R+1-r,'D'); return True
 if g[r-1][j]!='X': return False
 g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L')
 g[r-1][j]=tok(R+1-r,'D'); return True

def solve_mixed(C,T,M,A,B):
 x=assign_mixed(A,B,4,15000); _,ht,p4,rest,perm,_,_,halves,thirds=x
 targets=[[] for _ in range(C)]
 for z in range(2):
  for t in range(2): targets[halves[p4[2*z+t]][1]].append(ht[z])
 for pos,p in enumerate(perm): targets[thirds[p][1]].append(rest[pos//3])
 R=2*C+1; g=[['X']*C for _ in range(R)]
 for i in range(C):
  r=2*i+2
  if len(set(targets[i]))==1:
   g[0][i]=tok(r-1,'D');
   if not route(g,r,i,targets[i][0],R): return None
   continue
  if i in (0,C-1): return None
  ok=False
  for ds in itertools.permutations(('L','D','R')):
   snap=[row[:] for row in g]; g[0][i]=tok(r-1,'D'); g[r-1][i]=''.join(ds)
   good=True
   for d,j in zip(ds,targets[i]):
    rr,cc=(r,i-1) if d=='L' else ((r,i+1) if d=='R' else (r+1,i))
    if not route(g,rr,cc,j,R): good=False; break
   if good: ok=True; break
   g=snap
  if not ok:return None
 return R,g,x[0]



def main():
    d=list(map(int,sys.stdin.read().split()))
    C,T,M=d[:3]; A=d[3:3+C]; B=d[3+C:3+2*C]
    ew=whole_error(A,B); whole_est=2+max(ew,2)
    es=split_error(A,B); split_est=(1<<(C+1))+max(es,4)
    if split_est<whole_est:
        safe_R,safe_g=solve_split(C,T,M,A,B); safe_est=split_est
    else:
        safe_R,safe_g=solve_whole(C,T,M,A,B); safe_est=whole_est
    aggressive=solve_mixed(C,T,M,A,B) if C<=8 else None
    if aggressive is not None:
        ar,ag,ae=aggressive
        # A small margin covers ceil ordering/bounce perturbations observed in simulation.
        if (1<<(ar-C))+ae+100 < safe_est:
            R,g=ar,ag
        else: R,g=safe_R,safe_g
    else: R,g=safe_R,safe_g
    print(R)
    for row in g: print(*row)

if __name__=='__main__': main()
