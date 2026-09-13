#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main
#include <fstream>

static vector<string> phases(string s){sort(s.begin(),s.end());vector<string>v;do v.push_back(s);while(next_permutation(s.begin(),s.end()));return v;}
static auto key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}

int main(int argc,char**argv){
    if(argc<5){cerr<<"usage input grid output chunk\n";return 2;}
    ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
    Grid base;ifstream gi(argv[2]);gi>>base.R;base.cell.resize(base.R*C);for(auto&s:base.cell)gi>>s;
    vector<int>pos={18,10,29,21,28,37};vector<vector<string>>op;for(int p:pos)op.push_back(phases(base.cell[p]));
    int chunk=stoi(argv[4]);if(chunk<0||chunk>=(int)op[0].size())return 3;
    Grid best=base,g=base;Result br=evaluate(base);long long checked=0;
    g.cell[pos[0]]=op[0][chunk];
    function<void(int)>dfs=[&](int q){
        if(q==(int)pos.size()){
            Result r=evaluate(g);++checked;if(r.L==0&&key(r)<key(br)){br=r;best=g;}
            return;
        }
        for(const string&s:op[q]){g.cell[pos[q]]=s;dfs(q+1);}
    };
    dfs(1);
    ofstream out(argv[3]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
    cerr<<"chunk="<<chunk<<" checked="<<checked<<" cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces<<'\n';
}
