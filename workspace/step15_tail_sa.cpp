#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main

#include <fstream>
#include <set>

struct TailResult { Result r; long long root_m=0, internal_m=0; };

static TailResult tail_evaluate(const Grid&grid){
    int R=grid.R,NC=R*C,N=NC+C;auto p=parse_grid(grid);
    vector<long long>cnt(N),bp(C);vector<int>ptr(NC),active,sendlist,recv_targets,touched;
    vector<vector<int>>senders(N);vector<char>over(N),in_active(NC),in_touched(NC);
    auto add_active=[&](int x){if(x<NC&&cnt[x]>0&&!in_active[x]){in_active[x]=1;active.push_back(x);}};
    auto touch=[&](int x){if(x<NC&&!in_touched[x]){in_touched[x]=1;touched.push_back(x);}};
    long long dropped=0,total=accumulate(A.begin(),A.end(),0LL),last=0,bounces=0,root_m=0,internal_m=0;
    for(long long t=1;t<=T;t++){
        bool burrow_wait=false;for(int c=0;c<C;c++)burrow_wait|=cnt[NC+c]>0;
        if(dropped>=total&&active.empty()&&!burrow_wait)break;
        for(int c=0;c<C;c++)if(M-A[c]+1<=t&&t<=M){cnt[c]++;dropped++;add_active(c);}
        sendlist=active;for(int x:sendlist)in_active[x]=0;active.clear();recv_targets.clear();touched.clear();
        for(int x:sendlist){
            touch(x);int amt=(int)min<long long>(cnt[x],p[x].cap);if(!amt)continue;
            int k=(int)p[x].target.size(),q=ptr[x];
            for(int j=0;j<amt;j++){int y=p[x].target[(q+j)%k];if(senders[y].empty())recv_targets.push_back(y);senders[y].push_back(x);}
            ptr[x]=(q+amt)%k;cnt[x]-=amt;
        }
        for(int y:recv_targets)over[y]=cnt[y]>0;
        for(int y:recv_targets){
            if(over[y]){bounces+=(long long)senders[y].size();for(int x:senders[y]){cnt[x]++;touch(x);}}
            else {cnt[y]+=(long long)senders[y].size();touch(y);}
            senders[y].clear();over[y]=0;
        }
        for(int c=0;c<C;c++)if(cnt[NC+c]>0){cnt[NC+c]--;bp[c]++;last=t;}
        for(int x:touched){in_touched[x]=0;add_active(x);}
        if(t==M){root_m=cnt[4];internal_m=accumulate(cnt.begin(),cnt.begin()+NC,0LL);}
    }
    long long sumB=accumulate(B.begin(),B.end(),0LL),sumBp=accumulate(bp.begin(),bp.end(),0LL);
    long long L=sumB-sumBp,E=0;for(int i=0;i<C;i++)E+=llabs(bp[i]-B[i]);
    long long D=L?T:last-M,cost=(1LL<<(grid.R-C))+max(E,D)+T*L;
    return {{cost,E,D,L,bounces,last,bp},root_m,internal_m};
}

static bool phase_token(const string&s){return s!="X"&&!s.empty()&&!isdigit((unsigned char)s[0])&&s.size()>=2;}
static vector<string> phases(string s){sort(s.begin(),s.end());vector<string>v;do v.push_back(s);while(next_permutation(s.begin(),s.end()));return v;}
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
static double energy(const TailResult&z){
    if(z.r.L)return 1e12+z.r.cost;
    // Queue-aware redesign.  The old expression only penalized root backlog
    // ABOVE 31, even though 31 itself is exactly what forces the 15-tick tail.
    // Pay for every seed still queued at M and for the whole in-flight mass;
    // this lets SA cross temporarily inaccurate states to discover a network
    // that is structurally able to finish in two ticks.
    return 3.0*z.r.E + 2.0*z.r.D + 4.0*z.root_m + .08*z.internal_m
           + 1e-5*z.r.bounces;
}
static auto official(const TailResult&z){return tie(z.r.cost,z.r.D,z.r.E);}

