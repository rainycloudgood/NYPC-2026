"""Estimate horizontal lane pressure for piece assignments."""
import sys
from weighted_piece_planner import assign,two_thirds_two_sixths,third_four_sixths
from quarters_planner import assign_quarters

def pressure(C,pieces,target):
 intervals=[]
 for q,p in enumerate(pieces):
  src=p[1];k=1 if src==0 else(C-2 if src==C-1 else src);j=target[q]
  intervals.append((min(k,j),max(k,j),src,j))
 counts=[]
 for c in range(C):counts.append(sum(a<=c<=b for a,b,_,_ in intervals))
 # Greedy coloring of closed integer intervals.
 colors=[];assignment=[]
 for item in sorted(intervals,key=lambda x:(x[0],x[1])):
  a,b,_,_=item
  for col,last in enumerate(colors):
   if last<a:colors[col]=b;assignment.append(col);break
  else:assignment.append(len(colors));colors.append(b)
 return max(counts),counts,len(colors),intervals

def weighted_pressure(C,A,pieces,target):
 load=[0.0]*C
 for q,(amount,src,_) in enumerate(pieces):
  k=1 if src==0 else(C-2 if src==C-1 else src);j=target[q];w=amount/A[src]
  for c in range(min(k,j),max(k,j)+1):load[c]+=w
 return max(load),load

def main():
 d=list(map(int,open(sys.argv[1]).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C]
 for name,z in [('quarter',assign_quarters(A,B,restarts=40,steps=400000,min_sides=0)),
                ('weighted4',assign(A,B,two_thirds_two_sixths,restarts=80,steps=800000)),
                ('weighted5',assign(A,B,third_four_sixths,restarts=80,steps=800000))]:
  e,p,t,got=z[:4];mx,counts,nc,ints=pressure(C,p,t)
  wm,wl=weighted_pressure(C,A,p,t)
  print(name,'E',e,'lane_lower',mx,'greedy',nc,'column_pressure',counts,
        'weighted_lower',wm,'weighted_load',[round(x,3)for x in wl])

if __name__=='__main__':main()
