"""오라클 vs v5 를 동일 공식분포 케이스에서 비교."""
import os, random, re, subprocess, sys, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # 상위 seed_transport 폴더 (v5·채점 exe 위치)
EXE = os.path.join(ROOT, 'public1_offline_optimizer.exe')
ORACLE = os.path.join(HERE, 'cpp_oracle.exe')
V5 = os.path.join(ROOT, 'challenge_submission_rating_v5_balanced.py')
TOTAL = 1_000_000
BINS = {
    5: ((200000,421816),(421817,479291),(479292,539215),(539216,618806),(618807,1000000)),
    6: ((166667,376195),(376196,427656),(427657,481244),(481245,554261),(554262,1000000)),
    7: ((142858,340734),(340735,387307),(387308,435920),(435921,502939),(502940,1000000)),
    8: ((125000,312245),(312246,354780),(354781,399301),(399302,461116),(461117,1000000)),
    9: ((111112,288765),(288766,327921),(327922,368995),(368996,426322),(426323,1000000)),
   10: ((100000,269020),(269021,305310),(305311,343441),(343442,396873),(396874,1000000)),
}

def composition(c, rng):
    cuts = sorted(rng.sample(range(1, TOTAL+c), c-1))
    x = [0]+cuts+[TOTAL+c]
    return [x[i+1]-x[i]-1 for i in range(c)]

def official_case(c, band, rng):
    lo, hi = BINS[c][band]
    while True:
        x, y = composition(c, rng), composition(c, rng)
        a, b = (x, y) if max(x) >= max(y) else (y, x)
        if lo <= max(a) <= hi:
            return a, b

def evalgrid(inp, grid):
    ip = os.path.join(HERE, '_cmp.in')
    gp = os.path.join(HERE, '_cmp.grid')
    open(ip, 'w').write(inp); open(gp, 'w').write(grid)
    p = subprocess.run([EXE, ip, gp, gp+'.out', '0', '0', '1'],
                       text=True, capture_output=True, check=True)
    m = re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)', p.stderr)
    return tuple(map(int, m.groups()))  # cost,E,D,L

def run_sub(cmd, inp, env=None):
    e = dict(os.environ); e.update(env or {})
    p = subprocess.run(cmd, input=inp, text=True, capture_output=True, env=e)
    return p.stdout

def main():
    C = int(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    rng = random.Random(20261400 + C*1009)
    oenv = {'ORACLE_STRIPS': '1', 'ORACLE_LEAN': '1', 'ORACLE_SEEDS': '2'}
    orc, v5c = [], []
    for band in range(5):
        for q in range(n):
            a, b = official_case(C, band, rng)
            inp = f'{C} 2000000 {max(a)}\n'+' '.join(map(str, a))+'\n'+' '.join(map(str, b))+'\n'
            og = run_sub([ORACLE], inp, oenv)
            vg = run_sub([sys.executable, V5], inp)
            oc = evalgrid(inp, og); vc = evalgrid(inp, vg)
            orc.append(oc[0]); v5c.append(vc[0])
            print(f'C{C} b{band} q{q}: oracle={oc[0]:>8} (L{oc[3]})  v5={vc[0]:>8} (L{vc[3]})  '
                  f'{"ORACLE" if oc[0]<vc[0] else "v5":>6} better', flush=True)
    hyb = [min(o, v) for o, v in zip(orc, v5c)]
    print(f'\n=== C{C} n={5*n} ===')
    print(f'oracle: median={int(statistics.median(orc))} max={max(orc)} sum={sum(orc)}')
    print(f'v5    : median={int(statistics.median(v5c))} max={max(v5c)} sum={sum(v5c)}')
    print(f'hybrid: median={int(statistics.median(hyb))} max={max(hyb)} sum={sum(hyb)}  '
          f'(vs v5 sum {100*(1-sum(hyb)/sum(v5c)):.1f}% lower)')
    print(f'oracle beats v5 on {sum(o<v for o,v in zip(orc,v5c))}/{len(orc)} cases')

if __name__ == '__main__':
    main()
