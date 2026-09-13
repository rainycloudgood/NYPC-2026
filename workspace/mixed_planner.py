"""Plan edge halves + interior thirds for compact R=2C+1 routing."""
import itertools, random

def split(a,k,src):
 q,r=divmod(a,k); return [(q+(i<r),src,i) for i in range(k)]

def assign_mixed(A,B,restarts=100,steps=300000,seed_offset=0):
 C=len(A); halves=split(A[0],2,0)+split(A[-1],2,C-1)
 thirds=[p for i in range(1,C-1) for p in split(A[i],3,i)]
 best=None; rng=random.Random(0xA661+C+max(A)+seed_offset*1000003)
 for half_targets in itertools.combinations(range(C),2):
  rest=[j for j in range(C) if j not in half_targets]
  for perm4 in itertools.permutations(range(4)):
   hs=[sum(halves[perm4[2*z+t]][0] for t in range(2)) for z in range(2)]
   hcost=sum(abs(hs[z]-B[half_targets[z]]) for z in range(2))
   for _ in range(max(1,restarts//10)):
    perm=list(range(len(thirds))); rng.shuffle(perm)
    sums=[sum(thirds[perm[3*z+t]][0] for t in range(3)) for z in range(C-2)]
    cur=hcost+sum(abs(sums[z]-B[rest[z]]) for z in range(C-2))
    for _ in range(steps//restarts):
     x,y=rng.sample(range(len(thirds)),2); bx,by=x//3,y//3
     if bx==by: continue
     px,py=thirds[perm[x]][0],thirds[perm[y]][0]
     old=abs(sums[bx]-B[rest[bx]])+abs(sums[by]-B[rest[by]])
     nx,ny=sums[bx]-px+py,sums[by]-py+px
     new=abs(nx-B[rest[bx]])+abs(ny-B[rest[by]])
     if new<=old:
      perm[x],perm[y]=perm[y],perm[x];sums[bx],sums[by]=nx,ny;cur+=new-old
    if best is None or cur<best[0]: best=(cur,half_targets,perm4,tuple(rest),tuple(perm),tuple(hs),tuple(sums),halves,thirds)
 return best


def assign_mixed_fast(A, B, seed_offset=0, shortlist=12, steps=36000):
 """Rating-time variant: shortlist edge-half pairings, then optimize thirds."""
 C=len(A);halves=split(A[0],2,0)+split(A[-1],2,C-1)
 thirds=[p for i in range(1,C-1) for p in split(A[i],3,i)]
 configs=[]
 # Edge columns cannot fan out in the compact layout.  Their two halves must
 # reunite at one target, so only the two source-preserving pair orders are
 # geometrically meaningful.
 for j in range(C):
  for k in range(C):
   if j==k:continue
   for perm4 in ((0,1,2,3),(2,3,0,1)):
    x=sum(halves[q][0] for q in perm4[:2]);y=sum(halves[q][0] for q in perm4[2:])
    configs.append((abs(x-B[j])+abs(y-B[k]),(j,k),perm4,(x,y)))
 configs.sort(key=lambda x:x[0]);configs=configs[:shortlist]
 rng=random.Random(0xFA661+C+max(A)+seed_offset*1000003);best=None
 per=max(800,steps//max(1,len(configs)))
 for hcost,ht,p4,hs in configs:
  rest=tuple(j for j in range(C) if j not in ht)
  for _restart in range(2):
   perm=list(range(len(thirds)));rng.shuffle(perm)
   sums=[sum(thirds[perm[3*z+t]][0] for t in range(3)) for z in range(C-2)]
   cur=hcost+sum(abs(sums[z]-B[rest[z]]) for z in range(C-2))
   for _ in range(per//2):
    x,y=rng.sample(range(len(thirds)),2);bx,by=x//3,y//3
    if bx==by:continue
    px,py=thirds[perm[x]][0],thirds[perm[y]][0]
    old=abs(sums[bx]-B[rest[bx]])+abs(sums[by]-B[rest[by]])
    nx,ny=sums[bx]-px+py,sums[by]-py+px
    new=abs(nx-B[rest[bx]])+abs(ny-B[rest[by]])
    if new<=old or rng.random()<0.00015:
     perm[x],perm[y]=perm[y],perm[x];sums[bx],sums[by]=nx,ny;cur+=new-old
   if best is None or cur<best[0]:
    best=(cur,ht,p4,rest,tuple(perm),tuple(hs),tuple(sums),halves,thirds)
 return best
