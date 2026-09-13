"""Lift a valid layout by one row while preserving every route to a burrow."""

import os
import re
import sys


def main():
    src, dst = sys.argv[1:3]
    C = int(sys.argv[3])
    words = open(src).read().split()
    R = int(words[0])
    body = words[1:]
    grid = [body[r*C:(r+1)*C] for r in range(R)]

    # Numeric downward tunnels that used to hit the burrow must cross the new row.
    for r in range(1, R + 1):
        for c in range(C):
            m = re.fullmatch(r'(\d+)D', grid[r - 1][c])
            if m and r + int(m.group(1)) == R + 1:
                grid[r - 1][c] = f'{int(m.group(1)) + 1}D'

    # A squirrel D in the old last row now lands on this relay row.
    grid.append(['D'] * C)
    with open(dst, 'w') as f:
        f.write(str(R + 1) + '\n')
        for row in grid:
            f.write(' '.join(row) + '\n')


if __name__ == '__main__':
    main()
