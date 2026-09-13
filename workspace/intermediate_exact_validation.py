"""Exact end-to-end validation on the official intermediate distribution."""
import argparse,os,random,re,statistics,subprocess,sys,time
import challenge_submission_rating_v4_stable as s

HERE=os.path.dirname(os.path.abspath(__file__))
SUB=os.path.join(HERE,'challenge_submission_rating_v4_stable.py')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
OUT=os.path.join(HERE,'outputs');TOTAL=1_000_000

def composition(c,rng):
 cuts=sorted(rng.sample(range(1,TOTAL+c),c-1));x=[0]+cuts+[TOTAL+c]
 return [x[i+1]-x[i]-1 for i in range(c)]

def official_case(c,band,rng):
 lo,hi=s.INTERMEDIATE_M_BINS[c][band]
 while True:
  x,y=composition(c,rng),composition(c,rng);a,b=(x,y) if max(x)>=max(y) else (y,x)
  if lo<=max(a)<=hi:return a,b

def exact(inp,grid,tag):
 ip=os.path.join(OUT,tag+'.in');gp=os.path.join(OUT,tag+'.grid');op=gp+'.out'
 open(ip,'w').write(inp);open(gp,'w').write(grid)
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--c',type=int,required=True)
 ap.add_argument('-n',type=int,default=5);ap.add_argument('--seed',type=int,default=20261400)
 ap.add_argument('--sub',default='challenge_submission_rating_v4_stable.py')
 args=ap.parse_args();rng=random.Random(args.seed+args.c*1009);run=f'midval_{os.getpid()}'
 sub=os.path.join(HERE,args.sub)
 total_l=0;all_cost=[];all_ms=[]
 for band in range(5):
  rows=[]
  for q in range(args.n):
   a,b=official_case(args.c,band,rng);m=max(a)
   inp=f'{args.c} 2000000 {m}\n'+' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n'
   st=time.perf_counter();p=subprocess.run([sys.executable,sub],input=inp,text=True,
                                            capture_output=True,check=True)
   ms=(time.perf_counter()-st)*1000
   z=exact(inp,p.stdout,f'{run}_{band}_{q}');rows.append((z,ms,m));all_cost.append(z[0]);all_ms.append(ms)
  costs=sorted(x[0][0] for x in rows);ls=sum(x[0][3]>0 for x in rows);total_l+=ls
  print('C',args.c,'band',band,'costs',costs,'median',int(statistics.median(costs)),
        'max',max(costs),'L',ls,'runtime_max_ms',round(max(x[1] for x in rows),1))
 print('SUMMARY C',args.c,'cases',5*args.n,'L',total_l,'median',int(statistics.median(all_cost)),
       'max',max(all_cost),'runtime_max_ms',round(max(all_ms),1),'runtime_med_ms',round(statistics.median(all_ms),1))

if __name__=='__main__':main()
