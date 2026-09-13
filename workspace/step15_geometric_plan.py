"""Geometry-aware SA for eight depth-3 chain assignments on the 8x8 board."""

import math
import random
import time

A = [684, 297, 330, 609, 999, 198, 474, 108]
B = [363, 437, 412, 646, 602, 557, 260, 422]
C = 8
RATE = (4, 2, 1, 1)  # eighths of one seed/second; cap 10 = 1.25


def amounts(n):
    out = []
    for _ in range(3):
        hi = (n + 1) // 2;out.append(hi);n -= hi
    out.append(n)
    return out


def patterns(src):
    out = {}
    for c1 in range(max(0, src-1), min(C, src+2)):
        for c2 in range(max(0, c1-1), min(C, c1+2)):
            for d0 in range(C):
                for d1 in range(C):
                    for d2 in range(C):
                        for d3 in range(C):
                            remote = (abs(d0-src)>1)+(abs(d1-c1)>1)+(abs(d2-c2)>1)+(abs(d3-c2)>1)
                            key=(d0,d1,d2,d3);candidate=key+(c1,c2,remote)
                            if key not in out or remote<out[key][6]:out[key]=candidate
    return list(out.values())


def score(got, rate, remote):
    over = sum(max(0, x - 10) ** 2 for x in rate)
    return sum(abs(got[j] - B[j]) for j in range(C)) + 100000 * (over+max(0,remote-8)**2)


def main(seconds=25.0):
    rng = random.Random(150015);opts = [patterns(i) for i in range(C)]
    vals = [amounts(x) for x in A]
    print("pattern counts", [len(x) for x in opts], flush=True)
    global_best = None;start = time.time();restarts = iterations = 0
    while time.time() - start < seconds:
        restarts += 1;choice = [rng.choice(opts[i]) for i in range(C)]
        got = [0]*C;rate=[0]*C;remote=sum(p[6] for p in choice)
        for i,p in enumerate(choice):
            for q,d in enumerate(p[:4]):got[d]+=vals[i][q];rate[d]+=RATE[q]
        cur = score(got,rate,remote)
        for step in range(20000):
            iterations += 1;i=rng.randrange(C);old=choice[i];new=rng.choice(opts[i])
            ng=got[:];nr=rate[:];nremote=remote-old[6]+new[6]
            for q in range(4):
                ng[old[q]]-=vals[i][q];nr[old[q]]-=RATE[q]
                ng[new[q]]+=vals[i][q];nr[new[q]]+=RATE[q]
            ns=score(ng,nr,nremote);temp=5000*pow(.002,step/20000)
            if ns<=cur or rng.random()<math.exp((cur-ns)/max(.01,temp)):
                choice[i]=new;got,rate,remote,cur=ng,nr,nremote,ns
            if max(rate)<=10 and remote<=8:
                e=sum(abs(got[j]-B[j]) for j in range(C))
                if global_best is None or e<global_best[0]:
                    global_best=(e,choice[:],got[:],rate[:],remote)
                    print("BEST",e,"got",got,"rate",rate,"remote",remote,"choices",choice,flush=True)
                    if e<=2:
                        print("FINAL",global_best,"iterations",iterations);return
            if time.time()-start>=seconds:break
    print("FINAL",global_best,"iterations",iterations,"restarts",restarts)


if __name__=="__main__":main()
