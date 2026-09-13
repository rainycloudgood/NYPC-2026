"""Parallel evolutionary search over bus assignment targets (offline only)."""
import concurrent.futures,os,random,sys
import validate as V
from solution_bus_four import solve

def read(path):
 d=list(map(int,open(path).read().split()));C,T,M=d[:3]
 return C,T,M,d[3:3+C],d[3+C:3+2*C]
def worker(x):
 C,T,M,A,B,plan,seed=x;z=solve(C,T,M,A,plan,seed,False)
 if z is None:return(10**30,None,plan,seed,None)
 R,g,est,got=z;cells={(r+1,c):V.parse_cell(g[r][c])for r in range(R)for c in range(C)}
 bp,last,b,left=V.simulate(C,T,M,A,B,R,cells);L=sum(B)-sum(bp)
 E=sum(abs(bp[i]-B[i])for i in range(C));D=T if L else last-M
 return((1<<(R-C))+max(E,D)+T*L,g,plan,seed,(E,D,b,bp,L,est,R))
def mutate(plan,rng,scale):
 q=list(plan)
 for _ in range(rng.randint(1,4)):
  a,b=rng.sample(range(len(q)),2);v=min(q[a],max(1,int(abs(rng.gauss(0,scale)))))
  q[a]-=v;q[b]+=v
 return q
def main():
 inp,out=sys.argv[1:3];gens=int(sys.argv[3]) if len(sys.argv)>3 else 3
 C,T,M,A,B=read(inp);rng=random.Random(881177)
 known=list(B)
 if os.environ.get('START_PLAN'):known=list(map(int,os.environ['START_PLAN'].split(',')))
 start_seed=int(os.environ.get('START_SEED','0'))
 elite=[(known,start_seed),(list(B),0)];best=None
 jobs_per_gen=int(os.environ.get('JOBS','24'))
 workers=int(os.environ.get('WORKERS','12'))
 for gen in range(gens):
  jobs=[]
  for p,s in elite:jobs.append((C,T,M,A,B,p,s))
  while len(jobs)<jobs_per_gen:
   p,s=rng.choice(elite);base_scale=float(os.environ.get('SCALE','7000'))
   q=mutate(p,rng,base_scale/(gen+1));jobs.append((C,T,M,A,B,q,rng.randrange(1000)))
  with concurrent.futures.ProcessPoolExecutor(max_workers=workers)as ex:res=list(ex.map(worker,jobs))
  res.sort(key=lambda x:x[0]);
  for x in res[:6]:print('gen',gen,'cost',x[0],'seed',x[3],'meta',x[4],'plan',x[2],file=sys.stderr)
  if best is None or res[0][0]<best[0]:best=res[0]
  elite=[(x[2],x[3])for x in res[:6]]
 cost,g,plan,seed,meta=best
 with open(out,'w')as f:
  f.write(str(meta[-1])+'\n');[f.write(' '.join(row)+'\n')for row in g]
 print('BEST',cost,seed,meta,plan,file=sys.stderr)
if __name__=='__main__':main()
