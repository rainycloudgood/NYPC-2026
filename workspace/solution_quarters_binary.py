"""Four equal streams via a two-level binary splitter, for high-M cases."""
import itertools
import sys
from quarters_planner import assign_quarters

def tok(d,ch):return ch if d==1 else f'{d}{ch}'
def route(g,r,c,j,R):
 if g[r-1][c]!='X':return False
 if c==j:g[r-1][c]=tok(R+1-r,'D');return True
 if g[r-1][j]!='X':return False
 g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L');g[r-1][j]=tok(R+1-r,'D');return True

def solve(C,T,M,A,B,seed=0,extra=0):
 z=assign_quarters(A,B,seed,restarts=16,steps=180000,min_sides=0,min_lateral=2)
 if z is None:return None
 e,p,target,got=z; ts=[[target[4*i+q] for q in range(4)] for i in range(C)]
 R=2*C+5+extra; empty=[['X']*C for _ in range(R)]; nodes=[0]

 def placements(g,i,limit=100):
  k=1 if i==0 else (C-2 if i==C-1 else i)
  out=[]
  for r in range(3,R-1):
   for lateral_ids in itertools.combinations([q for q,j in enumerate(ts[i]) if j!=k],2):
    lateral=[ts[i][q] for q in lateral_ids]
    flex=[ts[i][q] for q in range(4) if q not in lateral_ids]
    for lateral in (lateral,lateral[::-1]):
     ng=[x[:] for x in g]
     if ng[0][i]!='X' or ng[r-1][k]!='X' or ng[r-2][k]!='X' or ng[r][k]!='X':continue
     ng[0][i]=tok(r-1,'D')
     if i==0:
      if ng[r-1][0]!='X':continue
      ng[r-1][0]='R'
     elif i==C-1:
      if ng[r-1][C-1]!='X':continue
      ng[r-1][C-1]='L'
     ng[r-1][k]='UD';good=True
     # Upper child: U is flexible, lateral branch points toward its target.
     for child_row,vertical_row,jf,jl,vd in ((r-1,r-2,flex[0],lateral[0],'U'),
                                             (r+1,r+2,flex[1],lateral[1],'D')):
      ld='L' if jl<k else 'R'; ng[child_row-1][k]=vd+ld
      if not route(ng,vertical_row,k,jf,R):good=False;break
      if not route(ng,child_row,k-1 if ld=='L' else k+1,jl,R):good=False;break
     if good:out.append(ng)
     if len(out)>=limit:return out
  return out

 def dfs(g,rem):
  nodes[0]+=1
  if nodes[0]>50000:return None
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
 return None if g is None else (R,g,e,got)

if __name__=='__main__':
 d=list(map(int,sys.stdin.read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 best=None
 for extra in (-3,-2,-1,0):
  for seed in range(8):
   z=solve(C,T,M,A,B,seed,extra)
   if z and (best is None or ((1<<(z[0]-C))+z[2]) < ((1<<(best[0]-C))+best[2])):best=z
 if best is None:raise SystemExit('no layout')
 R,g,e,got=best;print(R);[print(*row) for row in g]
 print('E_est',e,'got',got,file=sys.stderr)
