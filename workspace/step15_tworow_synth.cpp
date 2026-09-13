#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <random>
#include <vector>
using namespace std;
static constexpr int C=8,M=999;
static constexpr array<int,C>A{684,297,330,609,999,198,474,108};
static constexpr array<int,C>B{363,437,412,646,602,557,260,422};
struct Result{array<int,C>out{};int last=0,err=0,score=0;};

// Two coupled L/D/R squirrel rows, followed by a vertical hamster row.
// Bits 1=L,2=D,4=R. phase selects one of the six direction orders.
static Result sim(const array<uint8_t,16>&mask,const array<uint8_t,16>&phase){
 static constexpr int ord[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
 static constexpr int bit[3]={1,2,4},dx[3]={-1,0,1};
 array<int,16>q{},ptr{};array<int,C>direct{};Result z;
 for(int t=1;t<=1008;t++){
  bool alive=false;
  for(int c=0;c<C;c++)if(t>=M-A[c]+1&&t<=M)q[c]++;
  for(int x:q)alive|=x;for(int x:direct)alive|=x;if(!alive&&t>M)break;
  array<int,16>remain=q,recv{};array<int,C>toDirect{};
  array<array<int,3>,16>to{};array<int,16>ns{};
  for(int i=0;i<16;i++){
   int cap=!!(mask[i]&1)+!!(mask[i]&2)+!!(mask[i]&4),take=min(q[i],cap);
   int ds[3],nd=0;for(int u=0;u<3;u++){int d=ord[phase[i]%6][u];if(mask[i]&bit[d])ds[nd++]=d;}
   for(int u=0;u<take;u++){
    int d=ds[(ptr[i]+u)%nd],row=i/C,col=i%C;
    to[i][u]=(d==1?(row==0?C+col:100+col):i+dx[d]);
   }
   ns[i]=take;remain[i]-=take;if(nd)ptr[i]=(ptr[i]+take)%nd;
  }
  for(int i=0;i<16;i++)for(int u=0;u<ns[i];u++){
   int v=to[i][u];
   if(v>=100)toDirect[v-100]++;
   else if(remain[v]>0)remain[i]++;
   else recv[v]++;
  }
  for(int i=0;i<16;i++)q[i]=remain[i]+recv[i];
  for(int c=0;c<C;c++){if(direct[c]){direct[c]--;z.out[c]++;z.last=t;}direct[c]+=toDirect[c];}
 }
 for(int c=0;c<C;c++)z.err+=abs(z.out[c]-B[c]);z.score=max(z.err,z.last-M);return z;
}
int main(int argc,char**argv){
 double sec=argc>1?atof(argv[1]):60;mt19937_64 rng(0x215BADC0FFEEULL);
 vector<uint8_t>opts[16];for(int i=0;i<16;i++){int c=i%C;for(int m=1;m<8;m++)
  if((m&2)&&!(c==0&&(m&1))&&!(c==C-1&&(m&4)))opts[i].push_back((uint8_t)m);}
 Result best;best.score=1e9;array<uint8_t,16>bm{},bp{};uint64_t evals=0;
 auto end=chrono::steady_clock::now()+chrono::milliseconds((int)(sec*1000));
 while(chrono::steady_clock::now()<end){
  array<uint8_t,16>m{},p{};for(int i=0;i<16;i++){m[i]=opts[i][rng()%opts[i].size()];p[i]=rng()%6;}
  Result cur=sim(m,p);double temp=35;
  for(int it=0;it<1200&&chrono::steady_clock::now()<end;it++){
   auto nm=m,np=p;int changes=(rng()%20==0)?2:1;
   while(changes--){int i=rng()%16;if(rng()&1)nm[i]=opts[i][rng()%opts[i].size()];else np[i]=rng()%6;}
   Result nr=sim(nm,np);evals++;int d=nr.score-cur.score;
   if(d<=0||uniform_real_distribution<double>(0,1)(rng)<exp(-d/temp)){m=nm;p=np;cur=nr;}
   temp=max(0.15,temp*0.993);
   if(cur.score<best.score){best=cur;bm=m;bp=p;cerr<<"best "<<best.score<<" E="<<best.err<<" D="<<best.last-M<<" out=";
    for(int x:best.out)cerr<<x<<',';cerr<<" evals="<<evals<<'\n';}
  }
 }
 cout<<"best="<<best.score<<" E="<<best.err<<" D="<<best.last-M<<" evals="<<evals<<"\n";
 for(int x:bm)cout<<(int)x<<' ';cout<<"\n";for(int x:bp)cout<<(int)x<<' ';cout<<"\n";
}
