"""Offline simulator-feedback correction for public weighted-four layouts."""
import os,sys
import validate as V
from solution_weighted_four import solve as solve_weighted
from solution_bus_four import solve as solve_bus

HERE=os.path.dirname(os.path.abspath(__file__))

def read(path):
 d=list(map(int,open(path).read().split()));C,T,M=d[:3]
 return C,T,M,d[3:3+C],d[3+C:3+2*C]

def evaluate(C,T,M,A,B,R,g):
 cells={(r+1,c):V.parse_cell(g[r][c]) for r in range(R) for c in range(C)}
 bp,last,bounce,left=V.simulate(C,T,M,A,B,R,cells)
 L=sum(B)-sum(bp);E=sum(abs(bp[i]-B[i]) for i in range(C));D=T if L else last-M
 return (1<<(R-C))+max(E,D)+T*L,E,D,bounce,bp,L

def normalize(x,total):
 y=[max(0,int(round(v))) for v in x];delta=total-sum(y)
 order=sorted(range(len(y)),key=lambda i:y[i],reverse=True)
 q=0
 while delta:
  i=order[q%len(y)];step=1 if delta>0 else-1
  if y[i]+step>=0:y[i]+=step;delta-=step
  q+=1
 return y

def main():
 inp=sys.argv[1];out=sys.argv[2];rounds=int(sys.argv[3]) if len(sys.argv)>3 else 10
 mode=sys.argv[4] if len(sys.argv)>4 else 'weighted'
 C,T,M,A,B=read(inp);plan=list(B);best=None
 if os.environ.get('START_PLAN'):
  plan=list(map(int,os.environ['START_PLAN'].split(',')))
 for it in range(rounds):
  z=(solve_bus(C,T,M,A,plan,seed=it) if mode=='bus'
     else solve_weighted(C,T,M,A,plan,seed=it,extra=-2))
  if z is None:
   print('round',it,'no layout',file=sys.stderr);continue
  R,g,est,_=z;sc=evaluate(C,T,M,A,B,R,g)
  print('round',it,'cost',sc[0],'E',sc[1],'D',sc[2],'bounce',sc[3],
        'est',est,'plan',plan,'got',sc[4],file=sys.stderr)
  if sc[5]==0 and(best is None or sc[0]<best[0]):best=(sc[0],R,[x[:]for x in g],sc)
  # Integral control: ask the assignment for more where simulation underdelivered.
  alpha=float(os.environ.get('ALPHA',0.45 if mode=='bus' else 0.72))
  plan=normalize([plan[i]+alpha*(B[i]-sc[4][i]) for i in range(C)],sum(B))
 if best is None:raise SystemExit('no valid candidate')
 _,R,g,sc=best
 with open(out,'w')as f:
  f.write(str(R)+'\n');[f.write(' '.join(row)+'\n')for row in g]
 print('BEST',sc,file=sys.stderr)

if __name__=='__main__':main()
