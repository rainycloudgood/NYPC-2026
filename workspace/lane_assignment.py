"""Pareto search: weighted-four delivery error under a lane-pressure cap."""
import random,sys
from weighted_piece_planner import two_thirds_two_sixths

def run(A,B,cap,seed=0,restarts=80,steps=1200000):
 C=len(A);pieces=[]
 for src,a in enumerate(A):pieces += [(x,src,q)for q,x in enumerate(two_thirds_two_sixths(a))]
 rng=random.Random(91001+cap*31+seed);best=None
 def pressure(perm):
  dest=[0]*len(pieces)
  for pos,pid in enumerate(perm):dest[pid]=pos//4
  cnt=[0]*C
  for pid,(_,src,_) in enumerate(pieces):
   k=1 if src==0 else(C-2 if src==C-1 else src);j=dest[pid]
   for c in range(min(k,j),max(k,j)+1):cnt[c]+=1
  return max(cnt),tuple(cnt),dest
 for _ in range(restarts):
  perm=list(range(4*C));rng.shuffle(perm)
  sums=[sum(pieces[perm[4*j+t]][0]for t in range(4))for j in range(C)]
  err=sum(abs(sums[j]-B[j])for j in range(C));pr,_,_=pressure(perm)
  for __ in range(steps//restarts):
   x,y=rng.sample(range(4*C),2);bx,by=x//4,y//4
   if bx==by:continue
   px,py=pieces[perm[x]][0],pieces[perm[y]][0]
   old=abs(sums[bx]-B[bx])+abs(sums[by]-B[by]);nx,ny=sums[bx]-px+py,sums[by]-py+px
   new=abs(nx-B[bx])+abs(ny-B[by])
   perm[x],perm[y]=perm[y],perm[x];npr,counts,dest=pressure(perm);perm[x],perm[y]=perm[y],perm[x]
   delta=new-old+(max(0,npr-cap)-max(0,pr-cap))*2_000_000
   if delta<=0 or rng.random()<0.00012:
    perm[x],perm[y]=perm[y],perm[x];sums[bx],sums[by]=nx,ny;err+=new-old;pr=npr
  if pr<=cap and(best is None or err<best[0]):
   pr,counts,dest=pressure(perm);best=(err,counts,tuple(sums),tuple(dest))
 return best

if __name__=='__main__':
 d=list(map(int,open(sys.argv[1]).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C];cap=int(sys.argv[2])
 print(cap,run(A,B,cap))
