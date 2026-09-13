"""Fresh compact exact-flow builder using treegen's relay-capable placer."""
import os, random, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import treegen as G

C=8;T=2000;M=999
A=[684,297,330,609,999,198,474,108]
B=[363,437,412,646,602,557,260,422]
FLOW=[
 [[2,193],[0,363],[4,128]], [[5,297]], [[3,330]],
 [[5,152],[7,422],[3,35]], [[3,83],[6,260],[1,437],[2,219]],
 [[3,198]], [[4,474]], [[5,108]],
]

def attempt(R,rng,relay):
    trees=[G.plan_tree(A[i],[x[:] for x in FLOW[i]],rng) for i in range(C)]
    gr=G.Grid(C,R);gr.search_left=120000
    # Hard trees first, then singletons fill remaining corridors.
    order=[4,3,0,1,2,5,6,7]
    if rng.random()<.5: rng.shuffle(order[:3])
    for i in order:
        if not G.place_stream(gr,0,i,trees[i],rng,relay=relay):return None
    return gr.g

def main():
    seconds=float(sys.argv[1]) if len(sys.argv)>1 else 120
    rng=random.Random(81500015);start=time.time();tries=placed=0;best=None
    while time.time()-start<seconds:
        tries+=1
        # Concentrate on R=10; occasionally test R=9 and R=11.
        u=rng.random();R=10 if u<.78 else (9 if u<.9 else 11)
        grid=attempt(R,rng,relay=5)
        if grid is None:continue
        placed+=1;sc=G.evaluate(C,T,M,A,B,R,grid)
        if sc and (best is None or sc<best[0]):
            best=(sc,R,[x[:] for x in grid]);print('BEST',best[0],'R',R,'tries',tries,'placed',placed,flush=True)
            out=os.path.join(G.OUT_DIR,f'output_15_compact_fresh_r{R}_trial.txt')
            with open(out,'w') as f:f.write(str(R)+'\n');f.writelines(' '.join(x)+'\n' for x in grid)
            if sc[0]<16:break
    print('FINAL tries',tries,'placed',placed,'best',None if best is None else best[:2],flush=True)

if __name__=='__main__':main()
