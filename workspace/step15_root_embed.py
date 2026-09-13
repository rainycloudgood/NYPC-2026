"""Embed exact split trees with their roots directly in the source row.

The older builder unnecessarily reserved row 1 for a relay and embedded every
tree below it.  For test 15 that changes a 62-node exact construction into a
70-cell construction.  Here the root device itself receives flower seeds, so
all 64 board cells are usable.
"""
import argparse, random
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
import treegen
from milp_exact_tree_builder import perm_transport, tstats, flatten


def candidate_trees(A,B,tries,seed=0,limit=64):
    """Keep diverse exact trees that fit the raw 8x8 node budget."""
    C=len(A);rng=random.Random(seed);pool={}
    for it in range(tries):
        pi=list(range(C));pj=list(range(C));rng.shuffle(pi);rng.shuffle(pj)
        flow=perm_transport(A,B,pi,pj)
        for q in range(2):
            trees=[treegen.plan_tree(A[i],[x[:] for x in flow[i]],random.Random(seed+it*37+q)) for i in range(C)]
            raw=[tstats(t) for t in trees]
            extra=sum(t[0]=='leaf' and t[1]!=i for i,t in enumerate(trees))
            key=(sum(x[0] for x in raw)+extra,max(x[1] for x in raw),sum(map(len,flow)))
            if key[0]<=limit:
                sig=repr(flow)
                old=pool.get(sig)
                if old is None or key<old[0]:pool[sig]=(key,flow,trees)
        if it%10000==0 and pool:print('search',it,'pool',len(pool),'best',min(x[0] for x in pool.values()),flush=True)
    return sorted(pool.values(),key=lambda x:x[0])


def embed(C, R, nodes, edges, roots, time_limit):
    P = R*C; N=len(nodes); V=N*P
    def vid(n,r,c): return n*P+r*C+c
    lb=np.zeros(V); ub=np.ones(V); obj=np.zeros(V)
    root_info={n:(0,src) for src,n in enumerate(roots)}
    for n,node in enumerate(nodes):
        fixed_col=node['col']
        for r in range(R):
            for c in range(C):
                v=vid(n,r,c); obj[v]=r*1e-6
                if n in root_info:
                    if (r,c)!=root_info[n]: ub[v]=0
                elif r==0: ub[v]=0  # top row is exactly the eight roots
                elif fixed_col is not None and c!=fixed_col: ub[v]=0
    rr=[];cc=[];vv=[];lo=[];hi=[];rowid=0
    for n in range(N):
        for p in range(P):rr.append(rowid);cc.append(n*P+p);vv.append(1)
        lo.append(1);hi.append(1);rowid+=1
    for p in range(P):
        for n in range(N):rr.append(rowid);cc.append(n*P+p);vv.append(1)
        lo.append(-np.inf);hi.append(1);rowid+=1
    for parent,child,kind in edges:
        for r in range(R):
            for c in range(C):
                rr.append(rowid);cc.append(vid(child,r,c));vv.append(1)
                if kind=='adj':
                    for pr,pc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                        if 0<=pr<R and 0<=pc<C:
                            rr.append(rowid);cc.append(vid(parent,pr,pc));vv.append(-1)
                elif kind=='row':
                    pc=nodes[parent]['col']
                    rr.append(rowid);cc.append(vid(parent,r,pc));vv.append(-1)
                else: # axis-aligned hamster jump
                    for pc in range(C):
                        rr.append(rowid);cc.append(vid(parent,r,pc));vv.append(-1)
                    for pr in range(R):
                        if pr!=r:rr.append(rowid);cc.append(vid(parent,pr,c));vv.append(-1)
                lo.append(-np.inf);hi.append(0);rowid+=1
    mat=coo_matrix((vv,(rr,cc)),shape=(rowid,V)).tocsr()
    print('MILP',N,'nodes',V,'vars',rowid,'rows',flush=True)
    res=milp(obj,integrality=np.ones(V),bounds=Bounds(lb,ub),
             constraints=LinearConstraint(mat,np.array(lo),np.array(hi)),
             options={'time_limit':time_limit,'mip_rel_gap':0})
    if res.x is None:return None,res
    pos=[]
    for n in range(N):
        p=int(np.argmax(res.x[n*P:(n+1)*P]));pos.append((p//C,p%C))
    return pos,res


def tok(dist,ch): return ch if dist==1 else str(dist)+ch
def grid(C,R,nodes,edges,pos):
    g=[['X']*C for _ in range(R)]; children={n:[] for n in range(len(nodes))}
    for p,ch,kind in edges:children[p].append(ch)
    for n,node in enumerate(nodes):
        r,c=pos[n]
        if node['kind']=='leaf':
            g[r][c]=tok(R-r,'D')
        elif node['kind']=='relay':
            ch=children[n][0];rr,cc=pos[ch]
            if rr==r:g[r][c]=tok(abs(cc-c),'R' if cc>c else 'L')
            else:g[r][c]=tok(abs(rr-r),'D' if rr>r else 'U')
        else:
            ds=[]
            for ch in children[n]:
                rr,cc=pos[ch]
                ds.append('U' if rr<r else 'D' if rr>r else 'L' if cc<c else 'R')
            g[r][c]=''.join(ds)
    return g


def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--tries',type=int,default=30000)
    ap.add_argument('--time',type=float,default=300);ap.add_argument('--out',required=True)
    a=ap.parse_args();d=list(map(int,open(a.input).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C]
    pool=candidate_trees(A,B,a.tries,15000019);print('POOL',len(pool),flush=True)
    for ix,best in enumerate(pool):
        print('TRY',ix,'KEY',best[0],flush=True)
        nodes,edges,roots=flatten(best[2]);pos,res=embed(C,C,nodes,edges,roots,a.time)
        print('RESULT',res.message,flush=True)
        if pos is None and best[0][0] < 64:
            # Spend the remaining cells on hamster relays.  A relay is adjacent
            # to its splitter parent, then jumps along an axis to the subtree.
            base_nodes,base_edges,base_roots=nodes,edges,roots
            erng=random.Random(900000+ix)
            spare=64-len(base_nodes)
            order=list(range(len(base_edges)))
            # Deep/internal edges first; these are the ones most likely to need
            # a geometric jump.  Also sample broadly to avoid one greedy bias.
            for attempt in range(350):
                take=spare if attempt>30 else 1+attempt%spare
                chosen=set(erng.sample(order,take))
                nn=[dict(x) for x in base_nodes];ee=[]
                for q,(p,ch,kind) in enumerate(base_edges):
                    if q in chosen and kind=='adj':
                        z=len(nn);nn.append({'kind':'relay','col':None,'src':nn[p].get('src',-1)})
                        ee.append((p,z,'adj'));ee.append((z,ch,'axis'))
                    else:ee.append((p,ch,kind))
                if len(nn)>64:continue
                pp,rr=embed(C,C,nn,ee,base_roots,min(2.0,a.time))
                if pp is not None:
                    nodes,edges,roots,pos,res=nn,ee,base_roots,pp,rr
                    print('RELAY SUCCESS attempt',attempt,'nodes',len(nn),flush=True);break
        if pos is None:continue
        g=grid(C,C,nodes,edges,pos)
        with open(a.out,'w') as f:
            f.write(str(C)+'\n');f.writelines(' '.join(row)+'\n' for row in g)
        print('SAVED',a.out);return
    raise SystemExit(1)
if __name__=='__main__':main()
