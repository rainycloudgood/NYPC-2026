"""Split the largest source in halves and every other source in thirds."""
import random

def split(a,k,src):
 q,r=divmod(a,k); return [(q+(i<r),src,i) for i in range(k)]

def assign_maxhalf(A,B,restarts=8,steps=20000,seed=0):
 C=len(A); big=max(range(C),key=A.__getitem__)
 pieces=[]
 for i,a in enumerate(A): pieces += split(a,2 if i==big else 3,i)
 rng=random.Random(0x2A3F+C+max(A)+seed*1000003); best=None
 for short in range(C):
  caps=[2 if j==short else 3 for j in range(C)]
  starts=[]; z=0
  for x in caps: starts.append(z); z+=x
  for _ in range(restarts):
   perm=list(range(len(pieces))); rng.shuffle(perm)
   sums=[sum(pieces[perm[starts[j]+t]][0] for t in range(caps[j])) for j in range(C)]
   cur=sum(abs(sums[j]-B[j]) for j in range(C))
   posbin=[0]*len(pieces)
   for j in range(C):
    for p in range(starts[j],starts[j]+caps[j]):posbin[p]=j
   for __ in range(steps//restarts):
    x,y=rng.sample(range(len(pieces)),2); bx,by=posbin[x],posbin[y]
    if bx==by:continue
    px,py=pieces[perm[x]][0],pieces[perm[y]][0]
    old=abs(sums[bx]-B[bx])+abs(sums[by]-B[by])
    nx,ny=sums[bx]-px+py,sums[by]-py+px
    new=abs(nx-B[bx])+abs(ny-B[by])
    if new<=old or rng.random()<0.0001:
     perm[x],perm[y]=perm[y],perm[x];sums[bx],sums[by]=nx,ny;cur+=new-old
   if best is None or cur<best[0]:
    target=[-1]*len(pieces)
    for j in range(C):
     for p in range(starts[j],starts[j]+caps[j]):target[perm[p]]=j
    best=(cur,pieces,target,tuple(sums),big)
 return best
