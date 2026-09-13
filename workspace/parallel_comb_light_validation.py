import glob,os,re,subprocess,time,itertools
import challenge_submission_rating_v5_balanced as base
from dyadic_comb_bound import solve
from solution_parallel_comb import side_matching,build
HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
paths=sorted(glob.glob(os.path.join(OUT,'midval_30492_0_*.in')))+[r'C:\Users\<user>\Downloads\147-6.data.txt']
def exact(ip,z,n):
 gp=os.path.join(OUT,'_light_'+str(n)+'.grid');op=gp+'.out';open(gp,'w').write(str(z[0])+'\n'+'\n'.join(' '.join(x) for x in z[1])+'\n')
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True);m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr);return tuple(map(int,m.groups()))
for n,ip in enumerate(paths):
 d=list(map(int,open(ip).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];feasible=[x for x in itertools.combinations(range(C),3) if side_matching(C,x)];chosen=max(feasible,key=lambda x:sum(A[i] for i in x));st=time.perf_counter();cand=[]
 for depth in (5,6,7,8,9,10):
  for cap in (1.15,1.20,1.25,1.30):
   for seed in (0,1):
    sol=solve(A,B,3,depth,cap,seed,5000,chosen);z=build(C,A,B,3,depth,sol,chosen);cand.append(((1<<(depth+2))+sol[1],depth,cap,sol,z))
 q=min(cand,key=lambda x:x[0]);print(os.path.basename(ip),'sec',round(time.perf_counter()-st,3),'chosen',chosen,'model/depth/cap',q[:3],'exact',exact(ip,q[-1],n),flush=True)
