#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <random>
#include <cstdlib>
#include <vector>
using namespace std;

// Fresh Step-Up 15 synthesis model:
// row 1 is a coupled L/R/D squirrel network, row 2 sends straight to burrows.
// We optimize the exact official simultaneous-send / bounce dynamics.
static constexpr int C = 8, M = 999, T = 2000;
static constexpr array<int,C> A{684,297,330,609,999,198,474,108};
static constexpr array<int,C> B{363,437,412,646,602,557,260,422};

struct Result { array<int,C> out{}; int last=0, err=0, score=0; };

// Bits: 1=L, 2=D, 4=R. Direction iteration follows token character order,
// represented separately by one of the six permutations when all are present.
static Result sim(const array<uint8_t,C>& mask, const array<uint8_t,C>& phase) {
    array<int,C> q{}, down{}, ptr{};
    Result z;
    static constexpr int ord[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
    static constexpr int bit[3]={1,2,4};
    static constexpr int delta[3]={-1,0,1};
    for(int t=1;t<=1005;t++) {
        bool alive=false;
        for(int i=0;i<C;i++) {
            if(t>=M-A[i]+1 && t<=M) q[i]++;
            alive |= q[i] || down[i];
        }
        if(!alive && t>M) break;
        array<int,C> remain=q, recv{}, downRecv{};
        array<array<int,3>,C> sendTo{};
        array<int,C> ns{};
        for(int i=0;i<C;i++) {
            int cap=((mask[i]&1)!=0)+((mask[i]&2)!=0)+((mask[i]&4)!=0);
            int take=min(q[i],cap), k=0;
            int dirs[3], nd=0;
            for(int u=0;u<3;u++) { int d=ord[phase[i]%6][u]; if(mask[i]&bit[d]) dirs[nd++]=d; }
            for(int u=0;u<take;u++) {
                int d=dirs[(ptr[i]+u)%nd];
                sendTo[i][k++]=(d==1 ? 100+i : i+delta[d]);
            }
            ns[i]=take;
            remain[i]-=take;
            if(nd) ptr[i]=(ptr[i]+take)%nd;
        }
        // Receiving cell is overloaded iff it still contains a seed after sending.
        for(int i=0;i<C;i++) for(int u=0;u<ns[i];u++) {
            int v=sendTo[i][u];
            if(v>=100) downRecv[v-100]++;
            else if(remain[v]>0) remain[i]++; // bounced to sender
            else recv[v]++;
        }
        for(int i=0;i<C;i++) q[i]=remain[i]+recv[i];
        // row 2 is a hamster: old contents depart now, new arrivals wait one tick.
        for(int i=0;i<C;i++) {
            if(down[i]>0) { down[i]--; z.out[i]++; z.last=t; }
            down[i]+=downRecv[i];
        }
    }
    for(int i=0;i<C;i++) z.err+=abs(z.out[i]-B[i]);
    z.score=max(z.err,z.last-M);
    return z;
}

int main(int argc,char**argv){
    double seconds=argc>1?atof(argv[1]):30.0;
    mt19937_64 rng(0x15F12345ULL);
    vector<uint8_t> opts[C];
    for(int i=0;i<C;i++) for(int m=1;m<8;m++)
        if(!(i==0&&(m&1)) && !(i==C-1&&(m&4)) && (m&2)) opts[i].push_back((uint8_t)m);
    // Require D: otherwise lossless completion through this shallow model is impossible.
    Result global; global.score=1e9;
    array<uint8_t,C> gm{},gp{};
    auto end=chrono::steady_clock::now()+chrono::milliseconds((int)(seconds*1000));
    uint64_t evals=0;
    while(chrono::steady_clock::now()<end){
        array<uint8_t,C> m{},p{};
        for(int i=0;i<C;i++){m[i]=opts[i][rng()%opts[i].size()];p[i]=rng()%6;}
        Result cur=sim(m,p); double temp=20;
        for(int it=0;it<400 && chrono::steady_clock::now()<end;it++){
            auto nm=m,np=p; int i=rng()%C;
            if(rng()&1) nm[i]=opts[i][rng()%opts[i].size()]; else np[i]=rng()%6;
            Result nr=sim(nm,np); evals++;
            int d=nr.score-cur.score;
            if(d<=0 || uniform_real_distribution<double>(0,1)(rng)<exp(-d/temp)){m=nm;p=np;cur=nr;}
            temp*=0.985;
            if(cur.score<global.score){global=cur;gm=m;gp=p;
                cerr<<"best "<<global.score<<" E="<<global.err<<" D="<<global.last-M<<" out=";
                for(int x:global.out)cerr<<x<<',';cerr<<" masks=";
                for(int x:gm)cerr<<x<<',';cerr<<" phases=";for(int x:gp)cerr<<x<<',';cerr<<" evals="<<evals<<'\n';
            }
        }
    }
    cout<<"best="<<global.score<<" E="<<global.err<<" D="<<global.last-M<<" evals="<<evals<<"\n";
    for(int x:gm)cout<<(int)x<<' ';cout<<"\n";for(int x:gp)cout<<(int)x<<' ';cout<<"\n";
}
