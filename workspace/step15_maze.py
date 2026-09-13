# Circulant E=0 with BFS maze-routing of each leaf-stream to its hole.
import sys, os, random, itertools
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step15_fresh import evaluate, emit, C, T, M, A, B

val = [A[i] // 3 for i in range(C)]
targets = {i: [(i - 1) % C, i, (i + 1) % C] for i in range(C)}
DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


class Grid:
    def __init__(self, R):
        self.R = R
        self.occ = {}
    def free(self, r, c):
        return 1 <= r <= self.R and 0 <= c < C and (r, c) not in self.occ
    def is_hole(self, r, c):
        return r == self.R + 1 and 0 <= c < C

    def token_to(self, r, c, tr, tc):
        """token at (r,c) that sends to (tr,tc). adjacent->squirrel(1 dir), else hamster."""
        dr, dc = tr - r, tc - c
        if abs(dr) + abs(dc) == 1:
            for k, (a, b) in DIRS.items():
                if (a, b) == (dr, dc): return k
        # straight line dist>=2
        if dr != 0 and dc == 0:
            return f'{abs(dr)}{"D" if dr>0 else "U"}'
        if dc != 0 and dr == 0:
            return f'{abs(dc)}{"R" if dc>0 else "L"}'
        return None  # not a single move

    def neighbors(self, r, c, goalcol):
        """cells reachable by one device from (r,c): adjacent + straight-line dist>=2."""
        out = []
        # adjacent squirrels (not to flower row0)
        for dr, dc in DIRS.values():
            tr, tc = r + dr, c + dc
            if tr == 0: continue
            if self.is_hole(tr, tc) or self.free(tr, tc):
                out.append((tr, tc))
        # hamster straight lines dist>=2 (SKIPS intermediate cells, no interference)
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            for d in range(2, self.R + 2):
                tr, tc = r + dr * d, c + dc * d
                if not (1 <= tr <= self.R + 1 and 0 <= tc < C): break
                if tr == 0: break
                if self.is_hole(tr, tc):
                    out.append((tr, tc)); break   # can't go past hole row
                if self.free(tr, tc):
                    out.append((tr, tc))          # can land; keep scanning past occupied too
        return out

    def route(self, start, holecol):
        """BFS from start cell to hole (R+1,holecol). returns path of cells or None.
        start must be currently free (it's a splitter output)."""
        goal = (self.R + 1, holecol)
        prev = {start: None}
        q = deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                # reconstruct
                path = []
                x = cur
                while x is not None:
                    path.append(x); x = prev[x]
                return path[::-1]
            r, c = cur
            for nb in self.neighbors(r, c, holecol):
                if nb in prev: continue
                # only allow hole cell that matches holecol
                if nb[0] == self.R + 1 and nb[1] != holecol:
                    continue
                prev[nb] = cur
                q.append(nb)
        return None

    def place_path(self, path):
        for a, b in zip(path[:-1], path[1:]):
            tok = self.token_to(a[0], a[1], b[0], b[1])
            if tok is None: return False
            if a in self.occ: return False
            self.occ[a] = tok
        return True


def hamster_skip_neighbors_fix():
    pass


def build(R, srow, dirperm):
    g = Grid(R)
    # feeders: hamster from (1,i) straight to splitter row (skips intermediate cells,
    # leaving them free for U-outputs / routing). srow==1: no feeder. srow==2: squirrel D.
    for i in range(C):
        s = srow[i]
        if s == 1:
            continue
        elif s == 2:
            if not g.free(1, i): return None
            g.occ[(1, i)] = 'D'
        else:
            if not g.free(1, i): return None
            g.occ[(1, i)] = f'{s-1}D'   # hamster jump to (s,i), skipping 2..s-1
    # splitters
    leaves = []
    for i in range(C):
        r = srow[i]; holes = targets[i]; dirs = dirperm[i]
        if len(set(dirs)) != 3: return None
        cells = []
        for d, hole in zip(dirs, holes):
            dr, dc = DIRS[d]; tr, tc = r + dr, i + dc
            if tr == 0 or not (1 <= tr <= R and 0 <= tc < C): return None
            cells.append((tr, tc, hole))
        if not g.free(r, i): return None
        g.occ[(r, i)] = ''.join(dirs)
        for (tr, tc, hole) in cells:
            if (tr, tc) in g.occ: return None
        leaves += cells
    # reserve all leaf start cells so routes don't clobber each other
    for (tr, tc, hole) in leaves:
        if (tr, tc) in g.occ: return None
        g.occ[(tr, tc)] = 'LEAF'
    # route each leaf (remove own placeholder first)
    leaves.sort(key=lambda x: -abs(x[1] - x[2]))
    for (tr, tc, hole) in leaves:
        del g.occ[(tr, tc)]
        path = g.route((tr, tc), hole)
        if path is None: return None
        if not g.place_path(path): return None
    return g.occ


def search(R, tries, seed=0):
    rng = random.Random(seed)
    perms = list(itertools.permutations(['U', 'D', 'L', 'R'], 3))
    best = None
    for _ in range(tries):
        srow = [rng.randint(1, min(R - 2, 5)) for _ in range(C)]
        dp = [rng.choice(perms) for _ in range(C)]
        occ = build(R, srow, dp)
        if occ is None: continue
        cost, info = evaluate(R, occ)
        if cost is None: continue
        if best is None or cost < best[0]:
            best = (cost, R, srow, dp, dict(E=info['E'], D=info['D'], L=info['L'], b=info['bounces']), dict(occ))
            print(f'  R={R} new best cost={cost} {best[4]}')
            if cost <= 5: return best
    return best


if __name__ == '__main__':
    for R in [8, 9, 10, 11]:
        b = search(R, 40000, seed=1)
        if b:
            print(f'R={R}: BEST cost={b[0]} {b[4]}')
            emit(R, b[5], f'outputs/_cand/maze_R{R}.txt')
        else:
            print(f'R={R}: none')
