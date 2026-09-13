import os, random, subprocess, sys, re, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from compare_oracle_v5 import official_case

for C in [5, 6, 7, 8, 9, 10]:
    rng = random.Random(777 + C)
    a, b = official_case(C, 2, rng)  # mid band
    inp = f'{C} 2000000 {max(a)}\n' + ' '.join(map(str, a)) + '\n' + ' '.join(map(str, b)) + '\n'
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(HERE, 'challenge_submission_hybrid.py')],
                       input=inp, text=True, capture_output=True)
    dt = time.time() - t0
    R = p.stdout.split('\n', 1)[0] if p.stdout.strip() else 'EMPTY'
    m = re.search(r'chose \w+ cost=\d+', p.stderr)
    chose = m.group(0) if m else '?'
    ip = os.path.join(HERE, '_smk.in'); gp = os.path.join(HERE, '_smk.grid')
    open(ip, 'w').write(inp); open(gp, 'w').write(p.stdout)
    q = subprocess.run([os.path.join(ROOT, 'public1_offline_optimizer.exe'), ip, gp, gp + '.out', '0', '0', '1'],
                       text=True, capture_output=True)
    mm = re.search(r'cost=(\d+) E=\d+ D=\d+ L=(\d+)', q.stderr)
    verify = f'exe cost={mm.group(1)} L={mm.group(2)}' if mm else 'EXE-FAIL'
    print(f'C{C}: R={R}  {chose}  [{verify}]  {dt:.0f}s', flush=True)
print('SMOKE DONE', flush=True)
