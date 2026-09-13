"""Search exact transports whose required splitter trees are cheap to embed."""
import argparse,random
import treegen

def stats(t):
 if t[0]=='leaf':return 1,1,1
 z=[stats(x) for x in t[2]]
 return 1+sum(x[0] for x in z),sum(x[1] for x in z),1+max(x[2] for x in z)

def perm_transport(A,B,pi,pj):
 C=len(A);aa=[A[i] for i in pi];bb=[B[j] for j in pj]
 raw=treegen.transport(C,aa,bb);g=[[] for _ in range(C)]
 for ii,row in enumerate(raw):
  for jj,x in row:g[pi[ii]].append([pj[jj],x])
 return g

def score(A,g,seed):
 rng=random.Random(seed);ss=[]
 for i,a in enumerate(A):ss.append(stats(treegen.plan_tree(a,[x[:] for x in g[i]],rng)))
 return sum(x[0] for x in ss),sum(x[1] for x in ss),max(x[2] for x in ss)

ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('-n',type=int,default=3000)
args=ap.parse_args();d=list(map(int,open(args.input).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C]
rng=random.Random(20260714+C);best=None
for it in range(args.n):
 pi=list(range(C));pj=list(range(C));rng.shuffle(pi);rng.shuffle(pj);g=perm_transport(A,B,pi,pj)
 for q in range(2):
  z=score(A,g,it*17+q)
  if best is None or z<best[0]:best=(z,pi[:],pj[:],g);print('best',it,z,'flows',sum(map(len,g)),flush=True)
print('FINAL',best)
