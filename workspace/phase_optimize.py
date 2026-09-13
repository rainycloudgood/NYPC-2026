"""Greedily insert one-tick relays to reduce synchronized bounce congestion."""
import concurrent.futures,os,re,sys
import validate as V

def load_input(path):
 d=list(map(int,open(path).read().split()));C,T,M=d[:3]
 return C,T,M,d[3:3+C],d[3+C:3+2*C]
def load_grid(path,C):
 w=open(path).read().split();R=int(w[0]);return R,[w[1+r*C:1+(r+1)*C]for r in range(R)]
def score(args):
 C,T,M,A,B,R,g=args
 cells={(r+1,c):V.parse_cell(g[r][c])for r in range(R)for c in range(C)}
 bp,last,b,left=V.simulate(C,T,M,A,B,R,cells);L=sum(B)-sum(bp)
 E=sum(abs(bp[i]-B[i])for i in range(C));D=T if L else last-M
 return(1<<(R-C))+max(E,D)+T*L,E,D,b,L
def candidates(g,C,R):
 out=[]
 dirs={'D':(1,0),'U':(-1,0),'L':(0,-1),'R':(0,1)}
 for r in range(R):
  for c in range(C):
   m=re.fullmatch(r'(\d+)([UDLR])',g[r][c])
   if not m or int(m.group(1))<2:continue
   n,ch=int(m.group(1)),m.group(2);dr,dc=dirs[ch];r2,c2=r+dr,c+dc
   if not(0<=r2<R and 0<=c2<C)or g[r2][c2]!='X':continue
   ng=[x[:]for x in g];ng[r][c]=ch;ng[r2][c2]=ch if n-1==1 else f'{n-1}{ch}'
   out.append((r,c,ng))
 return out
def main():
 inp,src,dst=sys.argv[1:4];rounds=int(sys.argv[4]) if len(sys.argv)>4 else 4
 C,T,M,A,B=load_input(inp);R,g=load_grid(src,C);base=(C,T,M,A,B,R)
 cur=score(base+(g,));print('start',cur,file=sys.stderr)
 for rnd in range(rounds):
  cs=candidates(g,C,R)
  with concurrent.futures.ProcessPoolExecutor(max_workers=min(12,len(cs)))as ex:
   vals=list(ex.map(score,[base+(x[2],)for x in cs]))
  if not vals:break
  q=min(range(len(vals)),key=lambda i:vals[i])
  print('round',rnd,'at',cs[q][:2],vals[q],file=sys.stderr)
  if vals[q]>=cur:break
  cur=vals[q];g=cs[q][2]
 with open(dst,'w')as f:
  f.write(str(R)+'\n');[f.write(' '.join(row)+'\n')for row in g]
 print('BEST',cur,file=sys.stderr)
if __name__=='__main__':main()
