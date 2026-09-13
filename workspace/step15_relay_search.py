"""Find minimum split-edge relay subdivisions that make compact trees embeddable."""
import itertools, os, sys
sys.path.insert(0,os.path.dirname(__file__))
import milp_exact_tree_builder as M
import step15_shared_embed as S

def subdivide(nodes,edges,chosen):
    nn=[dict(x) for x in nodes];ee=[]
    for q,(p,ch,kind) in enumerate(edges):
        if q in chosen:
            z=len(nn);nn.append({'kind':'relay','col':None,'src':nodes[p].get('src',-1)})
            ee.append((p,z,'adj'));ee.append((z,ch,'axis'))
        else:ee.append((p,ch,kind))
    return nn,ee

def main():
    best=M.search_trees(S.A,S.B,5000,950015)
    for src in (0,3,4):
        nodes,edges,roots=M.flatten([best[2][src]]);nodes[roots[0]]['col']=src
        candidates=[q for q,(p,ch,k) in enumerate(edges) if nodes[ch]['kind']=='split']
        found=None
        for take in range(len(candidates)+1):
            for subset in itertools.combinations(candidates,take):
                nn,ee=subdivide(nodes,edges,set(subset));pos,res=S.embed(nn,ee,roots,1.0)
                if pos is not None:
                    found=(subset,nn,ee,pos);break
            if found:break
        print('SOURCE',src,'base_nodes',len(nodes),'candidate_edges',candidates,
              'FOUND',None if found is None else (found[0],len(found[1])),flush=True)

if __name__=='__main__':main()
