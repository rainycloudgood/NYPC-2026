"""Exact oracle for arbitrary weighted-four destination-bus candidates."""
import glob, os, re, subprocess
from solution_bus_four import solve
from weighted_piece_planner import two_thirds_two_sixths

HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'outputs')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
MS={627401,320226,437573,284296,598289,294014,822113,348835}

def exact(inp,z,tag):
 ip=os.path.join(OUT,tag+'.in');gp=os.path.join(OUT,tag+'.grid');op=gp+'.out'
 open(ip,'w').write(inp)
 with open(gp,'w') as f:
  f.write(str(z[0])+'\n');f.writelines(' '.join(x)+'\n' for x in z[1])
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

for path in glob.glob(os.path.join(OUT,'midval_*.in')):
 inp=open(path).read();d=list(map(int,inp.split()));C,T,M=d[:3]
 if M not in MS:continue
 A=d[3:3+C];B=d[3+C:3+2*C];zs=[]
 for seed in range(4):
  for compact in (True,False):
   z=solve(C,T,M,A,B,seed,compact,restarts=8,steps=80000)
   if z:zs.append(z)
 if not zs:print(C,M,'NO_LAYOUT',flush=True);continue
 # Exact-evaluate several low-E assignments: D is intentionally not trusted.
 vals=[]
 for n,z in enumerate(sorted(zs,key=lambda q:q[2])[:4]):
  rates=[0.0]*C
  pieces=[]
  for a in A: pieces.append(two_thirds_two_sixths(a))
  # Reconstructing assignment rates from got is impossible; exact D below is
  # authoritative, so report only the exact cost tuple.
  vals.append((exact(inp,z,f'varrate4_{C}_{M}_{n}'),z))
 best=min(vals,key=lambda q:q[0][0])
 print(C,M,'staticE',best[1][2],'exact',best[0],flush=True)
