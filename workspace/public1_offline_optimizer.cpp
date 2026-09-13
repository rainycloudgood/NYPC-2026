#include <algorithm>
#include <atomic>
#include <chrono>
#include <cctype>
#include <fstream>
#include <functional>
#include <iostream>
#include <mutex>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <thread>
#include <tuple>
#include <vector>
using namespace std;

struct Result {
    long long cost=0,E=0,D=0,L=0,bounces=0,last=0;
    vector<long long> bp;
};
struct Parsed { int cap=0; vector<int> target; };
struct Mutation { int a=-1,b=-1; string va,vb; string label; };

int C,R; long long T,M; vector<long long>A,B;
int dr(char d){return d=='U'?-1:d=='D'?1:0;}
int dc(char d){return d=='L'?-1:d=='R'?1:0;}
string hop(int n,char d){return n==1?string(1,d):to_string(n)+d;}

vector<Parsed> parse_grid(const vector<string>& g){
    int NC=R*C; vector<Parsed> p(NC);
    for(int r=0;r<R;r++)for(int c=0;c<C;c++){
        int id=r*C+c; const string&s=g[id];
        if(s=="X")continue;
        if(isdigit((unsigned char)s[0])){
            int q=0,n=0;while(q<(int)s.size()&&isdigit((unsigned char)s[q]))n=n*10+s[q++]-'0';
            char d=s[q];int rr=r+dr(d)*n,cc=c+dc(d)*n;
            p[id].cap=1;p[id].target.push_back(rr==R?NC+cc:rr*C+cc);
        }else{
            p[id].cap=(int)s.size();
            for(char d:s){int rr=r+dr(d),cc=c+dc(d);p[id].target.push_back(rr==R?NC+cc:rr*C+cc);}
        }
    }
    return p;
}

