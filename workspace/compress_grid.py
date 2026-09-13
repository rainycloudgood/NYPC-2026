"""Delete one X-only row and retarget vertical hamster tunnels."""
import re,sys

src,dst,C,d=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
w=open(src).read().split();R=int(w[0]);body=w[1:]
g=[body[r*C:(r+1)*C] for r in range(R)]
assert all(x=='X' for x in g[d-1])
out=[]
for r in range(1,R+1):
 if r==d: continue
 row=[]
 for tok in g[r-1]:
  m=re.fullmatch(r'(\d+)([UD])',tok)
  if m:
   dist=int(m.group(1));ch=m.group(2);target=r+dist if ch=='D' else r-dist
   nr=r-(r>d);nt=target-(target>d);nd=abs(nt-nr)
   tok=(ch if nd==1 else f'{nd}{ch}')
  row.append(tok)
 out.append(row)
with open(dst,'w') as f:
 f.write(str(R-1)+'\n')
 for row in out:f.write(' '.join(row)+'\n')
