"""Exact-transport splitter-tree synthesis with a MILP grid embedder.

This is an offline research builder.  It searches sparse exact transports,
chooses low-node splitter trees, and places every tree node in the legal grid.
Leaves are forced into their destination column and jump straight to a burrow.
"""
import argparse, random, time
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
import treegen


def perm_transport(A,B,pi,pj):
 C=len(A);raw=treegen.transport(C,[A[i] for i in pi],[B[j] for j in pj]);g=[[] for _ in range(C)]
 for ii,row in enumerate(raw):
  for jj,x in row:g[pi[ii]].append([pj[jj],x])
 return g

def tstats(t):
 if t[0]=='leaf':return 1,1
 z=[tstats(x) for x in t[2]];return 1+sum(x[0] for x in z),1+max(x[1] for x in z)

def search_trees(A,B,tries,seed=0):
 C=len(A);rng=random.Random(seed);best=None
 for it in range(tries):
  pi=list(range(C));pj=list(range(C));rng.shuffle(pi);rng.shuffle(pj);flow=perm_transport(A,B,pi,pj)
  for q in range(2):
   trng=random.Random(seed+it*37+q);trees=[treegen.plan_tree(A[i],[x[:] for x in flow[i]],trng) for i in range(C)]
   raw=[tstats(t) for t in trees]
   # A singleton sent to another column needs one horizontal relay.
   extra=sum(t[0]=='leaf' and t[1]!=i for i,t in enumerate(trees))
   key=(sum(x[0] for x in raw)+extra,max(x[1] for x in raw),sum(map(len,flow)))
   if best is None or key<best[0]:
    best=(key,flow,trees,pi,pj);print('transport',it,'key',key,flush=True)
 return best

def flatten(trees):
 nodes=[];edges=[];roots=[]
 def add(t,src,isroot=False):
  if t[0]=='leaf':
   nid=len(nodes);nodes.append({'kind':'leaf','col':t[1],'src':src});return nid
  nid=len(nodes);nodes.append({'kind':'split','col':src if isroot else None,'src':src})
  for ch in t[2]:
   cid=add(ch,src,False);edges.append((nid,cid,'adj'))
  return nid
 for src,t in enumerate(trees):
  if t[0]=='leaf' and t[1]!=src:
   rid=len(nodes);nodes.append({'kind':'relay','col':src,'src':src})
   lid=add(t,src,False);edges.append((rid,lid,'row'));roots.append(rid)
  else:
   rid=add(t,src,True);nodes[rid]['col']=src;roots.append(rid)
 return nodes,edges,roots

def embed(C,R,nodes,edges,roots,time_limit):
 rows=R-1;P=rows*C;N=len(nodes);V=N*P
 def vid(n,r,c):return n*P+(r-1)*C+c
 lb=np.zeros(V);ub=np.ones(V);obj=np.zeros(V)
 for n,node in enumerate(nodes):
  fixed=node['col']
  for r in range(1,R):
   for c in range(C):
    v=vid(n,r,c);obj[v]=r*1e-5
    if fixed is not None and c!=fixed:ub[v]=0
 rr=[];cc=[];vv=[];lo=[];hi=[];rowid=0
 # Every node occupies exactly one cell.
 for n in range(N):
  for p in range(P):rr.append(rowid);cc.append(n*P+p);vv.append(1)
  lo.append(1);hi.append(1);rowid+=1
 # No two nodes share a cell.
 for p in range(P):
  for n in range(N):rr.append(rowid);cc.append(n*P+p);vv.append(1)
  lo.append(-np.inf);hi.append(1);rowid+=1
 # Child position implies a legal parent position.
 for parent,child,kind in edges:
  for r in range(1,R):
   for c in range(C):
    rr.append(rowid);cc.append(vid(child,r,c));vv.append(1)
    if kind=='adj':
     for pr,pc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
      if 1<=pr<R and 0<=pc<C:rr.append(rowid);cc.append(vid(parent,pr,pc));vv.append(-1)
    else:
     pc=nodes[parent]['col']
     rr.append(rowid);cc.append(vid(parent,r,pc));vv.append(-1)
    lo.append(-np.inf);hi.append(0);rowid+=1
 A=coo_matrix((vv,(rr,cc)),shape=(rowid,V)).tocsr()
 print('MILP R',R,'nodes',N,'vars',V,'rows',rowid,'nnz',A.nnz,flush=True)
 res=milp(obj,integrality=np.ones(V),bounds=Bounds(lb,ub),
          constraints=LinearConstraint(A,np.array(lo),np.array(hi)),
          options={'time_limit':time_limit,'mip_rel_gap':0})
 if res.x is None:return None,res
 pos=[]
 for n in range(N):
  p=int(np.argmax(res.x[n*P:(n+1)*P]));pos.append((1+p//C,p%C))
 return pos,res

def token(d,ch):return ch if d==1 else str(d)+ch
def make_grid(C,R,nodes,edges,roots,pos):
 g=[['X']*C for _ in range(R)];children={n:[] for n in range(len(nodes))}
 for p,ch,kind in edges:children[p].append((ch,kind))
 for src,root in enumerate(roots):
  rr,cc=pos[root];g[0][src]=token(rr,'D')
 for n,node in enumerate(nodes):
  r,c=pos[n]
  if node['kind']=='leaf':g[r][c]=token(R-r,'D')
  elif node['kind']=='relay':
   ch=children[n][0][0];_,dc=pos[ch];g[r][c]=token(abs(dc-c),'R' if dc>c else 'L')
  else:
   ds=[]
   for ch,_ in children[n]:
    rr,cc=pos[ch]
    ds.append('U' if rr<r else ('D' if rr>r else ('L' if cc<c else 'R')))
   g[r][c]=''.join(ds)
 return g

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--tries',type=int,default=1500)
 ap.add_argument('--rmin',type=int);ap.add_argument('--time',type=float,default=60);ap.add_argument('--out',required=True)
 a=ap.parse_args();d=list(map(int,open(a.input).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 best=search_trees(A,B,a.tries,20260714+C);print('BEST TRANSPORT',best[0],best[1],flush=True)
 nodes,edges,roots=flatten(best[2]);start=a.rmin or C+8
 for R in range(start,C+21):
  pos,res=embed(C,R,nodes,edges,roots,a.time)
  print('result',R,res.message,'fun',res.fun,flush=True)
  if pos is not None:
   g=make_grid(C,R,nodes,edges,roots,pos)
   with open(a.out,'w') as f:f.write(str(R)+'\n');f.writelines(' '.join(x)+'\n' for x in g)
   print('SAVED',a.out,'R',R);return
 raise SystemExit('no embedding')

if __name__=='__main__':main()
