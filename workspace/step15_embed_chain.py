"""Exact-cover embedding of the fresh depth-3 MILP chain plan into 8x8."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optimizer as O

C = R = 8
DEST = [
    [7, 4, 2, 3], [6, 5, 4, 3], [1, 1, 4, 7], [5, 4, 4, 2],
    [3, 2, 1, 4], [0, 1, 7, 3], [0, 5, 5, 6], [6, 0, 7, 1],
]


def neighbors(cell):
    r, c = cell
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x = r + dr, c + dc
        if 0 <= x[0] < R and 0 <= x[1] < C:
            yield x


def direction(a, b):
    dr, dc = b[0] - a[0], b[1] - a[1]
    return {(1, 0): "D", (-1, 0): "U", (0, 1): "R", (0, -1): "L"}[(dr, dc)]


def embeddings(src, limit=200000):
    start = (0, src)
    roots = [start] + [(r, src) for r in range(1, R)]
    out = []
    for s0 in roots:
        # Other sources own every other top-row cell.
        reserved = {(0, c) for c in range(C) if c != src}
        base = {start, s0} | reserved
        for l0 in neighbors(s0):
            if l0[1] != DEST[src][0] or l0 in base:
                continue
            used0 = base | {l0}
            for s1 in neighbors(s0):
                if s1 in used0 or s1[0] == 0:
                    continue
                used1 = used0 | {s1}
                for l1 in neighbors(s1):
                    if l1[1] != DEST[src][1] or l1 in used1 or l1[0] == 0:
                        continue
                    used2 = used1 | {l1}
                    for s2 in neighbors(s1):
                        if s2 in used2 or s2[0] == 0:
                            continue
                        used3 = used2 | {s2}
                        ls2 = [x for x in neighbors(s2)
                               if x[1] == DEST[src][2] and x not in used3 and x[0] != 0]
                        ls3 = [x for x in neighbors(s2)
                               if x[1] == DEST[src][3] and x not in used3 and x[0] != 0]
                        for l2 in ls2:
                            for l3 in ls3:
                                if l2 == l3:
                                    continue
                                own = {start, s0, s1, s2, l0, l1, l2, l3}
                                # start==s0 for a root splitter, otherwise start is a relay.
                                out.append((own, (s0, s1, s2), (l0, l1, l2, l3)))
                                if len(out) >= limit:
                                    return out
    return out


def place(options):
    chosen = [None] * C
    occupied = set()

    def dfs(left):
        if not left:
            return True
        best_src = None;valid = None
        for src in left:
            cur = [x for x in options[src] if not (x[0] & occupied)]
            if not cur:
                return False
            if valid is None or len(cur) < len(valid):
                best_src, valid = src, cur
        rest = [x for x in left if x != best_src]
        # Prefer compact roots and lower rows to reduce finishing delay.
        valid.sort(key=lambda x: (len(x[0]), max(r for r, _ in x[0]), sum(r for r, _ in x[0])))
        for item in valid:
            chosen[best_src] = item;occupied.update(item[0])
            if dfs(rest):
                return True
            occupied.difference_update(item[0]);chosen[best_src] = None
        return False

    return chosen if dfs(list(range(C))) else None


def build(chosen):
    grid = [["X"] * C for _ in range(R)]
    for src, item in enumerate(chosen):
        _, (s0, s1, s2), (l0, l1, l2, l3) = item
        start = (0, src)
        if s0 != start:
            dist = s0[0]
            grid[0][src] = "D" if dist == 1 else f"{dist}D"
        grid[s0[0]][s0[1]] = direction(s0, l0) + direction(s0, s1)
        grid[s1[0]][s1[1]] = direction(s1, l1) + direction(s1, s2)
        grid[s2[0]][s2[1]] = direction(s2, l2) + direction(s2, l3)
        for leaf in (l0, l1, l2, l3):
            dist = R - leaf[0]
            grid[leaf[0]][leaf[1]] = "D" if dist == 1 else f"{dist}D"
    return grid


def main():
    options = []
    for src in range(C):
        x = embeddings(src);options.append(x)
        print("source", src, "embeddings", len(x), flush=True)
    chosen = place(options)
    if chosen is None:
        print("NO EMBEDDING")
        return 1
    grid = build(chosen);body = sum(grid, [])
    C0, T, M, A, B = O.read_input(15)
    score = O.evaluate(C0, T, M, A, B, R, body)
    path = os.path.join(O.OUT_DIR, "output_15_chain_milp_trial.txt")
    with open(path, "w") as f:
        f.write(str(R) + "\n")
        for row in grid:f.write(" ".join(row) + "\n")
    print("TRIAL", path, "score", score)
    return 0


if __name__ == "__main__":raise SystemExit(main())
