"""Compare exact strategy costs on downloaded intermediate tail cases."""
import os,re,subprocess,sys
import challenge_submission_rating_v4_stable as s

HERE=os.path.dirname(os.path.abspath(__file__))
EXE=os.path.join(HERE,'public1_offline_optimizer.exe')
OUT=os.path.join(HERE,'outputs')

def text(z):
 r,g=z[:2];return str(r)+'\n'+''.join(' '.join(x)+'\n' for x in g)

def exact(inp,grid,tag):
 ip=os.path.join(OUT,'_tail_'+tag+'.in');gp=os.path.join(OUT,'_tail_'+tag+'.grid');op=gp+'.out'
 open(ip,'w').write(inp);open(gp,'w').write(grid if isinstance(grid,str) else text(grid))
 p=subprocess.run([EXE,ip,gp,op,'0','0','1'],text=True,capture_output=True,check=True)
 m=re.search(r'START cost=(\d+) E=(\d+) D=(\d+) L=(\d+)',p.stderr)
 return tuple(map(int,m.groups()))

def main(path):
 d=list(map(int,open(path).read().split()));C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
 inp=' '.join(map(str,d))+'\n';ew=s.whole_error(A,B);es=s.split_error(A,B)
 cand={'whole':(*s.solve_whole(C,T,M,A,B),ew+2),
       'split':(*s.solve_split(C,T,M,A,B),es+(1<<(C+1)))}
 risk,band,score=s.outlier_risk(C,M,B,min(ew+2,es+(1<<(C+1))))
 for name,z in [('thirds',s.solve_thirds(C,T,M,A,B,tries=4)),
                ('maxhalf',s.solve_maxhalf(C,T,M,A,B)),
                ('var3',s.solve_variable23(C,T,M,A,B,max_k=3))]:
  if z:cand[name]=z
 print('case',os.path.basename(path),'C',C,'M',M,'risk',risk,band,score)
 sub=subprocess.run([sys.executable,os.path.join(HERE,'challenge_submission_rating_v4_stable.py')],
                    input=inp,text=True,capture_output=True,check=True)
 print('submission','exact',exact(inp,sub.stdout,'submission_'+str(C)))
 for tries in range(1,9):
  z=s.solve_thirds(C,T,M,A,B,tries=tries)
  if z:print('thirds'+str(tries),'model',z[2]+(1<<(C+4)),
             'exact',exact(inp,z,'thirds'+str(tries)+'_'+str(C)))
 for name,z in cand.items():print(name,'model',z[2],'exact',exact(inp,z,name+'_'+str(C)))

if __name__=='__main__':
 for p in sys.argv[1:]:main(p)
