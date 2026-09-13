"""Fresh R=8 exact-flow design with shared destination leaves."""
import os
import sys
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

sys.path.insert(0, os.path.dirname(__file__))
import milp_exact_tree_builder as M
import optimizer as O

C = 8
R = int(os.environ.get("STEP15_R", "8"))
A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]


def merge_destination_leaves(nodes, edges, roots):
    parents = {i: [] for i in range(len(nodes))}
    for p, ch, kind in edges: parents[ch].append((p, kind))
    keep = [i for i, n in enumerate(nodes) if n["kind"] != "leaf"]
    remap = {}
    newnodes = []
    for old in keep:
        remap[old] = len(newnodes); newnodes.append(dict(nodes[old]))

    # Per destination, greedily merge leaves whose parents are distinct.
    # A shared cell has at most four adjacent parents.
    groups = []
    for dest in range(C):
        leaves = [i for i, n in enumerate(nodes) if n["kind"] == "leaf" and n["col"] == dest]
        local = []
        for leaf in leaves:
            ps = {p for p, _ in parents[leaf]}
            placed = False
            for group in local:
                if len(group["leaves"]) < 2 and len(group["parents"] | ps) <= 2 and not (group["parents"] & ps):
                    group["leaves"].append(leaf); group["parents"] |= ps; placed = True; break
            if not placed: local.append({"leaves": [leaf], "parents": set(ps), "dest": dest})
        groups += local
    for group in groups:
        nid = len(newnodes);newnodes.append({"kind": "leaf", "col": group["dest"], "src": -1})
        for leaf in group["leaves"]: remap[leaf] = nid
    newedges = []
    seen = set()
    for p, ch, kind in edges:
        z = (remap[p], remap[ch], kind)
        if z not in seen: seen.add(z);newedges.append(z)
    return newnodes, newedges, [remap[x] for x in roots], groups


def embed(nodes, edges, roots, limit=180):
    rows = R - 1; P = rows * C; N = len(nodes); V = N * P
    def vid(n, r, c): return n * P + (r - 1) * C + c
    lb = np.zeros(V);ub = np.ones(V);obj = np.zeros(V)
    root_set = set(roots)
    for n, node in enumerate(nodes):
        fixed = node.get("col")
        for r in range(1, R):
            for c in range(C):
                v = vid(n, r, c);obj[v] = r * 1e-4
                if fixed is not None and c != fixed: ub[v] = 0
                # Roots prefer the first three internal rows but may use all.
                if n in root_set: obj[v] += r * 1e-3
    rr=[];cc=[];vv=[];lo=[];hi=[];row=0
    for n in range(N):
        for p in range(P):rr.append(row);cc.append(n*P+p);vv.append(1)
        lo.append(1);hi.append(1);row+=1
    for p in range(P):
        for n in range(N):rr.append(row);cc.append(n*P+p);vv.append(1)
        lo.append(-np.inf);hi.append(1);row+=1
    for parent, child, kind in edges:
        for r in range(1, R):
            for c in range(C):
                rr.append(row);cc.append(vid(child,r,c));vv.append(1)
                if kind == "adj":
                    for pr,pc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                        if 1<=pr<R and 0<=pc<C:rr.append(row);cc.append(vid(parent,pr,pc));vv.append(-1)
                elif kind == "row":
                    pc=nodes[parent]["col"]
                    rr.append(row);cc.append(vid(parent,r,pc));vv.append(-1)
                else:  # axis-aligned hamster jump
                    for pc in range(C):rr.append(row);cc.append(vid(parent,r,pc));vv.append(-1)
                    for pr in range(1,R):
                        if pr!=r:rr.append(row);cc.append(vid(parent,pr,c));vv.append(-1)
                lo.append(-np.inf);hi.append(0);row+=1
    mat=coo_matrix((vv,(rr,cc)),shape=(row,V)).tocsr()
    if os.environ.get("STEP15_QUIET") != "1":
        print("EMBED nodes",N,"vars",V,"rows",row,"nnz",mat.nnz,flush=True)
    res=milp(obj,integrality=np.ones(V),bounds=Bounds(lb,ub),
             constraints=LinearConstraint(mat,np.array(lo),np.array(hi)),
             options={"time_limit":limit,"mip_rel_gap":0})
    if res.x is None:return None,res
    pos=[]
    for n in range(N):
        p=int(np.argmax(res.x[n*P:(n+1)*P]));pos.append((1+p//C,p%C))
    return pos,res


def tok(dist, d): return d if dist == 1 else f"{dist}{d}"
def direction(a,b):
    dr,dc=b[0]-a[0],b[1]-a[1]
    return {(1,0):"D",(-1,0):"U",(0,1):"R",(0,-1):"L"}[(dr,dc)]


def make_grid(nodes, edges, roots, pos):
    g=[["X"]*C for _ in range(R)];children={i:[] for i in range(len(nodes))}
    for p,ch,kind in edges:children[p].append((ch,kind))
    for src,root in enumerate(roots):
        rr,cc=pos[root];assert cc==src;g[0][src]=tok(rr,"D")
    for n,node in enumerate(nodes):
        r,c=pos[n]
        if node["kind"]=="leaf":g[r][c]=tok(R-r,"D")
        elif node["kind"]=="relay":
            ch,_=children[n][0];_,dc=pos[ch];g[r][c]=tok(abs(dc-c),"R" if dc>c else "L")
        else:
            ds=[direction(pos[n],pos[ch]) for ch,_ in children[n]]
            if len(ds)!=len(set(ds)):raise ValueError((n,ds))
            g[r][c]="".join(ds)
    return g


def main():
    best=M.search_trees(A,B,5000,950015)
    print("TRANSPORT",best[0],best[1],flush=True)
    nodes,edges,roots=M.flatten(best[2])
    if os.environ.get("STEP15_MERGE", "1") == "1":
        nodes,edges,roots,groups=merge_destination_leaves(nodes,edges,roots)
    else:
        groups=[]
    print("MERGED nodes",len(nodes),"groups",[(x["dest"],len(x["leaves"])) for x in groups],flush=True)
    pos,res=embed(nodes,edges,roots)
    print("MILP",res.message,flush=True)
    if pos is None:return 1
    grid=make_grid(nodes,edges,roots,pos)
    body=sum(grid,[]);sc=O.evaluate(C,2000,999,A,B,R,body)
    out=os.path.join(O.OUT_DIR,f"output_15_shared_fresh_r{R}_trial.txt")
    with open(out,"w") as f:
        f.write(str(R)+"\n");f.writelines(" ".join(row)+"\n" for row in grid)
    print("SAVED",out,"score",sc,flush=True)


if __name__=="__main__":raise SystemExit(main() or 0)
