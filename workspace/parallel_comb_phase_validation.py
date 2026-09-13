import argparse,glob,itertools,os,re,subprocess
from dyadic_comb_bound import solve
from solution_parallel_comb import side_matching,build
HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
ap=argparse.ArgumentParser();ap.add_argument('--only147',action='store_true');args=ap.parse_args();paths=([r'C:\Users\<user>\Downloads\147-6.data.txt'] if args.only147 else sorted(glob.glob(os.path.join(OUT,'midval_30492_0_*.in')))+[r'C:\Users\<user>\Downloads\147-6.data.txt'])
def exact(ip,z,n):
 gp=os.path.join(OUT,'_phase.grid');op=gp+'.out';open(gp,'w').write(str(z[0])+'\n'+'\n'.join(' '.join(x) for x in z[1])+'\n');p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True);m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr);return tuple(map(int,m.groups()))
for n,ip in enumerate(paths):
 d=list(map(int,open(ip).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];fs=[x for x in itertools.combinations(range(C),3) if side_matching(C,x)];chosen=max(fs,key=lambda x:sum(A[i] for i in x));sol=solve(A,B,3,7,1.30,1,30000,chosen);best=None
 for vals in itertools.product(range(4),repeat=3):
  if min(vals)!=0:continue
  off=dict(zip(chosen,vals));z=build(C,A,B,3,7,sol,chosen,off,True);v=exact(ip,z,n)
  if best is None or v<best[0]:best=(v,vals,z[0])
 print(os.path.basename(ip),'chosen',chosen,'staticE',sol[1],'BEST',best,flush=True)
