import itertools,sys
from thirds_planner import assign_thirds

def tok(d,ch): return ch if d==1 else f'{d}{ch}'
def route(g,r,c,j,R):
 if g[r-1][c]!='X': return False
 if c==j: g[r-1][c]=tok(R+1-r,'D'); return True
 if g[r-1][j]!='X': return False
 g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L'); g[r-1][j]=tok(R+1-r,'D'); return True

def _solve_one(C,T,M,A,B,seed,restarts,steps):
 e,p,target,got=assign_thirds(A,B,restarts,steps,seed)
 ts=[[target[3*i+q] for q in range(3)] for i in range(C)]
 R=2*C+4; g=[['X']*C for _ in range(R)]
 for i in range(C):
  if i==0: r,k,dirs=3,1,('U','D','R')
  elif i==C-1: r,k,dirs=2*C+2,C-2,('U','D','L')
  else: r,k,dirs=2*i+3,i,('L','D','R')
  if len(set(ts[i]))==1:
   # All thirds reunite: keep the original rate-1 stream and use this block
   # only as a collision-free routing row.
   rr=2*i+3
   g[0][i]=tok(rr-1,'D')
   if not route(g,rr,i,ts[i][0],R): return None
   continue
  if i in (0,C-1):
   g[0][i]=tok(r-1,'D'); g[r-1][i]='R' if i==0 else 'L'
  else: g[0][i]=tok(r-1,'D')
  ok=False
  for ds in itertools.permutations(dirs):
   snap=[row[:] for row in g]; g[r-1][k]=''.join(ds); good=True
   for d,j in zip(ds,ts[i]):
    rr,cc=(r-1,k) if d=='U' else ((r+1,k) if d=='D' else (r,k-1 if d=='L' else k+1))
    if not route(g,rr,cc,j,R):
     # A lateral third returning to its own column collides with the splitter.
     # Drop it to the reserved last row, then route horizontally and into burrow.
     if d in ('L','R') and j==k and g[rr-1][cc]=='X' and g[R-1][cc]=='X':
      g[rr-1][cc]=tok(R-rr,'D')
      if not route(g,R,cc,j,R): good=False; break
     else: good=False; break
   if good: ok=True; break
   g=snap
  if not ok:return None
 return R,g,e

def solve(C,T,M,A,B,seed=0,restarts=8,steps=24000,tries=2):
 best=None
 for z in range(tries):
  cand=_solve_one(C,T,M,A,B,seed+z,restarts,steps)
  if cand is not None and (best is None or cand[2]<best[2]): best=cand
 return best

if __name__=='__main__':
 d=list(map(int,sys.stdin.read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 seed=int(sys.argv[1]) if len(sys.argv)>1 else 0
 z=solve(C,T,M,A,B,seed)
 if not z: raise SystemExit('no layout')
 R,g,_=z;print(R);[print(*row) for row in g]
