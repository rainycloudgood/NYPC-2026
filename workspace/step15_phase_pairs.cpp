#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main

#include <fstream>
#include <set>

static bool phase_token(const string& s){
    return s!="X"&&!s.empty()&&!isdigit((unsigned char)s[0])&&s.size()>=2;
}

static vector<string> phases(string s){
    sort(s.begin(),s.end());vector<string> out;
    do out.push_back(s);while(next_permutation(s.begin(),s.end()));
    return out;
}

static vector<string> all_tokens(int r,int c,int R,int C){
    vector<pair<char,pair<int,int>>> dirs={{'U',{-1,0}},{'D',{1,0}},{'L',{0,-1}},{'R',{0,1}}};
    vector<char> ok;
    for(auto [ch,d]:dirs){int nr=r+d.first,nc=c+d.second;if(1<=nr&&nr<=R+1&&0<=nc&&nc<C)ok.push_back(ch);}
    set<string> uniq;uniq.insert("X");
    for(int mask=1;mask<(1<<(int)ok.size());mask++){
        string s;for(int i=0;i<(int)ok.size();i++)if(mask>>i&1)s+=ok[i];sort(s.begin(),s.end());
        do uniq.insert(s);while(next_permutation(s.begin(),s.end()));
    }
    for(auto [ch,d]:dirs)for(int dist=2;dist<=max(R,C)+1;dist++){
        int nr=r+d.first*dist,nc=c+d.second*dist;
        if(1<=nr&&nr<=R+1&&0<=nc&&nc<C)uniq.insert(to_string(dist)+ch);
    }
    return {uniq.begin(),uniq.end()};
}

static auto score_key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}

int main(int argc,char**argv){
    if(argc<4){cerr<<"usage: phase_pairs input grid output\n";return 2;}
    ifstream in(argv[1]);if(!(in>>C>>T>>M))return 3;
    A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
    ifstream gg(argv[2]);Grid base;gg>>base.R;base.cell.resize(base.R*C);
    for(auto&s:base.cell)gg>>s;base.label="phase_search";
    Grid best=base;Result br=evaluate(best);long long checked=0;

    // Complete one-cell coordinate descent over every syntactically valid
    // squirrel/hamster token.  Same-cost D/E/bounce improvements are retained
    // because they can unlock a later phase-pair improvement.
    for(int sweep=0;sweep<3;sweep++){
        bool changed=false;
        for(int p=0;p<(int)best.cell.size();p++){
            int r=p/C+1,c=p%C;Grid local=best;Result lr=br;
            for(const string&t:all_tokens(r,c,best.R,C)){
                if(t==best.cell[p])continue;Grid cand=best;cand.cell[p]=t;Result z=evaluate(cand);checked++;
                if(z.L==0&&score_key(z)<score_key(lr)){lr=z;local=move(cand);}
            }
            if(score_key(lr)<score_key(br)){
                br=lr;best=move(local);changed=true;
                cerr<<"one-cell best cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces
                    <<" cell="<<r<<','<<c<<" checked="<<checked<<'\n';
            }
        }
        if(!changed)break;
    }

    vector<int> hot;
    for(int p=0;p<(int)base.cell.size();p++)if(phase_token(base.cell[p]))hot.push_back(p);
    sort(hot.begin(),hot.end());hot.erase(unique(hot.begin(),hot.end()),hot.end());

    for(int ai=0;ai<(int)hot.size();ai++)for(int bi=ai+1;bi<(int)hot.size();bi++){
        int a=hot[ai],b=hot[bi];auto pa=phases(best.cell[a]),pb=phases(best.cell[b]);
        Grid cand=best;
        for(const string&x:pa)for(const string&y:pb){
            cand.cell[a]=x;cand.cell[b]=y;Result r=evaluate(cand);checked++;
            if(r.L==0&&score_key(r)<score_key(br)){
                br=r;best=cand;
                cerr<<"best cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces
                    <<" cells="<<a/C+1<<','<<a%C+1<<' '<<b/C+1<<','<<b%C+1<<" checked="<<checked<<'\n';
            }
        }
    }
    ofstream out(argv[3]);out<<best.R<<'\n';
    for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
    cerr<<"FINAL cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" L="<<br.L<<" bounce="<<br.bounces<<" checked="<<checked<<'\n';
}
