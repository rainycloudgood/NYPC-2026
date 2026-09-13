"""Analyse the latest 150-case v5 run and alternative rate-safe patterns."""
import glob, os, re, subprocess
from balanced_weighted4_planner import assign, assign5

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe');PIDS={'22032','28940','29892','30492','4848','5028'}

def score(ip,gp):
 p=subprocess.run([EXE,ip,gp,gp+'.scan','0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

tails=[]
for ip in glob.glob(os.path.join(OUT,'midval_*.in')):
 tag=os.path.basename(ip)[:-3];parts=tag.split('_')
 if len(parts)<4 or parts[1] not in PIDS:continue
 gp=os.path.join(OUT,tag+'.grid');z=score(ip,gp)
 if z[0]<=100000:continue
 d=list(map(int,open(ip).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 q4=min(assign(A,B,s,4,30000)[0] for s in range(3))
 q5=min(assign5(A,B,s,4,30000)[0] for s in range(3))
 lo=sum(max(0,min(A)-b,b-max(A)) for b in B)
 tails.append((C,M,z[0],q4,q5,lo,tag))
for row in sorted(tails):print(row)
print('count',len(tails),'weighted5_under',sum(x[4]+2048<100000 for x in tails))
