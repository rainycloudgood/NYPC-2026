#define main embedded_challenge_main
#include "oracle_v1/release/challenge_oracle_v1.cpp"
#undef main

#include <fstream>

int main(int argc,char**argv){
    if(argc<3)return 2;
    ifstream in(argv[1]); in>>C>>T>>M; A.resize(C);B.resize(C);
    for(auto&x:A)in>>x; for(auto&x:B)in>>x;
    Grid grid; ifstream gg(argv[2]); gg>>grid.R; grid.cell.resize(grid.R*C);
    for(auto&s:grid.cell)gg>>s;
    int R=grid.R,NC=R*C,N=NC+C; auto p=parse_grid(grid);
    vector<long long>cnt(N),bp(C); vector<int>ptr(NC),active,sendlist,recv_targets,touched;
    vector<vector<int>>senders(N); vector<char>over(N),in_active(NC),in_touched(NC);
    auto add_active=[&](int x){if(x<NC&&cnt[x]>0&&!in_active[x]){in_active[x]=1;active.push_back(x);}};
    auto touch=[&](int x){if(x<NC&&!in_touched[x]){in_touched[x]=1;touched.push_back(x);}};
    long long dropped=0,total=accumulate(A.begin(),A.end(),0LL),last=0;
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
            if(over[y]){for(int x:senders[y]){cnt[x]++;touch(x);}}
            else {cnt[y]+=(long long)senders[y].size();touch(y);}
            senders[y].clear();over[y]=0;
        }
        vector<int>drained;
        for(int c=0;c<C;c++)if(cnt[NC+c]>0){cnt[NC+c]--;bp[c]++;last=t;drained.push_back(c);}
        for(int x:touched){in_touched[x]=0;add_active(x);}
        if(t>=M-2){
            cerr<<"t="<<t<<" drain=";for(int c:drained)cerr<<c<<',';
            cerr<<" cells=";
            for(int x=0;x<NC;x++)if(cnt[x])cerr<<'('<<x/C+1<<','<<x%C+1<<':'<<cnt[x]<<')';
            cerr<<" burrow=";for(int c=0;c<C;c++)if(cnt[NC+c])cerr<<'('<<c<<':'<<cnt[NC+c]<<')';
            cerr<<'\n';
        }
    }
    cerr<<"last="<<last<<" D="<<last-M<<" bp=";for(auto x:bp)cerr<<x<<',';cerr<<'\n';
}
