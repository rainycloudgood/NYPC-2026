#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main

#include <fstream>
#include <set>
#include <unordered_set>

static vector<string> tokens_at(int r,int c,int R,int C){
    vector<pair<char,pair<int,int>>> ds={{'U',{-1,0}},{'D',{1,0}},{'L',{0,-1}},{'R',{0,1}}};
    vector<char> ok;for(auto [ch,d]:ds){int nr=r+d.first,nc=c+d.second;if(1<=nr&&nr<=R+1&&0<=nc&&nc<C)ok.push_back(ch);}
    set<string> z;z.insert("X");
    for(int mask=1;mask<(1<<(int)ok.size());mask++){
        string s;for(int i=0;i<(int)ok.size();i++)if(mask>>i&1)s+=ok[i];sort(s.begin(),s.end());
        do z.insert(s);while(next_permutation(s.begin(),s.end()));
    }
    for(auto [ch,d]:ds)for(int k=2;k<=max(R,C)+1;k++){
        int nr=r+d.first*k,nc=c+d.second*k;if(1<=nr&&nr<=R+1&&0<=nc&&nc<C)z.insert(to_string(k)+ch);
    }
    return {z.begin(),z.end()};
}

static double energy(const Result&r){
    if(r.L)return 1e9+r.cost;
    // Test 15 targeted landscape: cost=16 is currently caused solely by D=15.
    // Search through same/worse official-cost states while keeping E near the
    // feasible cap, instead of letting the integer official cost dominate SA.
    return r.D+.03*r.E+8.0*max(0LL,r.E-14)+1e-5*min(10000LL,r.bounces);
}
static auto key(const Result&r){return tie(r.cost,r.D,r.E,r.bounces);}

int main(int argc,char**argv){
    if(argc<5){cerr<<"usage: fast_sa input grid output seconds\n";return 2;}
    ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
    Grid seed;ifstream gi(argv[2]);gi>>seed.R;seed.cell.resize(seed.R*C);for(auto&s:seed.cell)gi>>s;seed.label="fast_sa";
    double seconds=stod(argv[4]);vector<vector<string>> toks(seed.cell.size());vector<unordered_set<string>> valid(seed.cell.size());
    for(int p=0;p<(int)seed.cell.size();p++){toks[p]=tokens_at(p/C+1,p%C,seed.R,C);valid[p].insert(toks[p].begin(),toks[p].end());}
    uint64_t rng_seed=argc>=6?stoull(argv[5]):0x15A15A15ULL;
    mt19937_64 rng(rng_seed);uniform_real_distribution<double> U(0,1);
    // Tail-critical neighborhood for test 15: three final streams and their
    // immediate predecessors.  Bias mutations here while retaining global
    // moves for compensation of E.
    const vector<int> focus={18,10,34,29,21,28,37,42};
    Grid best=seed,cur=seed;Result br=evaluate(best),cr=br;long long it=0,accepted=0;
    auto start=chrono::steady_clock::now();
    while(chrono::duration<double>(chrono::steady_clock::now()-start).count()<seconds){
        it++;double elapsed=chrono::duration<double>(chrono::steady_clock::now()-start).count();
        double phase=fmod(elapsed,6.0)/6.0,temp=12.0*pow(.015,phase);
        Grid cand=cur;int nm=U(rng)<.52?1:(U(rng)<.72?2:(U(rng)<.84?3:4+rng()%4));
        for(int q=0;q<nm;q++){
            int p=U(rng)<.82?focus[rng()%focus.size()]:rng()%cand.cell.size();string old=cand.cell[p];double op=U(rng);
            if(op<.42&&old!="X"&&!isdigit((unsigned char)old[0])&&old.size()>1){
                shuffle(old.begin(),old.end(),rng);cand.cell[p]=old;
            }else if(op<.68&&old!="X"&&isdigit((unsigned char)old[0])){
                char d=old.back();vector<string> same;for(auto&t:toks[p])if(!t.empty()&&isdigit((unsigned char)t[0])&&t.back()==d)same.push_back(t);
                if(!same.empty())cand.cell[p]=same[rng()%same.size()];
            }else if(op<.82){
                int w=rng()%cand.cell.size();if(valid[p].count(cand.cell[w])&&valid[w].count(cand.cell[p]))swap(cand.cell[p],cand.cell[w]);
            }else cand.cell[p]=toks[p][rng()%toks[p].size()];
        }
        Result rr=evaluate(cand);double de=energy(rr)-energy(cr);
        if(de<=0||(de<80&&U(rng)<exp(-de/max(.01,temp)))){cur=cand;cr=rr;accepted++;}
        if(rr.L==0&&key(rr)<key(br)){
            best=cand;br=rr;if(br.cost<16)cerr<<"BREAKTHROUGH cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" bounce="<<br.bounces<<" iter="<<it<<" t="<<elapsed<<'\n';
        }
        if(it%5000==0){cur=best;cr=br;}
    }
    ofstream out(argv[3]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
    cerr<<"FINAL cost="<<br.cost<<" E="<<br.E<<" D="<<br.D<<" L="<<br.L<<" bounce="<<br.bounces<<" iter="<<it<<" accepted="<<accepted<<'\n';
}
