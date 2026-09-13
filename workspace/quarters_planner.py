"""Offline equal-quarter assignment with layout-aware penalties."""
import random


def assign_quarters(A, B, seed=0, restarts=10, steps=80_000, min_sides=1,
                    min_lateral=0):
    C = len(A)
    pieces = []
    for src, a in enumerate(A):
        q, rem = divmod(a, 4)
        pieces.extend((q + (part < rem), src, part) for part in range(4))
    rng = random.Random(0x4A17 + seed * 1000003)
    best = None
    def layout_penalty(perm):
        dest=[0]*(4*C)
        for pos,pid in enumerate(perm): dest[pid]=pos//4
        bad=0
        for src in range(C):
            k=1 if src==0 else (C-2 if src==C-1 else src)
            ds=[dest[4*src+t] for t in range(4)]
            bad += max(0, min_sides-sum(j<k for j in ds))
            bad += max(0, min_sides-sum(j>k for j in ds))
            bad += max(0, min_lateral-sum(j!=k for j in ds))
        return bad
    for _ in range(restarts):
        perm = list(range(4*C)); rng.shuffle(perm)
        sums = [sum(pieces[perm[4*j+t]][0] for t in range(4)) for j in range(C)]
        cur = sum(abs(sums[j]-B[j]) for j in range(C))
        pen=layout_penalty(perm)
        for __ in range(steps//restarts):
            x,y=rng.sample(range(4*C),2); bx,by=x//4,y//4
            if bx==by: continue
            px,py=pieces[perm[x]][0],pieces[perm[y]][0]
            old=abs(sums[bx]-B[bx])+abs(sums[by]-B[by])
            nx,ny=sums[bx]-px+py,sums[by]-py+px
            new=abs(nx-B[bx])+abs(ny-B[by])
            perm[x],perm[y]=perm[y],perm[x]
            npen=layout_penalty(perm)
            perm[x],perm[y]=perm[y],perm[x]
            delta=(new-old)+(npen-pen)*1_000_000
            if delta<=0 or rng.random()<0.00015:
                perm[x],perm[y]=perm[y],perm[x]; sums[bx],sums[by]=nx,ny
                cur += new-old; pen=npen
        if pen==0 and (best is None or cur<best[0]):
            target=[-1]*(4*C)
            for j in range(C):
                for t in range(4): target[perm[4*j+t]]=j
            best=(cur,pieces,target,tuple(sums))
    return best