int main(int argc,char**argv){
    if(argc<6){cerr<<"usage: tail_sa input grid output seconds seed\n";return 2;}
    ifstream in(argv[1]);in>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)in>>x;for(auto&x:B)in>>x;
    Grid seed;ifstream gi(argv[2]);gi>>seed.R;seed.cell.resize(seed.R*C);for(auto&s:seed.cell)gi>>s;
    vector<int>cells;vector<vector<string>>opts(seed.cell.size()),allopts(seed.cell.size());
    for(int p=0;p<(int)seed.cell.size();p++){
        allopts[p]=all_tokens(p/C+1,p%C,seed.R,C);
        if(phase_token(seed.cell[p])){cells.push_back(p);opts[p]=phases(seed.cell[p]);}
    }
    double seconds=stod(argv[4]);mt19937_64 rng(stoull(argv[5]));uniform_real_distribution<double>U(0,1);
    Grid cur=seed,best=seed,plateau=seed;TailResult cr=tail_evaluate(cur),br=cr,pr=cr;
    cerr<<"START cost="<<br.r.cost<<" E="<<br.r.E<<" D="<<br.r.D<<" rootM="<<br.root_m<<" intM="<<br.internal_m<<'\n';
    auto start=chrono::steady_clock::now();long long it=0,acc=0;
    while(chrono::duration<double>(chrono::steady_clock::now()-start).count()<seconds){
        ++it;double elapsed=chrono::duration<double>(chrono::steady_clock::now()-start).count();
        double cyc=fmod(elapsed,8.0)/8.0,temp=5.0*pow(.015,cyc);Grid cand=cur;
        int n=U(rng)<.68?1:(U(rng)<.80?2:3+rng()%4);
        for(int q=0;q<n;q++){
            if(U(rng)<.82){int p=cells[rng()%cells.size()];cand.cell[p]=opts[p][rng()%opts[p].size()];}
            else {int p=rng()%cand.cell.size();cand.cell[p]=allopts[p][rng()%allopts[p].size()];}
        }
        TailResult rr=tail_evaluate(cand);double de=energy(rr)-energy(cr);
        if(de<=0||(de<60&&U(rng)<exp(-de/max(.01,temp)))){cur=cand;cr=rr;++acc;}
        if(official(rr)<official(br)){best=cand;br=rr;if(br.r.cost<16)cerr<<"BREAKTHROUGH cost="<<br.r.cost<<" E="<<br.r.E<<" D="<<br.r.D<<" rootM="<<br.root_m<<" intM="<<br.internal_m<<" it="<<it<<'\n';}
        if(energy(rr)<energy(pr)){plateau=cand;pr=rr;}
        if(it%12000==0){cur=plateau;cr=pr;}
    }
    ofstream out(argv[3]);out<<best.R<<'\n';for(int r=0;r<best.R;r++){for(int c=0;c<C;c++)out<<best.cell[r*C+c]<<(c+1==C?'\n':' ');}
    cerr<<"FINAL cost="<<br.r.cost<<" E="<<br.r.E<<" D="<<br.r.D<<" rootM="<<br.root_m<<" intM="<<br.internal_m<<" it="<<it<<" acc="<<acc<<'\n';
    ofstream po(string(argv[3])+".plateau");po<<plateau.R<<'\n';for(int r=0;r<plateau.R;r++){for(int c=0;c<C;c++)po<<plateau.cell[r*C+c]<<(c+1==C?'\n':' ');}
    cerr<<"PLATEAU cost="<<pr.r.cost<<" E="<<pr.r.E<<" D="<<pr.r.D<<" rootM="<<pr.root_m<<" intM="<<pr.internal_m<<" energy="<<energy(pr)<<'\n';
}
