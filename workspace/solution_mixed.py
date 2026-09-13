import itertools, sys
from mixed_planner import assign_mixed, assign_mixed_fast

def tok(d,ch): return ch if d==1 else f'{d}{ch}'

def route(g,r,c,j,R):
 if g[r-1][c]!='X': return False
 if c==j:
  g[r-1][c]=tok(R+1-r,'D'); return True
 if g[r-1][j]!='X': return False
 g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L')
 g[r-1][j]=tok(R+1-r,'D'); return True

def solve(C,T,M,A,B,seed_offset=0):
 x=assign_mixed(A,B,4,15000,seed_offset); _,ht,p4,rest,perm,_,_,halves,thirds=x
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


def solve_fast(C,T,M,A,B,seed_offset=0):
 x=assign_mixed_fast(A,B,seed_offset);_,ht,p4,rest,perm,_,_,halves,thirds=x
 targets=[[] for _ in range(C)]
 for z in range(2):
  for t in range(2):targets[halves[p4[2*z+t]][1]].append(ht[z])
 for pos,p in enumerate(perm):targets[thirds[p][1]].append(rest[pos//3])
 R=2*C+1;g=[['X']*C for _ in range(R)]
 for i in range(C):
  r=2*i+2
  if len(set(targets[i]))==1:
   g[0][i]=tok(r-1,'D')
   if not route(g,r,i,targets[i][0],R):return None
   continue
  if i in (0,C-1):return None
  ok=False
  for ds in itertools.permutations(('L','D','R')):
   snap=[row[:] for row in g];g[0][i]=tok(r-1,'D');g[r-1][i]=''.join(ds);good=True
   for d,j in zip(ds,targets[i]):
    rr,cc=(r,i-1) if d=='L' else ((r,i+1) if d=='R' else (r+1,i))
    if not route(g,rr,cc,j,R):good=False;break
   if good:ok=True;break
   g=snap
  if not ok:return None
 return R,g,x[0]

if __name__=='__main__':
 d=list(map(int,sys.stdin.read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 seed=int(sys.argv[1]) if len(sys.argv)>1 else 0
 z=solve(C,T,M,A,B,seed)
 if not z: raise SystemExit('no layout')
 R,g,_e=z;print(R);[print(*row) for row in g]
