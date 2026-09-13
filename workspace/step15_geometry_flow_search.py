"""Search exact transports by a geometry-aware tree/column-distance score."""
import heapq, os, random, sys
sys.path.insert(0,os.path.dirname(__file__))
import milp_exact_tree_builder as M
import treegen as G

A=[684,297,330,609,999,198,474,108]
B=[363,437,412,646,602,557,260,422]
C=8

def main(tries=30000):
    rng=random.Random(190715);best=[]
    for it in range(tries):
        pi=list(range(C));pj=list(range(C));rng.shuffle(pi);rng.shuffle(pj)
        flow=M.perm_transport(A,B,pi,pj)
        trng=random.Random(7000003+it*97)
        trees=[G.plan_tree(A[i],[x[:] for x in flow[i]],trng) for i in range(C)]
        nodes=sum(M.tstats(t)[0] for t in trees)+sum(t[0]=='leaf' and t[1]!=i for i,t in enumerate(trees))
        dist=sum(abs(i-j) for i,row in enumerate(flow) for j,x in row if x)
        far=sum(max(0,abs(i-j)-1) for i,row in enumerate(flow) for j,x in row if x)
        key=(nodes+2*far,nodes,far,dist,max(M.tstats(t)[1] for t in trees))
        item=(tuple(-x for x in key),it,key,flow,trees)
        if len(best)<30:heapq.heappush(best,item)
        elif item[0]>best[0][0]:heapq.heapreplace(best,item)
    out=sorted(best,key=lambda x:x[2])
    for rank,(_,it,key,flow,trees) in enumerate(out[:15]):
        print(rank,'it',it,'key',key,'flow',flow,'stats',[M.tstats(t) for t in trees],flush=True)

if __name__=='__main__':main(int(sys.argv[1]) if len(sys.argv)>1 else 30000)
