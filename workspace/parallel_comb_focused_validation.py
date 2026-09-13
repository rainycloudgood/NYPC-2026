import glob,itertools,os,re,subprocess,time
from dyadic_comb_bound import solve
from solution_parallel_comb import side_matching,build
HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
paths=sorted(glob.glob(os.path.join(OUT,'midval_30492_0_*.in')))+[r'C:\Users\<user>\Downloads\147-6.data.txt']
for n,ip in enumerate(paths):
 d=list(map(int,open(ip).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];feasible=[x for x in itertools.combinations(range(C),3) if side_matching(C,x)];chosen=max(feasible,key=lambda x:sum(A[i] for i in x));st=time.perf_counter();sol=solve(A,B,3,7,1.30,1,30000,chosen);z=build(C,A,B,3,7,sol,chosen);gp=os.path.join(OUT,f'_focus_{n}.grid');op=gp+'.out';open(gp,'w').write(str(z[0])+'\n'+'\n'.join(' '.join(x) for x in z[1])+'\n');p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True);m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr);print(os.path.basename(ip),'sec',round(time.perf_counter()-st,3),'model',(1<<9)+sol[1],'staticE',sol[1],'rates',sol[3],'exact',m.groups(),flush=True)
