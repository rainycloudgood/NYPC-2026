#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main
#include <fstream>

static vector<string> opts(int r,int c,int R,int C){
    vector<string>v;int down=R-r;v.push_back(down==1?"D":to_string(down)+"D");v.push_back("D");
    if(c+1<C){v.push_back("DR");v.push_back("RD");for(int k=2;c+k<C;k++)v.push_back(to_string(k)+"R");}
    if(c>0){v.push_back("DL");v.push_back("LD");for(int k=2;c-k>=0;k++)v.push_back(to_string(k)+"L");}
    if(c>0&&c+1<C){string s="DLR";sort(s.begin(),s.end());do v.push_back(s);while(next_permutation(s.begin(),s.end()));}
    sort(v.begin(),v.end());v.erase(unique(v.begin(),v.end()),v.end());return v;
}
static double en(const Result&r){if(r.L)return 1e10+r.cost;return 10.0*max(r.E,r.D)+r.E+.2*r.D+1e-5*r.bounces;}
static auto key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}
int main(int argc,char**argv){
 if(argc<5)return 2;ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
 double seconds=stod(argv[3]);mt19937_64 rng(stoull(argv[4]));uniform_real_distribution<double>U(0,1);int R=C;
 vector<vector<string>>op(R*C);for(int r=0;r<R;r++)for(int c=0;c<C;c++)op[r*C+c]=opts(r,c,R,C);
 Grid best;Result br;br.cost=LLONG_MAX;long long it=0,acc=0,restarts=0;auto start=chrono::steady_clock::now();
 while(chrono::duration<double>(chrono::steady_clock::now()-start).count()<seconds){
  ++restarts;Grid cur;cur.R=R;cur.cell.resize(R*C);
  for(int r=0;r<R;r++)for(int c=0;c<C;c++)cur.cell[r*C+c]=(r==R-1?"D":op[r*C+c][rng()%op[r*C+c].size()]);
  Result cr=evaluate(cur);if(cr.L==0&&key(cr)<key(br)){best=cur;br=cr;}
  for(int z=0;z<2500&&chrono::duration<double>(chrono::steady_clock::now()-start).count()<seconds;z++){
   ++it;Grid g=cur;int nm=U(rng)<.72?1:(U(rng)<.85?2:3+rng()%5);
   for(int q=0;q<nm;q++){int p=rng()%((R-1)*C);g.cell[p]=op[p][rng()%op[p].size()];}
   Result rr=evaluate(g);double temp=80*pow(.01,(z%500)/500.0),de=en(rr)-en(cr);
   if(de<=0||(de<500&&U(rng)<exp(-de/max(.01,temp)))){cur=g;cr=rr;++acc;}
   if(rr.L==0&&key(rr)<key(br)){best=g;br=rr;if(br.cost<16)cerr<<"BREAK cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces<<'\n';}
  }
 }
 ofstream out(argv[2]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
 cerr<<"FINAL restarts="<<restarts<<" it="<<it<<" acc="<<acc<<" cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" L="<<br.L<<" bounce="<<br.bounces<<'\n';
}
