"""Offline exhaustive mixed-half/third search for one C=6 input."""
import argparse,hashlib,itertools,os,re,subprocess
import challenge_submission_rating_v5_balanced as s

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--keep',type=int,default=500);ap.add_argument('--steps',type=int,default=2000);ap.add_argument('--seeds',type=int,default=1);a=ap.parse_args()
d=list(map(int,open(a.input).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];assert C==6
cand={};base=sum((q+1)*x for q,x in enumerate(A+B))
for k in range(1,C):
 for hs in itertools.combinations(range(C),k):
  for ht in itertools.combinations(range(C),k):
   for q in range(a.seeds):
    z=s.v23_assign(A,B,frozenset(hs),frozenset(ht),base+100003*k+1009*q+31*sum(hs)+sum(ht),steps=a.steps)
    p=s.v23_layout(C,z) if z else None
    if not p:continue
    text=str(p[0])+'\n'+'\n'.join(' '.join(x) for x in p[1])+'\n';h=hashlib.sha1(text.encode()).hexdigest()
    if h not in cand or p[2]<cand[h][0]:cand[h]=(p[2],text,k,hs,ht)
print('generated',len(cand),flush=True);items=sorted(cand.values())[:a.keep];best=None
for n,(model,text,k,hs,ht) in enumerate(items):
 gp=os.path.join(OUT,'_c6v23.grid');op=gp+'.out';open(gp,'w').write(text)
 p=subprocess.run([EXE,a.input,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)',p.stderr);z=tuple(map(int,m.groups()))
 if best is None or z<best[0]:
  best=(z,model,k,hs,ht,text);print('best',n,best[:5],flush=True)
with open(os.path.join(OUT,'c6_exhaustive_best.grid'),'w') as f:f.write(best[-1])
print('FINAL',best[:5])
