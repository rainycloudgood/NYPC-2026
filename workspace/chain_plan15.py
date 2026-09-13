"""Find compact dyadic split targets for step-up input 15.

Each of sources 1..7 feeds two adjacent burrows in the monotone transport
decomposition.  A depth-d binary splitter can realize q/2**d of a stream,
up to the exact ceil/floor effects.  This DP chooses depths under a splitter
budget and reports the best total E lower bound before geometric placement.
"""

import sys


def split_count(n, depth, q):
    """Exact number in the first q leaves of a balanced depth tree."""
    sizes = [n]
    for _ in range(depth):
        nxt = []
        for x in sizes:
            nxt.extend(((x + 1) // 2, x // 2))
        sizes = nxt
    return sum(sizes[:q])


def options(n, target, max_depth=8):
    out = []
    for d in range(max_depth + 1):
        den = 1 << d
        center = round(target * den / n)
        for q in range(max(0, center - 2), min(den, center + 2) + 1):
            got = split_count(n, d, q)
            # A prefix selector can be represented by at most d splitters along
            # its boundary; d=0 means the whole stream goes to one side.
            out.append((d, abs(got - target) * 2, got, q, den))
    best = {}
    for x in out:
        key = (x[0], x[2])
        if key not in best or x[1] < best[key][1]:
            best[key] = x
    return list(best.values())


def radix_options(n, target):
    """Uniform radix trees, costed by splitter + completed branch relays."""
    out = []
    for radix in (2, 3, 4):
        for depth in range(0, 9):
            den = radix ** depth
            if den > 65536:
                break
            center = round(target * den / n)
            for q in range(max(0, center - 3), min(den, center + 3) + 1):
                # Balanced leaves differ by at most one; prefix receives large leaves.
                base, rem = divmod(n, den)
                got = q * base + min(q, rem)
                err = 2 * abs(got - target)
                # Boundary chain: one splitter and at most radix-1 terminal relays/level.
                cells = depth * radix
                out.append((cells, err, got, q, den, radix, depth))
    best = {}
    for x in out:
        key = (x[0], x[2])
        if key not in best or x[1] < best[key][1]:
            best[key] = x
    return list(best.values())


def main():
    A = [684, 297, 330, 609, 999, 198, 474]
    left = [363, 116, 231, 547, 540, 98, 160]
    opts = [options(n, x) for n, x in zip(A, left)]
    # dp[splitters] = (E, choices)
    dp = {0: (0, [])}
    for os in opts:
        ndp = {}
        for used, (err, choices) in dp.items():
            for o in os:
                nu = used + o[0]
                if nu > 56:
                    continue
                val = err + o[1]
                if nu not in ndp or val < ndp[nu][0]:
                    ndp[nu] = (val, choices + [o])
        dp = ndp
    for budget in (24, 28, 32, 36, 40, 44, 48, 52, 56):
        candidates = [(e, u, c) for u, (e, c) in dp.items() if u <= budget]
        e, u, choices = min(candidates)
        print(f'budget={budget:2} splitters={u:2} E_lower={e:2}')
        print(' ', [(d, got, f'{q}/{den}') for d, _, got, q, den in choices])

    print('\nactual-cell model (uniform radix per source)')
    ropts = [radix_options(n, x) for n, x in zip(A, left)]
    dp = {0: (0, [])}
    for os in ropts:
        ndp = {}
        for used, (err, choices) in dp.items():
            for o in os:
                nu = used + o[0]
                if nu > 72:
                    continue
                val = err + o[1]
                if nu not in ndp or val < ndp[nu][0]:
                    ndp[nu] = (val, choices + [o])
        dp = ndp
    for budget in (48, 52, 56, 60, 64, 68, 72):
        e, u, choices = min((e, u, c) for u, (e, c) in dp.items() if u <= budget)
        print(f'cells={budget:2} used={u:2} E_lower={e:2}')
        print(' ', [(radix, depth, got, f'{q}/{den}')
                    for _, _, got, q, den, radix, depth in choices])


if __name__ == '__main__':
    main()
