"""Route 1/3 + four 1/6-like streams using three splitters per source."""
import itertools,sys
from weighted_piece_planner import assign,third_four_sixths

def tok(d,ch):return ch if d==1 else f'{d}{ch}'
def route(g,r,c,j,R):
 if not(1<=r<=R and 0<=c<len(g[0])) or g[r-1][c]!='X':return False
 if c==j:g[r-1][c]=tok(R+1-r,'D');return True
 if g[r-1][j]!='X':return False
 g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L');g[r-1][j]=tok(R+1-r,'D');return True

def solve(C,T,M,A,B,seed=0,extra=0):
 z=assign(A,B,third_four_sixths,seed,restarts=20,steps=120000,geometry5=True)
 if z is None:return None
 e,p,target,got=z
 ts=[[target[5*i+q] for q in range(5)] for i in range(C)]
 R=2*C+4+extra;empty=[['X']*C for _ in range(R)];nodes=[0]

 def placements(g,i,limit=120):
  k=1 if i==0 else(C-2 if i==C-1 else i);out=[]
  direct=ts[i][0];pairs=(ts[i][1:3],ts[i][3:5])
  direct_dirs=[d for d in 'LR' if (d=='L' and direct<k) or(d=='R' and direct>k)]
  if not direct_dirs:return []
  for r in range(3,R-1):
   for dd in direct_dirs:
    for swaps in itertools.product((0,1),repeat=2):
     flex=[];lat=[];goodpair=True
     for pair,sw in zip(pairs,swaps):
      f,l=(pair[sw],pair[1-sw])
      if l==k:goodpair=False;break
      flex.append(f);lat.append(l)
     if not goodpair:continue
     ng=[x[:] for x in g]
     if any(ng[x-1][k]!='X' for x in (r-1,r,r+1)):continue
     if ng[0][i]!='X':continue
     ng[0][i]=tok(r-1,'D')
     if i==0:
      if ng[r-1][0]!='X':continue
      ng[r-1][0]='R'
     elif i==C-1:
      if ng[r-1][C-1]!='X':continue
      ng[r-1][C-1]='L'
     # Direction order controls which branch receives the remainder.
     # The planner models the unsplit third as piece 0, then upper and lower.
     ng[r-1][k]=dd+'UD'
     if not route(ng,r,k-1 if dd=='L' else k+1,direct,R):continue
     good=True
     for child,vr,jf,jl,vd in ((r-1,r-2,flex[0],lat[0],'U'),
                                (r+1,r+2,flex[1],lat[1],'D')):
      ld='L' if jl<k else'R';ng[child-1][k]=vd+ld
      if not route(ng,vr,k,jf,R) or not route(ng,child,k-1 if ld=='L' else k+1,jl,R):good=False;break
     if good:out.append(ng)
     if len(out)>=limit:return out
  return out

 def dfs(g,rem):
  nodes[0]+=1
  if nodes[0]>10000:return None
  if not rem:return g
  choice=None;opts=None
  for i in rem:
   q=placements(g,i)
   if not q:return None
   if opts is None or len(q)<len(opts):choice,opts=i,q
  nr=[i for i in rem if i!=choice]
  for ng in opts:
   ans=dfs(ng,nr)
   if ans is not None:return ans
  return None
 g=dfs(empty,list(range(C)))
 return None if g is None else(R,g,e,got)

if __name__=='__main__':
 d=list(map(int,sys.stdin.read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];best=None
 for extra in (1,):
  for seed in range(2):
   z=solve(C,T,M,A,B,seed,extra)
   if z and(best is None or(1<<(z[0]-C))+z[2]<(1<<(best[0]-C))+best[2]):best=z
 if best is None:raise SystemExit('no layout')
 R,g,e,got=best;print(R);[print(*row) for row in g];print('E_est',e,'got',got,file=sys.stderr)
