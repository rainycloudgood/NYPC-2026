"""Compact direct four-way layout candidate (offline/public-data use)."""
import itertools,sys
from quarters_planner import assign_quarters

def tok(d,ch): return ch if d==1 else f'{d}{ch}'

def route(g,r,c,j,R):
    if g[r-1][c]!='X': return False
    if c==j: g[r-1][c]=tok(R+1-r,'D'); return True
    if g[r-1][j]!='X': return False
    g[r-1][c]=tok(abs(j-c),'R' if j>c else 'L')
    g[r-1][j]=tok(R+1-r,'D'); return True

def solve(C,T,M,A,B,seed=0,extra_rows=0):
    z=assign_quarters(A,B,seed)
    if z is None: return None
    e,p,target,got=z
    ts=[[target[4*i+q] for q in range(4)] for i in range(C)]
    R=2*C+4+extra_rows; empty=[['X']*C for _ in range(R)]

    def placements(g,i,limit=80):
        k=1 if i==0 else (C-2 if i==C-1 else i)
        out=[]
        for r in range(2,R):
            for js in set(itertools.permutations(ts[i])):
                ng=[row[:] for row in g]
                if ng[0][i]!='X' or ng[r-1][k]!='X': continue
                ng[0][i]=tok(r-1,'D')
                if i==0:
                    if ng[r-1][0]!='X': continue
                    ng[r-1][0]='R'
                elif i==C-1:
                    if ng[r-1][C-1]!='X': continue
                    ng[r-1][C-1]='L'
                ng[r-1][k]='UDLR'; good=True
                for d,j in zip('UDLR',js):
                    rr,cc=(r-1,k) if d=='U' else ((r+1,k) if d=='D' else (r,k-1 if d=='L' else k+1))
                    if not route(ng,rr,cc,j,R): good=False; break
                if good:
                    out.append(ng)
                    if len(out)>=limit:return out
        return out

    nodes=[0]
    def dfs(g,rem):
        nodes[0]+=1
        if nodes[0]>30000:return None
        if not rem:return g
        choice=None; opts=None
        for i in rem:
            z=placements(g,i)
            if not z:return None
            if opts is None or len(z)<len(opts): choice,opts=i,z
        nr=[i for i in rem if i!=choice]
        for ng in opts:
            ans=dfs(ng,nr)
            if ans is not None:return ans
        return None
    g=dfs(empty,list(range(C)))
    return None if g is None else (R,g,e,got)

if __name__=='__main__':
    d=list(map(int,sys.stdin.read().split())); C,T,M=d[:3];A=d[3:3+C];B=d[3+C:3+2*C]
    for extra in range(3):
     for seed in range(3):
        z=solve(C,T,M,A,B,seed,extra)
        if z:
            R,g,e,got=z; print(R); [print(*row) for row in g]
            print('E_est',e,'seed',seed,'extra',extra,'got',got,file=sys.stderr); break
     else: continue
     break
    else: raise SystemExit('no layout')
