"""Oracle coverage analysis for >100K official-distribution tail cases."""
import glob,os,re,subprocess,sys
import challenge_submission_rating_v4_stable as s

HERE=os.path.dirname(os.path.abspath(__file__));OUT=os.path.join(HERE,'outputs')
EXE=os.path.join(HERE,'public1_offline_optimizer.exe');SUB=os.path.join(HERE,'challenge_submission_rating_v4_stable.py')

def grid_text(z):
 r,g=z[:2];return str(r)+'\n'+''.join(' '.join(x)+'\n' for x in g)

def exact(inp,grid,tag):
 ip=os.path.join(OUT,'portfolio_'+tag+'.in');gp=os.path.join(OUT,'portfolio_'+tag+'.grid');op=gp+'.out'
 open(ip,'w').write(inp);open(gp,'w').write(grid)
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

def main():
 tails=[];covered=0
 for path in sorted(glob.glob(os.path.join(OUT,'midval_*.in'))):
  inp=open(path).read();d=list(map(int,inp.split()));c,t,m=d[:3];a=d[3:3+c];b=d[3+c:3+2*c]
  tag=os.path.basename(path).replace('.in','');p=subprocess.run([sys.executable,SUB],input=inp,text=True,capture_output=True,check=True)
  cur=exact(inp,p.stdout,tag+'_cur')
  if cur[0]<=100000:continue
  cand={}
  ew=s.whole_error(a,b);es=s.split_error(a,b)
  cand['whole']=((*s.solve_whole(c,t,m,a,b),),ew+2)
  cand['split']=((*s.solve_split(c,t,m,a,b),),(1<<(c+1))+es)
  for name,z in [('third6',s.solve_thirds(c,t,m,a,b,tries=6)),
                 ('var3',s.solve_variable23(c,t,m,a,b,max_k=3)),
                 ('varfull',s.solve_variable23(c,t,m,a,b,max_k=c-1))]:
   if z:cand[name]=(z,(1<<(z[0]-c))+z[2])
  vals={}
  for name,(z,model) in cand.items():
   zz=z[0] if len(z)==1 else z
   vals[name]=(exact(inp,grid_text(zz),tag+'_'+name),model)
  bestn,(bestz,bestm)=min(vals.items(),key=lambda kv:kv[1][0][0])
  covered+=bestz[0]<=100000;tails.append((tag,c,m,cur[0],bestn,bestz[0]))
  print(tag,'C',c,'M',m,'current',cur,'BEST',bestn,bestz,'model',bestm,
        'all',{k:v[0][0] for k,v in vals.items()},flush=True)
 print('SUMMARY tails',len(tails),'covered_under_100k',covered,'uncovered',len(tails)-covered)
 print('UNRESOLVED',[x for x in tails if x[-1]>100000])

if __name__=='__main__':main()
