"""Route 1/3,1/3,1/6,1/6 using a ternary root and binary child."""
import itertools,sys
from weighted_piece_planner import assign,two_thirds_two_sixths

def tok(d,ch):return ch if d==1 else f'{d}{ch}'
def route(g,r,c,j,R):
 if not(1<=r<=R and 0<=c<len(g[0]))or g[r-1][c]!='X':return False
 if c==j:g[r-1][c]=tok(R+1-r,'D');return True
 if g[r-1][j]!='X':return False
 g[r-1][c]=tok(abs(j-c),'R'if j>c else'L');g[r-1][j]=tok(R+1-r,'D');return True

def solve(C,T,M,A,B,seed=0,extra=0):
 z=assign(A,B,two_thirds_two_sixths,seed,restarts=20,steps=120000,geometry4=True)
 if z is None:return None
 e,p,target,got=z;ts=[[target[4*i+q]for q in range(4)]for i in range(C)]
 R=2*C+3+extra;empty=[['X']*C for _ in range(R)];nodes=[0]
 def placements(g,i,limit=120):
  k=1 if i==0 else(C-2 if i==C-1 else i);out=[]
  flex0,side,ha,hb=ts[i]
  dds=[d for d in'LR'if(d=='L'and side<k)or(d=='R'and side>k)]
  for r in range(2,R-1):
   for dd in dds:
    for sw in(0,1):
     flex1,lat=(ha,hb)if sw==0 else(hb,ha)
     if lat==k:continue
     ld='L'if lat<k else'R';ng=[x[:]for x in g]
     if ng[0][i]!='X'or ng[r-1][k]!='X'or ng[r][k]!='X':continue
     ng[0][i]=tok(r-1,'D')
     if i==0:
      if ng[r-1][0]!='X':continue
      ng[r-1][0]='R'
     elif i==C-1:
      if ng[r-1][C-1]!='X':continue
      ng[r-1][C-1]='L'
     ng[r-1][k]='U'+dd+'D'
     if not route(ng,r-1,k,flex0,R):continue
     if not route(ng,r,k-1 if dd=='L'else k+1,side,R):continue
     ng[r][k]='D'+ld
     if not route(ng,r+2,k,flex1,R):continue
     if not route(ng,r+1,k-1 if ld=='L'else k+1,lat,R):continue
     out.append(ng)
     if len(out)>=limit:return out
  return out
 def dfs(g,rem):
  nodes[0]+=1
  if nodes[0]>20000:return None
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
 for extra in(-3,-2,-1,0,1):
  for seed in range(4):
   z=solve(C,T,M,A,B,seed,extra)
   if z and(best is None or(1<<(z[0]-C))+z[2]<(1<<(best[0]-C))+best[2]):best=z
 if best is None:raise SystemExit('no layout')
 R,g,e,got=best;print(R);[print(*row)for row in g];print('E_est',e,'got',got,file=sys.stderr)
