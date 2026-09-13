"""Data-1-only shallow piece-bank assignment + destination-bus packer."""
import argparse, math, os, random, subprocess, tempfile

HERE=os.path.dirname(os.path.abspath(__file__))
INP=os.path.join(HERE,'public_1_input.txt')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
OUT=os.path.join(HERE,'outputs')
A=[71780,40734,34823,21664,386738,78532,252360,113369]
B=[43797,25501,136827,63769,243154,274570,17689,194693]
C=8

def splitn(a,k):
 q,r=divmod(a,k);return [q+(i<r) for i in range(k)]

def make_template(a,name,src,next_id):
 leaves=[]
 def leaf(x):
  q=next_id[0];next_id[0]+=1;leaves.append((q,x,x/a,src));return ('leaf',q)
 if name=='whole': root=leaf(a)
 elif name=='half': root=('split',[leaf(x) for x in splitn(a,2)])
 elif name=='third': root=('split',[leaf(x) for x in splitn(a,3)])
 elif name=='quarter':
  root=('split',[('split',[leaf(y) for y in splitn(x,2)]) for x in splitn(a,2)])
 elif name=='w4':
  t=splitn(a,3);root=('split',[leaf(t[0]),leaf(t[1]),('split',[leaf(y) for y in splitn(t[2],2)])])
 elif name=='w5':
  t=splitn(a,3);root=('split',[leaf(t[0])]+[('split',[leaf(y) for y in splitn(x,2)]) for x in t[1:]])
 elif name=='sixth':
  root=('split',[('split',[leaf(y) for y in splitn(x,2)]) for x in splitn(a,3)])
 else:raise ValueError(name)
 return root,leaves

def bank(combo):
 next_id=[0];trees=[];pieces=[]
 for i,(a,name) in enumerate(zip(A,combo)):
  t,p=make_template(a,name,i,next_id);trees.append(t);pieces+=p
 return trees,pieces

def assignment(combo,cap,seed,steps=70000):
 trees,pieces=bank(combo);rng=random.Random(seed);m=len(pieces)
 order=sorted(range(m),key=lambda q:-pieces[q][1]);dest=[0]*m;got=[0]*C;rate=[0.0]*C
 for q in order:
  x,rr=pieces[q][1],pieces[q][2]
  vals=[]
  for j in range(C):
   pen=2_000_000*max(0,rate[j]+rr-cap)**2
   delta=abs(got[j]+x-B[j])-abs(got[j]-B[j]);vals.append((pen+delta+rng.random(),j))
  _,j=min(vals);dest[q]=j;got[j]+=x;rate[j]+=rr
 def local(j):return abs(got[j]-B[j])+2_000_000*max(0,rate[j]-cap)**2
 temp=25000.0
 for it in range(steps):
  if rng.random()<.7:
   q=rng.randrange(m);a=dest[q];b=rng.randrange(C)
   if a==b:continue
   x,rr=pieces[q][1],pieces[q][2];old=local(a)+local(b)
   got[a]-=x;got[b]+=x;rate[a]-=rr;rate[b]+=rr;new=local(a)+local(b)
   if new<=old or rng.random()<math.exp((old-new)/max(1,temp)):dest[q]=b
   else:got[a]+=x;got[b]-=x;rate[a]+=rr;rate[b]-=rr
  else:
   xq,yq=rng.sample(range(m),2);a,b=dest[xq],dest[yq]
   if a==b:continue
   x,rx=pieces[xq][1],pieces[xq][2];y,ry=pieces[yq][1],pieces[yq][2];old=local(a)+local(b)
   got[a]+=y-x;got[b]+=x-y;rate[a]+=ry-rx;rate[b]+=rx-ry;new=local(a)+local(b)
   if new<=old or rng.random()<math.exp((old-new)/max(1,temp)):dest[xq],dest[yq]=b,a
   else:got[a]+=x-y;got[b]+=y-x;rate[a]+=rx-ry;rate[b]+=ry-rx
  temp*=.99988
 E=sum(abs(got[j]-B[j]) for j in range(C));mr=max(rate)
 return (E+2_000_000*sum(max(0,r-cap)**2 for r in rate),E,mr,dest,got,rate,trees,pieces,combo,cap)

def token(d,ch):return ch if d==1 else f'{d}{ch}'
DELTA={'D':(1,0),'L':(0,-1),'R':(0,1)}

def build_bus(g,bus0,R):
 for j in range(C):
  r=bus0+j
  for c in range(C):
   if c==j:g[r][c]=token(R-r,'D')
   elif c<j:g[r][c]='R'
   else:g[r][c]='L'

