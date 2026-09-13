"""Offline assignment estimates for arbitrary per-source integer pieces."""
import random,sys

def assign(A,B,make_pieces,seed=0,restarts=80,steps=800000,geometry5=False,
           geometry4=False):
 pieces=[]
 for src,a in enumerate(A):
  pieces += [(x,src,q) for q,x in enumerate(make_pieces(a))]
 C=len(A); k=len(pieces)//C; rng=random.Random(77123+seed);best=None
 def penalty(perm):
  if not geometry5 and not geometry4:return 0
  dest=[0]*len(pieces)
  for pos,pid in enumerate(perm):dest[pid]=pos//k
  bad=0
  for src in range(C):
   if geometry4:
    col=1 if src==0 else(C-2 if src==C-1 else src);base=4*src
    jd=dest[base+1]
    bad += (jd<=col) if src==0 else ((jd>=col) if src==C-1 else(jd==col))
    bad += dest[base+2]==col and dest[base+3]==col
    continue
   col=1 if src==0 else(C-2 if src==C-1 else src);base=5*src
   jd=dest[base]
   bad += (jd<=col) if src==0 else ((jd>=col) if src==C-1 else(jd==col))
   bad += dest[base+1]==col and dest[base+2]==col
   bad += dest[base+3]==col and dest[base+4]==col
  return bad
 for _ in range(restarts):
  perm=list(range(len(pieces)));rng.shuffle(perm)
  sums=[sum(pieces[perm[k*j+t]][0] for t in range(k)) for j in range(C)]
  cur=sum(abs(sums[j]-B[j]) for j in range(C));pen=penalty(perm)
  for __ in range(steps//restarts):
   x,y=rng.sample(range(len(pieces)),2);bx,by=x//k,y//k
   if bx==by:continue
   px,py=pieces[perm[x]][0],pieces[perm[y]][0]
   old=abs(sums[bx]-B[bx])+abs(sums[by]-B[by])
   nx,ny=sums[bx]-px+py,sums[by]-py+px
   new=abs(nx-B[bx])+abs(ny-B[by])
   perm[x],perm[y]=perm[y],perm[x];npen=penalty(perm);perm[x],perm[y]=perm[y],perm[x]
   delta=new-old+(npen-pen)*1_000_000
   if delta<=0 or rng.random()<0.00015:
    perm[x],perm[y]=perm[y],perm[x];sums[bx],sums[by]=nx,ny;cur+=new-old
    pen=npen
  if pen==0 and(best is None or cur<best[0]):
   target=[-1]*len(pieces)
   for j in range(C):
    for t in range(k):target[perm[k*j+t]]=j
   best=(cur,pieces,target,tuple(sums))
 return best

def sixths(a):
 q,r=divmod(a,6);return [q+(i<r) for i in range(6)]
def third_four_sixths(a):
 q,r=divmod(a,3);third=[q+(i<r) for i in range(3)]
 out=[third[0]]
 for x in third[1:]:out.extend(((x+1)//2,x//2))
 return out
def two_thirds_two_sixths(a):
 q,r=divmod(a,3);third=[q+(i<r) for i in range(3)]
 x=third[2]
 return [third[0],third[1],(x+1)//2,x//2]

if __name__=='__main__':
 d=list(map(int,open(sys.argv[1]).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C]
 for name,fn in [('four_unequal',two_thirds_two_sixths),('five',third_four_sixths),('six',sixths)]:
  z=assign(A,B,fn);print(name,z[0],z[3])
