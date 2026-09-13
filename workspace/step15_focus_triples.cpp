#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main
#include <fstream>
#include <queue>
#include <set>

struct Mut{int p;string s;Result r;};
struct Cand{long long h;int a,b,c;bool operator<(const Cand&o)const{return h<o.h;}};
static vector<string> tokens(int r,int c,int R,int C){
 vector<pair<char,pair<int,int>>>ds={{'U',{-1,0}},{'D',{1,0}},{'L',{0,-1}},{'R',{0,1}}};vector<char>ok;
 for(auto[ch,d]:ds){int rr=r+d.first,cc=c+d.second;if(1<=rr&&rr<=R+1&&0<=cc&&cc<C)ok.push_back(ch);}set<string>z;z.insert("X");
 for(int m=1;m<(1<<(int)ok.size());m++){string s;for(int i=0;i<(int)ok.size();i++)if(m>>i&1)s+=ok[i];sort(s.begin(),s.end());do z.insert(s);while(next_permutation(s.begin(),s.end()));}
 for(auto[ch,d]:ds)for(int k=2;k<=max(R,C)+1;k++){int rr=r+d.first*k,cc=c+d.second*k;if(1<=rr&&rr<=R+1&&0<=cc&&cc<C)z.insert(to_string(k)+ch);}
 return {z.begin(),z.end()};
}
static auto key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}
int main(int argc,char**argv){
 if(argc<5)return 2;ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
 Grid base;ifstream gi(argv[2]);gi>>base.R;base.cell.resize(base.R*C);for(auto&s:base.cell)gi>>s;Result rr0=evaluate(base);
 vector<int>focus={18,10,34,29,21,28,37,42};int chunk=stoi(argv[4]);if(chunk<0||chunk>5)return 3;
 vector<vector<Mut>>m(8);long long singles=0;
 for(int q=0;q<8;q++)for(const string&s:tokens(focus[q]/C+1,focus[q]%C,base.R,C))if(s!=base.cell[focus[q]]){Grid g=base;g.cell[focus[q]]=s;Result r=evaluate(g);if(r.L==0)m[q].push_back({focus[q],s,r});++singles;}
 const int KEEP=5000;priority_queue<Cand>pq;long long predicted=0;
 for(int j=chunk+1;j<7;j++)for(int k=j+1;k<8;k++)for(int ai=0;ai<(int)m[chunk].size();ai++)for(int bi=0;bi<(int)m[j].size();bi++)for(int ci=0;ci<(int)m[k].size();ci++){
   const Result&x=m[chunk][ai].r;const Result&y=m[j][bi].r;const Result&z=m[k][ci].r;long long ep=0;
   for(int d=0;d<C;d++){long long v=x.bp[d]+y.bp[d]+z.bp[d]-2*rr0.bp[d];ep+=llabs(v-B[d]);}
   if(ep>24)continue;long long dp=max(0LL,x.D+y.D+z.D-2*rr0.D);long long h=10000*ep+100*llabs(dp-14)+(x.bounces+y.bounces+z.bounces)/100;
   int packed=(ai<<16)|(bi<<8)|ci;Cand cc{h,packed,j,k};if((int)pq.size()<KEEP)pq.push(cc);else if(cc.h<pq.top().h){pq.pop();pq.push(cc);}++predicted;
 }
 vector<Cand>todo;while(!pq.empty()){todo.push_back(pq.top());pq.pop();}sort(todo.begin(),todo.end(),[](auto&a,auto&b){return a.h<b.h;});
 Grid best=base;Result br=rr0;long long checked=0;
 for(auto&q:todo){int ai=q.a>>16,bi=(q.a>>8)&255,ci=q.a&255;Grid g=base;g.cell[m[chunk][ai].p]=m[chunk][ai].s;g.cell[m[q.b][bi].p]=m[q.b][bi].s;g.cell[m[q.c][ci].p]=m[q.c][ci].s;Result r=evaluate(g);++checked;if(r.L==0&&key(r)<key(br)){br=r;best=g;}}
 ofstream out(argv[3]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
 cerr<<"chunk="<<chunk<<" singles="<<singles<<" predicted="<<predicted<<" exact="<<checked<<" cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces<<'\n';
}
