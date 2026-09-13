#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main
#include <fstream>
#include <queue>

static Grid read_grid(const char*p){Grid g;ifstream f(p);f>>g.R;g.cell.resize(g.R*C);for(auto&s:g.cell)f>>s;return g;}
static double energy(const Result&r){if(r.L)return 1e9+r.cost;return 100.0*r.cost+2.0*r.D+.5*r.E+1e-4*r.bounces;}
static auto key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}
int main(int argc,char**argv){
 if(argc<7)return 2;ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
 Grid a=read_grid(argv[2]),b=read_grid(argv[3]);vector<int>d;for(int p=0;p<(int)a.cell.size();p++)if(a.cell[p]!=b.cell[p])d.push_back(p);
 double seconds=stod(argv[5]);mt19937_64 rng(stoull(argv[6]));uniform_real_distribution<double>U(0,1);
 uint64_t mask=0,cm=0,bm=0;Grid cur=a,best=a;Result cr=evaluate(cur),br=cr;auto start=chrono::steady_clock::now();long long it=0,acc=0;
 // Additive delivered-count screening over a million broad/sparse crossovers.
 vector<Result>single(d.size());for(int q=0;q<(int)d.size();q++){Grid g=a;g.cell[d[q]]=b.cell[d[q]];single[q]=evaluate(g);}
 struct Pred{long long h;uint64_t m;bool operator<(const Pred&o)const{return h<o.h;}};priority_queue<Pred>pq;const int KEEP=5000;
 for(int z=0;z<1000000;z++){
  uint64_t msk;if(z<200000){msk=0;int flips=1+rng()%12;for(int q=0;q<flips;q++)msk^=1ULL<<(rng()%d.size());}else msk=rng()&((1ULL<<d.size())-1);
  long long ep=0;for(int j=0;j<C;j++){long long v=br.bp[j];for(int q=0;q<(int)d.size();q++)if(msk>>q&1)v+=single[q].bp[j]-br.bp[j];ep+=llabs(v-B[j]);}
  Pred p{ep,msk};if((int)pq.size()<KEEP)pq.push(p);else if(p.h<pq.top().h){pq.pop();pq.push(p);}
 }
 while(!pq.empty()){
  uint64_t msk=pq.top().m;pq.pop();Grid g=a;for(int q=0;q<(int)d.size();q++)if(msk>>q&1)g.cell[d[q]]=b.cell[d[q]];Result r=evaluate(g);
  if(r.L==0&&key(r)<key(br)){best=g;br=r;bm=msk;if(br.cost<16)cerr<<"SCREEN BREAK cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" mask="<<bm<<'\n';}
 }
 cur=best;cr=br;cm=bm;
 start=chrono::steady_clock::now();
 while(chrono::duration<double>(chrono::steady_clock::now()-start).count()<seconds){
  ++it;double t=chrono::duration<double>(chrono::steady_clock::now()-start).count();double cyc=fmod(t,2.0)/2.0,temp=10*pow(.02,cyc);uint64_t nm=cm;int flips=U(rng)<.55?1:(U(rng)<.75?2:3+rng()%7);
  for(int q=0;q<flips;q++)nm^=1ULL<<(rng()%d.size());Grid g=a;for(int q=0;q<(int)d.size();q++)if(nm>>q&1)g.cell[d[q]]=b.cell[d[q]];Result r=evaluate(g);double de=energy(r)-energy(cr);
  if(de<=0||(de<100&&U(rng)<exp(-de/max(.01,temp)))){cur=g;cr=r;cm=nm;++acc;}
  if(r.L==0&&key(r)<key(br)){best=g;br=r;bm=nm;if(br.cost<16)cerr<<"BREAK cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" mask="<<bm<<'\n';}
  if(it%5000==0){cur=best;cr=br;cm=bm;}
 }
 ofstream out(argv[4]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
 cerr<<"diff="<<d.size()<<" it="<<it<<" acc="<<acc<<" cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces<<" mask="<<bm<<'\n';
}
