"""Randomized best-fit packing of weighted stream intervals into shared lanes."""
import random,sys
from weighted_piece_planner import assign,two_thirds_two_sixths

def pack(C,A,pieces,target,K,tries=20000):
 items=[]
 for q,(amt,src,part)in enumerate(pieces):
  k=1 if src==0 else(C-2 if src==C-1 else src);j=target[q]
  items.append((amt/A[src],min(k,j),max(k,j),q,src,j,amt))
 rng=random.Random(44551+K);best=None
 for it in range(tries):
  # Large/long intervals first, with jitter to escape greedy traps.
  order=sorted(items,key=lambda x:-(x[0]*(x[2]-x[1]+1)+rng.random()*0.08))
  load=[[0.0]*C for _ in range(K)];where={};ok=True
  for w,a,b,q,src,j,amt in order:
   opts=[]
   for lane in range(K):
    peak=max(load[lane][c]+w for c in range(a,b+1))
    if peak<=1.0000001:opts.append((peak+0.02*sum(load[lane]),rng.random(),lane))
   if not opts:ok=False;break
   lane=min(opts)[2];where[q]=lane
   for c in range(a,b+1):load[lane][c]+=w
  if ok:return where,load,items
  placed=len(where)
  if best is None or placed>best[0]:best=(placed,load)
 return None

if __name__=='__main__':
 d=list(map(int,open(sys.argv[1]).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C]
 e,p,t,got=assign(A,B,two_thirds_two_sixths,restarts=80,steps=800000)
 for K in range(4,9):
  z=pack(C,A,p,t,K)
  print('lanes',K,'success',z is not None,'E',e)
  if z:
   where,load,items=z
   print(' peaks',[round(max(x),4)for x in load]);print(' assignment',where);break
