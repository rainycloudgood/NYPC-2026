#include <bits/stdc++.h>
using namespace std;

struct Cell {
    int type = 1;       // 1 = squirrel, 2 = hamster
    string dirs;        // squirrel directions, or "X"
    long long dist = 0; // hamster distance
    char hdir = 0;      // hamster direction
    int ptr = 0;        // squirrel round-robin pointer
};

static Cell parseCell(const string &tok) {
    Cell c;
    if (tok == "X") {
        c.type = 1;
        c.dirs = "X";
        return c;
    }
    if (!tok.empty() && isdigit((unsigned char)tok[0])) {
        size_t i = 0;
        while (i < tok.size() && isdigit((unsigned char)tok[i])) i++;
        c.type = 2;
        c.dist = stoll(tok.substr(0, i));
        c.hdir = tok[i];
        return c;
    }
    c.type = 1;
    c.dirs = tok;
    return c;
}

static bool validCell(const string &tok, int r, int c, int R, int C) {
    auto validDir = [](char ch) {
        return ch == 'U' || ch == 'D' || ch == 'L' || ch == 'R';
    };
    auto inside = [&](int tr, int tc) {
        return 1 <= tr && tr <= R + 1 && 0 <= tc && tc < C;
    };

    if (tok == "X") return true;
    if (!tok.empty() && isdigit((unsigned char)tok[0])) {
        size_t i = 0;
        while (i < tok.size() && isdigit((unsigned char)tok[i])) i++;
        if (i == 0 || i + 1 != tok.size() || !validDir(tok[i])) return false;
        long long dist = stoll(tok.substr(0, i));
        if (dist <= 1) return false;
        int dr = 0, dc = 0;
        if (tok[i] == 'U') dr = -1;
        if (tok[i] == 'D') dr = 1;
        if (tok[i] == 'L') dc = -1;
        if (tok[i] == 'R') dc = 1;
        int tr = r + dr * (int)dist;
        int tc = c + dc * (int)dist;
        return tr != 0 && inside(tr, tc);
    }

    array<int, 256> seen{};
    for (char ch : tok) {
        if (!validDir(ch) || seen[(unsigned char)ch]) return false;
        seen[(unsigned char)ch] = 1;
        int tr = r, tc = c;
        if (ch == 'U') tr--;
        if (ch == 'D') tr++;
        if (ch == 'L') tc--;
        if (ch == 'R') tc++;
        if (tr == 0 || !inside(tr, tc)) return false;
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int C;
    long long T, M;
    cin >> C >> T >> M;
    vector<long long> A(C), B(C);
    for (auto &x : A) cin >> x;
    for (auto &x : B) cin >> x;

    int R;
    cin >> R;
    vector<vector<Cell>> cells(R + 1, vector<Cell>(C));
    for (int r = 1; r <= R; r++) {
        for (int c = 0; c < C; c++) {
            string tok;
            cin >> tok;
            if (!validCell(tok, r, c, R, C)) {
                cerr << "Invalid cell token at row " << r << ", col " << c + 1 << ": " << tok << "\n";
                return 1;
            }
            cells[r][c] = parseCell(tok);
        }
    }

    auto dirVec = [](char d) -> pair<int, int> {
        switch (d) {
            case 'U': return {-1, 0};
            case 'D': return {1, 0};
            case 'L': return {0, -1};
            case 'R': return {0, 1};
        }
        return {0, 0};
    };

    vector<vector<long long>> cnt(R + 2, vector<long long>(C, 0));
    vector<long long> Bp(C, 0);
    long long lastStored = 0;

    auto capacity = [&](int r, int c) -> long long {
        Cell &cell = cells[r][c];
        if (cell.type == 1) {
            if (cell.dirs == "X") return 0;
            return (long long)cell.dirs.size();
        }
        return 1;
    };

    for (long long t = 1; t <= T; t++) {
        vector<vector<long long>> start = cnt;
        vector<vector<long long>> sentAmt(R + 2, vector<long long>(C, 0));
        vector<array<int, 4>> transfers; // sr, sc, tr, tc per seed

        for (int r = 1; r <= R; r++) {
            for (int c = 0; c < C; c++) {
                long long cap = capacity(r, c);
                long long amt = min(start[r][c], cap);
                if (amt <= 0) continue;

                sentAmt[r][c] = amt;
                Cell &cell = cells[r][c];
                for (long long k = 0; k < amt; k++) {
                    int tr, tc;
                    if (cell.type == 1) {
                        char d = cell.dirs[(cell.ptr + k) % cell.dirs.size()];
                        auto [dr, dc] = dirVec(d);
                        tr = r + dr;
                        tc = c + dc;
                    } else {
                        auto [dr, dc] = dirVec(cell.hdir);
                        tr = r + dr * (int)cell.dist;
                        tc = c + dc * (int)cell.dist;
                    }
                    transfers.push_back({r, c, tr, tc});
                }
                if (cell.type == 1 && cell.dirs != "X") {
                    cell.ptr = (int)((cell.ptr + amt) % (long long)cell.dirs.size());
                }
            }
        }

        vector<vector<char>> overloaded(R + 1, vector<char>(C, 0));
        for (int r = 1; r <= R; r++) {
            for (int c = 0; c < C; c++) {
                if (start[r][c] > capacity(r, c)) overloaded[r][c] = 1;
            }
        }

        vector<vector<long long>> next = cnt;
        for (int i = 0; i < C; i++) {
            if (M - A[i] + 1 <= t && t <= M) next[1][i] += 1;
        }

        for (int r = 1; r <= R; r++) {
            for (int c = 0; c < C; c++) {
                next[r][c] -= sentAmt[r][c];
            }
        }

        for (auto &tr4 : transfers) {
            int sr = tr4[0], sc = tr4[1], tr = tr4[2], tc = tr4[3];
            bool outOfGrid = (tr < 0 || tr > R + 1 || tc < 0 || tc >= C);
            bool targetOverloaded = (!outOfGrid && 1 <= tr && tr <= R && overloaded[tr][tc]);
            if (outOfGrid || targetOverloaded) {
                next[sr][sc] += 1;
            } else {
                next[tr][tc] += 1;
            }
        }

        for (int c = 0; c < C; c++) {
            if (next[R + 1][c] > 0) {
                next[R + 1][c] -= 1;
                Bp[c] += 1;
                lastStored = t;
            }
        }

        cnt = move(next);
    }

    long long L = 0, E = 0;
    for (int i = 0; i < C; i++) {
        L += max(0LL, B[i] - Bp[i]);
        E += llabs(Bp[i] - B[i]);
    }

    long long D, cost;
    if (L == 0) {
        D = lastStored - M;
        cost = (1LL << (R - C)) + max(E, D);
    } else {
        D = T;
        cost = (1LL << (R - C)) + max(E, D) + T * L;
    }

    cerr << "Bp:";
    for (auto v : Bp) cerr << ' ' << v;
    cerr << "\nL=" << L << " E=" << E << " lastStored=" << lastStored
         << " D=" << D << " cost=" << cost << "\n";

    cout << "L=" << L << " E=" << E << " D=" << D << " cost=" << cost << "\n";
    return 0;
}