Result evaluate(const vector<string>& g){
    const int NC=R*C,N=NC+C; auto p=parse_grid(g);
    vector<long long>cnt(N),bp(C);vector<int>ptr(NC),active,sendlist,recv_targets,touched;
    vector<vector<int>>senders(N);vector<char>over(N),in_active(NC),in_touched(NC);
    auto add_active=[&](int x){if(x<NC&&cnt[x]>0&&!in_active[x]){in_active[x]=1;active.push_back(x);}};
    auto touch=[&](int x){if(x<NC&&!in_touched[x]){in_touched[x]=1;touched.push_back(x);}};
    long long dropped=0,total=accumulate(A.begin(),A.end(),0LL),last=0,bounces=0;
    for(long long t=1;t<=T;t++){
        bool burrow_wait=false;for(int c=0;c<C;c++)burrow_wait|=cnt[NC+c]>0;
        if(dropped>=total&&active.empty()&&!burrow_wait)break;
        for(int c=0;c<C;c++)if(M-A[c]+1<=t&&t<=M){cnt[c]++;dropped++;add_active(c);}
        sendlist=active;for(int x:sendlist)in_active[x]=0;active.clear();recv_targets.clear();touched.clear();
        for(int x:sendlist){
            touch(x);
            int amt=(int)min<long long>(cnt[x],p[x].cap);if(!amt)continue;
            int k=(int)p[x].target.size(),q=ptr[x];
            for(int j=0;j<amt;j++){
                int y=p[x].target[(q+j)%k];if(senders[y].empty())recv_targets.push_back(y);senders[y].push_back(x);
            }
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
    }
    long long sumB=accumulate(B.begin(),B.end(),0LL),sumBp=accumulate(bp.begin(),bp.end(),0LL);
    long long L=sumB-sumBp,E=0;for(int i=0;i<C;i++)E+=llabs(bp[i]-B[i]);
    long long D=L?T:last-M,cost=(1LL<<(R-C))+max(E,D)+T*L;
    return {cost,E,D,L,bounces,last,bp};
}

vector<Mutation> mutations(const vector<string>&g){
    vector<Mutation> out;
    for(int r=0;r<R;r++)for(int c=0;c<C;c++){
        int id=r*C+c;const string&s=g[id];if(s=="X")continue;
        if(!isdigit((unsigned char)s[0])&&s.size()>=2){
            string q=s;sort(q.begin(),q.end());
            do{if(q!=s)out.push_back({id,-1,q,"","perm"});}while(next_permutation(q.begin(),q.end()));
        }
        if(isdigit((unsigned char)s[0])){
            int q=0,n=0;while(q<(int)s.size()&&isdigit((unsigned char)s[q]))n=n*10+s[q++]-'0';char d=s[q];
            // A downward hop from the split area directly into one of the
            // bottom C bus rows is a leaf destination.  Retargeting that hop
            // moves the whole leaf stream to another burrow without changing
            // the splitter tree or adding cells.
            int bus0=R-C,land=r+dr(d)*n;
            if(d=='D'&&r<bus0&&land>=bus0&&land<R){
                for(int j=0;j<C;j++){
                    int nn=bus0+j-r;
                    if(nn>=1&&nn!=n)out.push_back({id,-1,hop(nn,'D'),"","retarget"});
                }
            }
            for(int cut=1;cut<n;cut++){
                int rr=r+dr(d)*cut,cc=c+dc(d)*cut;if(rr<0||rr>=R||cc<0||cc>=C)continue;
                int mid=rr*C+cc;if(g[mid]=="X")out.push_back({id,mid,hop(cut,d),hop(n-cut,d),"relay"});
            }
        }
        if(s.size()==1&&string("UDLR").find(s[0])!=string::npos){
            char d=s[0];int rr=r+dr(d),cc=c+dc(d);if(rr<0||rr>=R||cc<0||cc>=C)continue;
            int mid=rr*C+cc;const string&t=g[mid];int n=0;char td=0;
            if(t.size()==1&&t[0]==d){n=1;td=d;}
            else if(!t.empty()&&isdigit((unsigned char)t[0])){int q=0;while(q<(int)t.size()&&isdigit((unsigned char)t[q]))n=n*10+t[q++]-'0';td=t[q];}
            if(n&&td==d)out.push_back({id,mid,hop(n+1,d),"X","merge"});
        }
    }
    return out;
}

bool structurally_valid(const vector<string>&g){
    int NC=R*C;auto p=parse_grid(g);vector<char>state(NC);
    function<bool(int)> dfs=[&](int x){
        if(x>=NC)return true;if(p[x].cap==0)return false;
        if(state[x]==1)return false;if(state[x]==2)return true;state[x]=1;
        for(int y:p[x].target)if(!dfs(y))return false;
        state[x]=2;return true;
    };
    for(int c=0;c<C;c++)if(A[c]>0&&!dfs(c))return false;
    return true;
}

void apply_mut(vector<string>&g,const Mutation&m){g[m.a]=m.va;if(m.b>=0)g[m.b]=m.vb;}
bool better(const Result&a,const Result&b){return tie(a.cost,a.E,a.D,a.bounces)<tie(b.cost,b.E,b.D,b.bounces);}
void print_result(const string&tag,const Result&s){
    cerr<<tag<<" cost="<<s.cost<<" E="<<s.E<<" D="<<s.D<<" L="<<s.L<<" bounce="<<s.bounces<<" bp=";
    for(auto x:s.bp)cerr<<x<<',';cerr<<'\n';
}

pair<int,Result> parallel_best(const vector<vector<string>>&gs,const Result&base,int threads){
    atomic<size_t>next{0};vector<Result>res(gs.size());vector<thread>pool;
    threads=max(1,min<int>(threads,(int)gs.size()));
    for(int w=0;w<threads;w++)pool.emplace_back([&]{for(;;){size_t i=next++;if(i>=gs.size())break;res[i]=evaluate(gs[i]);}});
    for(auto&t:pool)t.join();int bi=-1;Result br=base;
    for(int i=0;i<(int)gs.size();i++)if(res[i].L==0&&better(res[i],br)){bi=i;br=res[i];}
    return {bi,br};
}

int main(int argc,char**argv){
    if(argc<4){cerr<<"usage: optimizer input grid output [rounds] [random_trials]\n";return 2;}
    ifstream fi(argv[1]);fi>>C>>T>>M;A.resize(C);B.resize(C);for(auto&x:A)fi>>x;for(auto&x:B)fi>>x;
    ifstream fg(argv[2]);fg>>R;vector<string>bestg(R*C);for(auto&x:bestg)fg>>x;
    int rounds=argc>4?stoi(argv[4]):3,trials=argc>5?stoi(argv[5]):300;
    int threads=argc>6?stoi(argv[6]):max(1u,thread::hardware_concurrency());
    Result best=evaluate(bestg);print_result("START",best);
    long long evals=1;auto started=chrono::steady_clock::now();
    for(int round=0;round<rounds;round++){
        auto ms=mutations(bestg);vector<vector<string>>gs;vector<string>labels;
        for(const auto&m:ms){auto g=bestg;apply_mut(g,m);if(structurally_valid(g)){gs.push_back(move(g));labels.push_back(m.label);}}
        auto [bi,pick]=parallel_best(gs,best,threads);evals+=gs.size();
        if(bi<0){cerr<<"round "<<round<<" no single improvement among "<<gs.size()<<"\n";break;}
        best=pick;bestg=move(gs[bi]);print_result("ROUND "+to_string(round)+" "+labels[bi],best);
    }
    mt19937_64 rng(0xDADA1001);auto base_ms=mutations(bestg);
    vector<Mutation>retarget_ms,targeted_ms;
    auto bus_dest=[&](int id,const string&s){
        int r=id/C;if(s.empty()||!isdigit((unsigned char)s[0]))return -1;
        int q=0,n=0;while(q<(int)s.size()&&isdigit((unsigned char)s[q]))n=n*10+s[q++]-'0';
        if(q>=(int)s.size()||s[q]!='D')return -1;int land=r+n,bus0=R-C;
        return land>=bus0&&land<R?land-bus0:-1;
    };
    for(const auto&m:base_ms)if(m.label=="retarget"){
        retarget_ms.push_back(m);int from=bus_dest(m.a,bestg[m.a]),to=bus_dest(m.a,m.va);
        if(from>=0&&to>=0&&best.bp[from]>B[from]&&best.bp[to]<B[to])targeted_ms.push_back(m);
    }
    vector<vector<string>>random_g;
    const auto&pool=!retarget_ms.empty()?retarget_ms:base_ms;
    for(int it=0;it<trials&&!pool.empty();it++){
        auto g=bestg;int k=2+(rng()%3);set<int>used;
        for(int z=0;z<k;z++){
            const auto&pickpool=(z==0&&!targeted_ms.empty())?targeted_ms:pool;
            const Mutation*m=nullptr;
            for(int guard=0;guard<20;guard++){const auto&x=pickpool[rng()%pickpool.size()];if(!used.count(x.a)){m=&x;break;}}
            if(!m)break;used.insert(m->a);apply_mut(g,*m);
        }
        if(structurally_valid(g))random_g.push_back(move(g));
    }
    cerr<<"random_pool targeted="<<targeted_ms.size()<<" retarget="<<retarget_ms.size()<<" all="<<base_ms.size()<<'\n';
    auto [ri,rpick]=parallel_best(random_g,best,threads);evals+=random_g.size();
    if(ri>=0){best=rpick;bestg=move(random_g[ri]);print_result("RANDOM",best);}
    ofstream fo(argv[3]);fo<<R<<'\n';for(int r=0;r<R;r++){for(int c=0;c<C;c++)fo<<bestg[r*C+c]<<(c+1==C?'\n':' ');}
    double sec=chrono::duration<double>(chrono::steady_clock::now()-started).count();
    print_result("BEST",best);cerr<<"evals="<<evals<<" seconds="<<sec<<" eval/s="<<evals/sec<<'\n';
}
