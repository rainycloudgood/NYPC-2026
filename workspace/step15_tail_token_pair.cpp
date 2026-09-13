#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main
#include <fstream>
#include <set>

static vector<string> all_tokens(int r,int c,int R,int C){
    vector<pair<char,pair<int,int>>>ds={{'U',{-1,0}},{'D',{1,0}},{'L',{0,-1}},{'R',{0,1}}};vector<char>ok;
    for(auto[ch,d]:ds){int rr=r+d.first,cc=c+d.second;if(1<=rr&&rr<=R+1&&0<=cc&&cc<C)ok.push_back(ch);}
    set<string>z;z.insert("X");for(int mask=1;mask<(1<<(int)ok.size());mask++){
        string s;for(int i=0;i<(int)ok.size();i++)if(mask>>i&1)s+=ok[i];sort(s.begin(),s.end());
        do z.insert(s);while(next_permutation(s.begin(),s.end()));
    }
    for(auto[ch,d]:ds)for(int k=2;k<=max(R,C)+1;k++){int rr=r+d.first*k,cc=c+d.second*k;if(1<=rr&&rr<=R+1&&0<=cc&&cc<C)z.insert(to_string(k)+ch);}
    return {z.begin(),z.end()};
}
static auto key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}
int main(int argc,char**argv){
    if(argc<5)return 2;ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
    Grid base;ifstream gi(argv[2]);gi>>base.R;base.cell.resize(base.R*C);for(auto&s:base.cell)gi>>s;
    vector<int>focus={18,10,34,29,21,28,37,42};vector<pair<int,int>>pairs;
    for(int i=0;i<(int)focus.size();i++)for(int j=i+1;j<(int)focus.size();j++)pairs.push_back({focus[i],focus[j]});
    int q=stoi(argv[4]);if(q<0||q>=(int)pairs.size())return 3;auto[a,b]=pairs[q];
    auto aa=all_tokens(a/C+1,a%C,base.R,C),bb=all_tokens(b/C+1,b%C,base.R,C);
    Grid g=base,best=base;Result br=evaluate(base);long long checked=0;
    for(const string&x:aa)for(const string&y:bb){g.cell[a]=x;g.cell[b]=y;Result r=evaluate(g);++checked;if(r.L==0&&key(r)<key(br)){br=r;best=g;}}
    ofstream out(argv[3]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
    cerr<<"pair="<<q<<" cells="<<a/C+1<<','<<a%C+1<<' '<<b/C+1<<','<<b%C+1<<" checked="<<checked<<" cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces<<'\n';
}
