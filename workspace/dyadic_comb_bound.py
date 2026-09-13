"""Static bound for splitting only the largest sources into dyadic combs."""
import argparse,math,random

def comb(a,depth):
 out=[];x=a;rate=1.0
 for _ in range(depth):
  hi=(x+1)//2;lo=x//2
  out.append((hi,rate/2));x=lo;rate/=2
 out.append((x,rate));return out

def solve(A,B,k,depth,cap,seed,steps=120000,chosen=None):
 C=len(A);chosen=set(sorted(range(C),key=lambda i:-A[i])[:k] if chosen is None else chosen);pieces=[]
 for i,a in enumerate(A):
  for x,r in (comb(a,depth) if i in chosen else [(a,1.0)]):pieces.append((x,r,i))
 rng=random.Random(seed+991*k+37*depth);n=len(pieces);dest=[rng.randrange(C) for _ in pieces];got=[0]*C;rate=[0.0]*C
 for q,(x,r,_) in enumerate(pieces):got[dest[q]]+=x;rate[dest[q]]+=r
 def local(j):
  return abs(got[j]-B[j])+2_000_000*max(0,rate[j]-cap)**2+200_000*max(0,0.45-rate[j])**2
 temp=30000.0
 for it in range(steps):
  if rng.random()<.72:
   q=rng.randrange(n);a=dest[q];b=rng.randrange(C)
   if a==b:continue
   x,r,_=pieces[q];old=local(a)+local(b);got[a]-=x;got[b]+=x;rate[a]-=r;rate[b]+=r;new=local(a)+local(b)
   if new<=old or rng.random()<math.exp((old-new)/max(1,temp)):dest[q]=b
   else:got[a]+=x;got[b]-=x;rate[a]+=r;rate[b]-=r
  else:
   q,w=rng.sample(range(n),2);a,b=dest[q],dest[w]
   if a==b:continue
   x,rx,_=pieces[q];y,ry,_=pieces[w];old=local(a)+local(b)
   got[a]+=y-x;got[b]+=x-y;rate[a]+=ry-rx;rate[b]+=rx-ry;new=local(a)+local(b)
   if new<=old or rng.random()<math.exp((old-new)/max(1,temp)):dest[q],dest[w]=b,a
   else:got[a]+=x-y;got[b]+=y-x;rate[a]+=rx-ry;rate[b]+=ry-rx
  temp*=.9999
 E=sum(abs(got[j]-B[j]) for j in range(C));score=E+2_000_000*sum(max(0,r-cap)**2 for r in rate)
 return score,E,max(rate),tuple(round(x,4) for x in rate),tuple(got),len(pieces),dest,pieces

def main():
 ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--steps',type=int,default=120000);ap.add_argument('--seeds',type=int,default=5);ap.add_argument('--quick',action='store_true');a=ap.parse_args();d=list(map(int,open(a.input).read().split()));C=d[0];A=d[3:3+C];B=d[3+C:3+2*C]
 for k in range(1,min(4,C+1)):
  for depth in ((6,8,10) if a.quick else (6,8,10,12)):
   for cap in ((1.02,1.05,1.10) if a.quick else (1.02,1.05,1.10,1.20)):
    z=min((solve(A,B,k,depth,cap,s,a.steps) for s in range(a.seeds)),key=lambda x:x[0])
    print('k',k,'d',depth,'cap',cap,'E',z[1],'rate',z[2],'rates',z[3],'pieces',z[5],flush=True)

if __name__=='__main__':main()
