import glob,os,re,subprocess
import challenge_submission_rating_v5_balanced as s
HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
paths=sorted(glob.glob(os.path.join(OUT,'midval_30492_0_*.in')))+[r'C:\Users\<user>\Downloads\147-6.data.txt']
def exact(ip,z,tag):
 gp=os.path.join(OUT,tag+'.grid');op=gp+'.out'
 with open(gp,'w') as f:f.write(str(z[0])+'\n');f.writelines(' '.join(x)+'\n' for x in z[1])
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr);return tuple(map(int,m.groups()))
for n,ip in enumerate(paths):
 d=list(map(int,open(ip).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 curp=subprocess.run(['python',os.path.join(HERE,'challenge_submission_rating_v5_balanced.py')],input=open(ip).read(),text=True,capture_output=True,check=True)
 lines=curp.stdout.splitlines();cur=(int(lines[0]),[x.split() for x in lines[1:]])
 z=s.solve_variable23(C,T,M,A,B,max_k=C-1,min_k=4)
 print(M,'current',exact(ip,cur,f'c6low_{n}_cur'),'var',None if z is None else exact(ip,z,f'c6low_{n}_var'),flush=True)
