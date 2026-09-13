#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main

#include <fstream>
#include <queue>
#include <set>

struct Mut { int cell; string token; Result r; };
struct PairMut { int a,b; string x,y; Result r; };
struct Candidate {
    int heuristic;
    int pi,si;
    bool operator<(const Candidate&o)const { return heuristic<o.heuristic; }
};

static bool phase_token(const string&s){
    return s!="X"&&!s.empty()&&!isdigit((unsigned char)s[0])&&s.size()>=2;
}
static vector<string> phases(string s){
    sort(s.begin(),s.end()); vector<string> out;
    do out.push_back(s); while(next_permutation(s.begin(),s.end()));
    return out;
}
static auto score_key(const Result&r){ return tie(r.cost,r.D,r.E,r.bounces); }

int main(int argc,char**argv){
    if(argc<4){ cerr<<"usage: phase_triples input grid output\n"; return 2; }
    ifstream in(argv[1]); if(!(in>>C>>T>>M)) return 3;
    A.resize(C); B.resize(C); for(auto&x:A)in>>x; for(auto&x:B)in>>x;
    ifstream gg(argv[2]); Grid base; gg>>base.R; base.cell.resize(base.R*C);
    for(auto&s:base.cell)gg>>s; base.label="phase_triples";
    Result br=evaluate(base); Grid best=base;

    vector<Mut> singles;
    for(int p=0;p<(int)base.cell.size();p++) if(phase_token(base.cell[p])){
        for(const string&t:phases(base.cell[p])) if(t!=base.cell[p]){
            Grid g=base; g.cell[p]=t; Result r=evaluate(g);
            if(r.L==0) singles.push_back({p,t,r});
        }
    }
    cerr<<"singles="<<singles.size()<<" base cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<'\n';

    vector<PairMut> pairs;
    for(int i=0;i<(int)singles.size();i++) for(int j=i+1;j<(int)singles.size();j++){
        if(singles[i].cell==singles[j].cell) continue;
        Grid g=base; g.cell[singles[i].cell]=singles[i].token; g.cell[singles[j].cell]=singles[j].token;
        Result r=evaluate(g);
        if(r.L==0) pairs.push_back({singles[i].cell,singles[j].cell,singles[i].token,singles[j].token,r});
    }
    cerr<<"pairs="<<pairs.size()<<'\n';

    // Keep the combinations whose additive delivered-seed vector is closest to B.
    // The estimate is only a filter; every retained triple is evaluated exactly.
    const int KEEP=70000;
    priority_queue<Candidate> q;
    for(int pi=0;pi<(int)pairs.size();pi++) for(int si=0;si<(int)singles.size();si++){
        const auto&p=pairs[pi]; const auto&s=singles[si];
        if(s.cell==p.a||s.cell==p.b) continue;
        long long ep=0;
        for(int k=0;k<C;k++){
            long long predicted=p.r.bp[k]+s.r.bp[k]-br.bp[k];
            ep+=llabs(predicted-B[k]);
        }
        long long dp=max(0LL, p.r.D+s.r.D-br.D);
        int h=(int)(1000*ep+20*dp+p.r.bounces/100+s.r.bounces/100);
        Candidate c{h,pi,si};
        if((int)q.size()<KEEP)q.push(c);
        else if(c.heuristic<q.top().heuristic){q.pop();q.push(c);}
    }
    vector<Candidate> todo;
    while(!q.empty()){todo.push_back(q.top());q.pop();}
    sort(todo.begin(),todo.end(),[](auto&a,auto&b){return a.heuristic<b.heuristic;});
    cerr<<"exact triples="<<todo.size()<<'\n';

    long long checked=0;
    for(const Candidate&c:todo){
        const auto&p=pairs[c.pi]; const auto&s=singles[c.si];
        Grid g=base; g.cell[p.a]=p.x; g.cell[p.b]=p.y; g.cell[s.cell]=s.token;
        Result r=evaluate(g); checked++;
        if(r.L==0&&score_key(r)<score_key(br)){
            br=r; best=move(g);
            cerr<<"best cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces
                <<" cells="<<p.a/C+1<<','<<p.a%C+1<<' '<<p.b/C+1<<','<<p.b%C+1
                <<' '<<s.cell/C+1<<','<<s.cell%C+1<<" checked="<<checked<<'\n';
        }
    }
    ofstream out(argv[3]); out<<best.R<<'\n';
    for(int r=0;r<best.R;r++){
        for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');
    }
    cerr<<"FINAL cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" L="<<br.L
        <<" bounce="<<br.bounces<<" checked="<<checked<<'\n';
}
