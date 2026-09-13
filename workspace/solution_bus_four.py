"""Weighted-four splitters feeding one shared horizontal bus per destination."""
import sys
from weighted_piece_planner import assign,two_thirds_two_sixths

def tok(n,ch):return ch if n==1 else f'{n}{ch}'

def solve(C,T,M,A,B,seed=0,compact=False,restarts=80,steps=800000):
 e,p,target,got=assign(A,B,two_thirds_two_sixths,seed,restarts=restarts,steps=steps)
 ts=[[target[4*i+q]for q in range(4)]for i in range(C)]
 split_rows=9 if compact else 11;R=split_rows+C;g=[['X']*C for _ in range(R)]
 # Destination buses.  Seeds may merge here safely because identity is no
 # longer needed; each bus drains only into its own burrow.
 for j in range(C):
  br=split_rows+1+j
  for c in range(C):
   if c<j:g[br-1][c]='R'
   elif c>j:g[br-1][c]='L'
   else:g[br-1][c]=tok(R+1-br,'D')

 def send(r,c,j):
  if not(1<=r<=split_rows and 0<=c<C)or g[r-1][c]!='X':return False
  br=split_rows+1+j;g[r-1][c]=tok(br-r,'D');return True

 for i in range(C):
  r=3+(2 if compact else 3)*(i%3)
  side='R'if i<C-1 else'L';dc=1 if side=='R'else-1
  # Input jumps directly to the ternary root.
  if g[0][i]!='X'or g[r-1][i]!='X'or g[r][i]!='X':return None
  g[0][i]=tok(r-1,'D');g[r-1][i]='U'+side+'D';g[r][i]='D'+side
  starts=((r-1,i),(r,i+dc),(r+2,i),(r+1,i+dc))
  for (rr,cc),j in zip(starts,ts[i]):
   if not send(rr,cc,j):return None
 return R,g,e,got

if __name__=='__main__':
 d=list(map(int,sys.stdin.read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];best=None
 for compact in (True,False):
  for seed in range(4):
   z=solve(C,T,M,A,B,seed,compact)
   if z and(best is None or(1<<(z[0]-C))+z[2]<(1<<(best[0]-C))+best[2]):best=z
 if best is None:raise SystemExit('no layout')
 R,g,e,got=best;print(R);[print(*row)for row in g];print('E_est',e,'got',got,file=sys.stderr)
