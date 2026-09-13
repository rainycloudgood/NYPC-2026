import itertools
from maxhalf_planner import assign_maxhalf

def tok(d,ch):return ch if d==1 else f'{d}{ch}'
def route(g,r,c,j,R):
 if not (1<=r<=R and 0<=c<len(g[0])) or g[r-1][c]!='X':return False
 if c==j:g[r-1][c]=tok(R+1-r,'D');return True
 if g[r-1][j]!='X':return False
 g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L');g[r-1][j]=tok(R+1-r,'D');return True

def solve(C,T,M,A,B,seed=0):
 e,p,target,got,big=assign_maxhalf(A,B,seed=seed)
 ts=[[] for _ in range(C)]
 for q,x in enumerate(p):ts[x[1]].append(target[q])
 R=2*C+4;g=[['X']*C for _ in range(R)]
 for i in range(C):
  r=2*i+3
  dirs=('U','D','R') if i==0 else (('U','D','L') if i==C-1 else ('L','D','R'))
  if len(ts[i])==2:
   dirsets=list(itertools.combinations(dirs,2))
  else:dirsets=[dirs]
  ok=False
  for ds0 in dirsets:
   for ds in itertools.permutations(ds0):
    snap=[row[:] for row in g]
    if g[0][i]!='X' or g[r-1][i]!='X':continue
    g[0][i]=tok(r-1,'D');g[r-1][i]=''.join(ds);good=True
    for d,j in zip(ds,ts[i]):
     rr,cc=(r-1,i) if d=='U' else ((r+1,i) if d=='D' else (r,i-1 if d=='L' else i+1))
     if not route(g,rr,cc,j,R):good=False;break
    if good:ok=True;break
    g=snap
   if ok:break
  if not ok:return None
 return R,g,e