def try_pack(sol,R,seed,attempts):
 dest,trees=sol[3],sol[6];bus0=R-C;rng=random.Random(seed)
 complexities=[]
 def nodes(t):return 1 if t[0]=='leaf' else 1+sum(nodes(x) for x in t[1])
 for i,t in enumerate(trees):complexities.append((nodes(t),i))
 for attempt in range(attempts):
  g=[['X']*C for _ in range(R)];build_bus(g,bus0,R)
  for c in range(C):g[0][c]='RES'
  order=[i for _,i in sorted(complexities,reverse=True)];rng.shuffle(order[:0])
  # Vary equal-complexity ordering without losing hardest-first bias.
  if attempt%3:order=sorted(range(C),key=lambda i:(-nodes(trees[i]),rng.random()))
  def free(r,c,owner=None):
   return 0<=r<bus0 and 0<=c<C and (g[r][c]=='X' or (r==0 and c==owner and g[r][c]=='RES'))
  def place(t,r,c,owner,depth=0):
   if depth>8 or not free(r,c,owner):return False
   snap=[row[:] for row in g]
   if t[0]=='leaf':
    j=dest[t[1]];d=bus0+j-r
    if d<2:return False
    g[r][c]=token(d,'D');return True
   children=t[1];k=len(children);dirsets=[]
   if k==2:
    # A splitter stream must keep a downward exit; L/R alone can create
    # a same-row cycle and is not used by the proven tree generator.
    for ds in (('D','L'),('D','R')):
     if all(free(r+DELTA[d][0],c+DELTA[d][1],owner) for d in ds):dirsets.append(ds)
   elif k==3:
    ds=('D','L','R')
    if all(free(r+DELTA[d][0],c+DELTA[d][1],owner) for d in ds):dirsets.append(ds)
   rng.shuffle(dirsets)
   import itertools
   for ds in dirsets:
    ps=list(itertools.permutations(ds));rng.shuffle(ps)
    for tok in ps:
     g[:]=[row[:] for row in snap];g[r][c]=''.join(tok);ok=True
     for ch,d in zip(children,tok):
      rr,cc=r+DELTA[d][0],c+DELTA[d][1]
      if not place(ch,rr,cc,owner,depth+1):ok=False;break
     if ok:return True
   g[:]=[row[:] for row in snap];return False
  ok=True
  for i in order:
   placed=False;rows=list(range(0,max(1,bus0-3)));rng.shuffle(rows)
   # Moving only vertically makes every 3-way tree rooted at source 0/7
   # impossible.  Permit a vertical relay followed by a horizontal relay,
   # so the actual tree root can start in an interior column.
   starts=[(rr,cc) for rr in rows for cc in range(C)]
   rng.shuffle(starts)
   starts.sort(key=lambda z:(z[1]!=i, abs(z[1]-i), z[0]))
   for rr,cc in starts:
    snap=[row[:] for row in g]
    if rr==0:
     if cc!=i:continue
     g[0][i]='X'
    elif cc==i:
     g[0][i]=token(rr,'D')
    else:
     # source -> (rr, source-column) -> (rr, root-column)
     if not free(rr,i,i) or not free(rr,cc,i):continue
     g[0][i]=token(rr,'D')
     g[rr][i]=token(abs(cc-i),'R' if cc>i else 'L')
    if place(trees[i],rr,cc,i):placed=True;break
    g[:]=snap
   if not placed:ok=False;break
  if ok and all(g[0][c]!='RES' for c in range(C)):return g
 return None

def score_grid(R,g,tag):
 gp=os.path.join(OUT,f'_bank_{tag}.txt');op=gp+'.out'
 with open(gp,'w') as f:
  f.write(str(R)+'\n');f.writelines(' '.join(row)+'\n' for row in g)
 p=subprocess.run([EXE,INP,gp,op,'0','0','1'],capture_output=True,text=True,timeout=30)
 line=next((x for x in p.stderr.splitlines() if x.startswith('START ')),'');vals={}
 for x in line.replace(',',' ').split():
  if '=' in x:
   k,v=x.split('=',1)
   try:vals[k]=int(v)
   except ValueError:pass
 return vals,gp

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=18);ap.add_argument('--attempts',type=int,default=2500);args=ap.parse_args()
 configs=[
  (1.10,['w5','whole','third','whole','third','quarter','w5','sixth']),
  (1.20,['quarter','w5','half','sixth','sixth','w4','half','w5']),
  (1.30,['sixth','w4','sixth','quarter','w5','half','half','sixth']),
  (1.20,['w4']*8),(1.20,['w5']*8),
 ]
 sols=[]
 for ci,(cap,combo) in enumerate(configs):
  for s in range(args.seeds):sols.append(assignment(combo,cap,90000+ci*1000+s))
 sols.sort(key=lambda x:(x[0],x[1]));print('assignments',len(sols),'best',[(x[1],round(x[2],3),x[8]) for x in sols[:8]])
 best=None;built=0
 for si,sol in enumerate(sols[:30]):
  for R in (19,20,21,22):
   g=try_pack(sol,R,700000+si*31+R,args.attempts)
   if g is None:continue
   built+=1;vals,path=score_grid(R,g,f'{si}_{R}')
   print('built',si,'R',R,'staticE',sol[1],'rate',round(sol[2],3),'actual',vals)
   if vals.get('L',1)==0 and (best is None or vals.get('cost',10**30)<best[0]):best=(vals['cost'],path,vals,sol,R)
 print('BUILT',built,'BEST',None if best is None else best[:3])
 if best:
  dst=os.path.join(OUT,'public1_shallow_best.txt')
  import shutil;shutil.copy(best[1],dst);print('saved',dst)

if __name__=='__main__':main()
