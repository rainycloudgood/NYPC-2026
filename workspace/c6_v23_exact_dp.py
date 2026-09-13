"""Exact piece-to-target DP for selected C6 half/third configurations."""
import functools,itertools,os,re,subprocess
import challenge_submission_rating_v5_balanced as s

IP=r'C:\Users\<user>\Downloads\147-6.data.txt';HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs');EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
d=list(map(int,open(IP).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
CONFIGS=[((0,2),(1,4)),((1,4),(2,4)),((4,5),(1,4)),((1,2,4,5),(2,3,4,5)),((0,1,2),(2,4,5))]

def exact_assign(hs,ht):
 pieces=[]
 for i,a in enumerate(A):pieces+=s.split(a,2 if i in hs else 3,i)
 caps=[2 if j in ht else 3 for j in range(C)];n=len(pieces);full=(1<<n)-1
 # Hardest/largest targets first improves pruning but retain target labels.
 order=sorted(range(C),key=lambda j:(caps[j],-B[j]));choice={}
 @functools.lru_cache(None)
 def dp(q,mask):
  if q==C:return (0,()) if mask==full else (10**30,())
  j=order[q];rem=[i for i in range(n) if not(mask>>i&1)];best=(10**30,())
  for ids in itertools.combinations(rem,caps[j]):
   nm=mask
   for i in ids:nm|=1<<i
   tail,_=dp(q+1,nm);v=abs(sum(pieces[i][0] for i in ids)-B[j])+tail
   if v<best[0]:best=(v,ids)
  return best
 target=[-1]*n;mask=0
 for q in range(C):
  v,ids=dp(q,mask);j=order[q]
  for i in ids:target[i]=j;mask|=1<<i
 return dp(0,0)[0],pieces,target

def score(z,tag):
 gp=os.path.join(OUT,tag+'.grid');op=gp+'.out';open(gp,'w').write(str(z[0])+'\n'+'\n'.join(' '.join(x) for x in z[1])+'\n')
 p=subprocess.run([EXE,IP,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+) bounce=(\d+)',p.stderr);return tuple(map(int,m.groups()))

for q,(hs,ht) in enumerate(CONFIGS):
 z=exact_assign(frozenset(hs),frozenset(ht));g=s.v23_layout(C,z);print(hs,ht,'model',z[0],'exact',None if not g else score(g,'c6dp_'+str(q)),flush=True)
