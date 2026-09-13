import itertools,os,random,re,subprocess,sys,time
import intermediate_exact_validation as gen
from dyadic_comb_bound import solve
from solution_parallel_comb import side_matching,build

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe');SUB=os.path.join(HERE,'challenge_submission_rating_v5_balanced.py')
def exact(inp,text,tag):
 ip=os.path.join(OUT,tag+'.in');gp=os.path.join(OUT,tag+'.grid');op=gp+'.out';open(ip,'w').write(inp);open(gp,'w').write(text);p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True);m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr);return tuple(map(int,m.groups()))
rng=random.Random(880061);found=0;attempt=0
while found<12 and attempt<5000:
 attempt+=1;A,B=gen.official_case(6,0,rng);lb=2*sum(max(0,min(A)-b,b-max(A)) for b in B)
 if lb<50000:continue
 M=max(A);inp=f'6 2000000 {M}\n'+' '.join(map(str,A))+'\n'+' '.join(map(str,B))+'\n';p=subprocess.run([sys.executable,SUB],input=inp,text=True,capture_output=True,check=True);cur=exact(inp,p.stdout,f'conv_{found}_cur')
 feasible=[x for x in itertools.combinations(range(6),3) if side_matching(6,x)];chosen=max(feasible,key=lambda x:sum(A[i] for i in x));st=time.perf_counter();sol=solve(A,B,3,7,1.30,1,30000,chosen);z=build(6,A,B,3,7,sol,chosen);text=str(z[0])+'\n'+'\n'.join(' '.join(x) for x in z[1])+'\n';comb=exact(inp,text,f'conv_{found}_comb');print(found,'M',M,'lb',lb,'chosen',chosen,'model',512+sol[1],'current',cur,'comb',comb,'sec',round(time.perf_counter()-st,2),flush=True);found+=1
print('found',found,'attempts',attempt)
