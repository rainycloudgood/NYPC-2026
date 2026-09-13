"""Exact benchmark for one official C/M rating band."""
import argparse,os,random,re,subprocess,sys
import challenge_submission_rating_v4_stable as s

HERE=os.path.dirname(os.path.abspath(__file__))
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
SUB=os.path.join(HERE,'challenge_submission_rating_v4_stable.py')
OUT=os.path.join(HERE,'outputs');TOTAL=1_000_000

def composition(c,rng):
 cuts=sorted(rng.sample(range(1,TOTAL+c),c-1));x=[0]+cuts+[TOTAL+c]
 return [x[i+1]-x[i]-1 for i in range(c)]

def official_case(c,band,rng):
 lo,hi=s.INTERMEDIATE_M_BINS[c][band]
 while True:
  x,y=composition(c,rng),composition(c,rng);a,b=(x,y) if max(x)>=max(y) else (y,x)
  if lo<=max(a)<=hi:return a,b

def grid_text(z):
 r,g=z[:2];return str(r)+'\n'+''.join(' '.join(row)+'\n' for row in g)

def exact(inp,out,tag):
 ip=os.path.join(OUT,tag+'.in');gp=os.path.join(OUT,tag+'.grid');op=gp+'.out'
 open(ip,'w').write(inp);open(gp,'w').write(out)
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--c',type=int,required=True)
 ap.add_argument('--band',type=int,required=True);ap.add_argument('-n',type=int,default=12)
 ap.add_argument('--seed',type=int,default=20261101);args=ap.parse_args();rng=random.Random(args.seed)
 rows=[];run=f'bandtmp_{os.getpid()}'
 for q in range(args.n):
  a,b=official_case(args.c,args.band,rng);m=max(a)
  inp=f'{args.c} 2000000 {m}\n'+ ' '.join(map(str,a))+'\n'+' '.join(map(str,b))+'\n'
  p=subprocess.run([sys.executable,SUB],input=inp,text=True,capture_output=True,check=True)
  base=exact(inp,p.stdout,f'{run}_{q}_base')
  t6=s.solve_thirds(args.c,2_000_000,m,a,b,tries=6)
  tz=(exact(inp,grid_text(t6),f'{run}_{q}_t6'),(1<<(args.c+4))+t6[2]) if t6 else None
  vf=s.solve_variable23(args.c,2_000_000,m,a,b,max_k=args.c-1)
  vz=(exact(inp,grid_text(vf),f'{run}_{q}_vf'),(1<<(args.c+4))+vf[2]) if vf else None
  safe=min(2+max(s.whole_error(a,b),2),(1<<(args.c+1))+max(s.split_error(a,b),4))
  rows.append((base[0],tz[0][0] if tz else 10**30,vz[0][0] if vz else 10**30,
               tz[1] if tz else 10**30,vz[1] if vz else 10**30,safe))
  print(q,'M',m,'base',base,'safe',safe,'t6',tz,'vfull',vz)
 print('base',[x[0] for x in rows]);print('t6',[x[1] for x in rows]);print('vfull',[x[2] for x in rows])
 print('t6wins',sum(x[1]<x[0] for x in rows),'vwins',sum(x[2]<x[0] for x in rows),'/',len(rows))

if __name__=='__main__':main()
