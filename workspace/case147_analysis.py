import os,re,subprocess
import challenge_submission_rating_v5_balanced as s

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
CASES=[('147-6',r'C:\Users\<user>\Downloads\147-6.data.txt'),
       ('147-25',r'C:\Users\<user>\Downloads\147-25.data.txt')]

def exact(ip,z,tag):
 r,g=z[:2];gp=os.path.join(OUT,tag+'.grid');op=gp+'.out'
 with open(gp,'w') as f:
  f.write(str(r)+'\n');f.writelines(' '.join(x)+'\n' for x in g)
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

for name,ip in CASES:
 d=list(map(int,open(ip).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 cand={'whole':s.solve_whole(C,T,M,A,B),'split':s.solve_split(C,T,M,A,B)}
 for tries in (2,6,12,24):
  z=s.solve_thirds(C,T,M,A,B,tries=tries)
  if z:cand['third'+str(tries)]=z
 for k in (3,C-1):
  z=s.solve_variable23(C,T,M,A,B,max_k=k)
  if z:cand['var'+str(k)]=z
 for seed in range(4):
  z=s.solve_maxhalf(C,T,M,A,B,seed=seed,restarts=12,steps=30000)
  if z:cand['half'+str(seed)]=z
 z=s.solve_balanced4_bus(C,T,M,A,B)
 if z:cand['balanced4']=z
 vals=[]
 for key,z in cand.items():
  vals.append((exact(ip,z,name+'_'+key),key,(1<<(z[0]-C))+z[2] if len(z)>2 else None))
 for row in sorted(vals):print(name,row,flush=True)
