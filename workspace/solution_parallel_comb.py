"""Three disjoint dyadic comb strips feeding destination buses (C6 research)."""
import argparse,itertools,os,re,subprocess
from dyadic_comb_bound import solve

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
def tok(n,ch):return ch if n==1 else f'{n}{ch}'

def side_matching(C,chosen):
 opts=[]
 for i in chosen:opts.append([j for j in (i-1,i+1) if 0<=j<C])
 for sides in itertools.product(*opts):
  cells=[]
  for i,j in zip(chosen,sides):cells += [i,j]
  if len(set(cells))==2*len(chosen):return dict(zip(chosen,sides))
 return None

def build(C,A,B,k,depth,assignment,chosen=None,offsets=None,phase_chain=False):
 chosen=tuple(sorted(range(C),key=lambda i:-A[i])[:k] if chosen is None else chosen);side=side_matching(C,chosen)
 if side is None:return None
 score,E,mr,rates,got,npieces,dest,pieces=assignment;offsets={} if offsets is None else offsets;bus0=depth+2+max([offsets.get(i,0) for i in chosen] or [0]);R=bus0+C;g=[['X']*C for _ in range(R)]
 for j in range(C):
  r=bus0+j
  for c in range(C):g[r][c]='R' if c<j else ('L' if c>j else tok(R-r,'D'))
 q=0
 for i,a in enumerate(A):
  if i not in side:
   g[0][i]=tok(bus0+dest[q],'D');q+=1;continue
  sc=side[i];sd='R' if sc>i else 'L';start=1+offsets.get(i,0);g[0][i]='D' if phase_chain else tok(start,'D');x=a
  if phase_chain:
   for rr in range(1,start):g[rr][i]='D'
  for level in range(depth):
   r=start+level;g[r][i]=sd+'D';g[r][sc]=tok(bus0+dest[q]-r,'D');q+=1;x//=2
  r=start+depth;g[r][i]=tok(bus0+dest[q]-r,'D');q+=1
 assert q==len(dest)
 return R,g

def exact(ip,z,tag):
 gp=os.path.join(OUT,tag+'.grid');op=gp+'.out';open(gp,'w').write(str(z[0])+'\n'+'\n'.join(' '.join(x) for x in z[1])+'\n')
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)',p.stderr);return tuple(map(int,m.groups())),gp

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--seeds',type=int,default=6);ap.add_argument('--steps',type=int,default=60000);a=ap.parse_args()
 d=list(map(int,open(a.input).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C];best=None;n=0
 feasible=[x for x in itertools.combinations(range(C),3) if side_matching(C,x)]
 chosen=max(feasible,key=lambda x:sum(A[i] for i in x));print('chosen strips',chosen,side_matching(C,chosen),flush=True)
 for depth in (5,6,7,8,9,10):
  for cap in (1.10,1.15,1.20,1.25,1.30):
   for seed in range(a.seeds):
    sol=solve(A,B,3,depth,cap,seed,a.steps,chosen);z=build(C,A,B,3,depth,sol,chosen)
    if z is None:continue
    val,gp=exact(a.input,z,f'_pcomb_{n}');n+=1
    if best is None or val<best[0]:
     best=(val,depth,cap,sol[1],sol[2],sol[3],gp);print('best',best,flush=True)
 if best:
  import shutil;dst=os.path.join(OUT,'parallel_comb_best.grid');shutil.copy(best[-1],dst);print('SAVED',dst,'FINAL',best[:-1])

if __name__=='__main__':main()
