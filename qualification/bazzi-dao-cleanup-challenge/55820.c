#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

#define N 50

typedef enum {
    CELL_EMPTY,
    CELL_BLOCK,
    CELL_WALL
} CellType;

typedef struct {
    int x, y;
} Point;

typedef struct {
    CellType map[N][N];
    Point playerB;
    Point playerD;
    int K;
    int num_players;
} GameState;

typedef struct {
    Point data[N * N];
    int front, rear;
} Queue;

int dx[4] = {-1, 1, 0, 0};
int dy[4] = {0, 0, -1, 1};
char dir_char[4] = {'U', 'D', 'L', 'R'};

void initQueue(Queue* q) { q->front = 0; q->rear = 0; }
bool isEmpty(Queue* q) { return q->front == q->rear; }
void push(Queue* q, Point p) { q->data[q->rear++] = p; }
Point pop(Queue* q) { return q->data[q->front++]; }

// 폭탄 파괴력 시뮬레이션
int countDestroy(GameState* state, int x, int y) {
    if (state->map[x][y] == CELL_WALL || state->map[x][y] == CELL_BLOCK) return 0;
    int count = 0;
    for (int i = 0; i < 4; i++) {
        for (int len = 1; len <= state->K; len++) {
            int nx = x + dx[i] * len;
            int ny = y + dy[i] * len;
            if (nx < 0 || nx >= N || ny < 0 || ny >= N) break;
            if (state->map[nx][ny] == CELL_WALL) break;
            if (state->map[nx][ny] == CELL_BLOCK) {
                count++;
                break;
            }
        }
    }
    return count;
}

// 각 캐릭터별 개인 목적지 탐색 (상대방 위치는 장애물 처리)
Point findBestTarget(GameState* state, Point self, Point other, int dist[N][N], Point parent[N][N], bool use_other) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) dist[i][j] = -1;
    }

    Queue q;
    initQueue(&q);
    dist[self.x][self.y] = 0;
    parent[self.x][self.y] = self;
    push(&q, self);

    while (!isEmpty(&q)) {
        Point curr = pop(&q);
        for (int i = 0; i < 4; i++) {
            int nx = curr.x + dx[i];
            int ny = curr.y + dy[i];

            if (nx >= 0 && nx < N && ny >= 0 && ny < N) {
                if (state->map[nx][ny] == CELL_EMPTY && dist[nx][ny] == -1) {
                    // 2인용일 때만 상대방 좌표를 벽으로 우회
                    if (use_other && nx == other.x && ny == other.y) continue;
                    
                    dist[nx][ny] = dist[curr.x][curr.y] + 1;
                    parent[nx][ny] = curr;
                    push(&q, (Point){nx, ny});
                }
            }
        }
    }

    int best_score = -999999;
    Point target = self;
    
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (dist[i][j] != -1) {
                int destroy_cnt = countDestroy(state, i, j);
                if (destroy_cnt == 0) continue;

                // 휴리스틱 가중치 (이동 비용 대비 파괴 효율)
                int score = (destroy_cnt * 25) - dist[i][j];
                if (score > best_score) {
                    best_score = score;
                    target = (Point){i, j};
                }
            }
        }
    }
    return target;
}

// 폭발 맵 반영
void applyExplosion(GameState* state, int x, int y) {
    for (int i = 0; i < 4; i++) {
        for (int len = 1; len <= state->K; len++) {
            int nx = x + dx[i] * len;
            int ny = y + dy[i] * len;
            if (nx < 0 || nx >= N || ny < 0 || ny >= N) break;
            if (state->map[nx][ny] == CELL_WALL) break;
            if (state->map[nx][ny] == CELL_BLOCK) {
                state->map[nx][ny] = CELL_EMPTY;
                break;
            }
        }
    }
}

void solve(GameState* state) {
    while (true) {
        int distB[N][N], distD[N][N];
        Point parentB[N][N], parentD[N][N];

        bool has_other = (state->num_players == 2);

        // 1. 목적지 탐색
        Point targetB = findBestTarget(state, state->playerB, state->playerD, distB, parentB, has_other);
        Point targetD = { -1, -1 };
        if (has_other) {
            targetD = findBestTarget(state, state->playerD, state->playerB, distD, parentD, has_other);
        }

        // 탈출 조건 계산
        bool b_done = (targetB.x == state->playerB.x && targetB.y == state->playerB.y && countDestroy(state, targetB.x, targetB.y) == 0);
        bool d_done = true;
        if (has_other) {
            d_done = (targetD.x == state->playerD.x && targetD.y == state->playerD.y && countDestroy(state, targetD.x, targetD.y) == 0);
        }

        if (b_done && d_done) break;

        char actionB = '.';
        char actionD = '.';

        // [배찌 행동 역추적 및 결정]
        if (!b_done) {
            if (!(targetB.x == state->playerB.x && targetB.y == state->playerB.y)) {
                Point curr = targetB;
                while (!(parentB[curr.x][curr.y].x == state->playerB.x && parentB[curr.x][curr.y].y == state->playerB.y)) {
                    curr = parentB[curr.x][curr.y];
                }
                for (int i = 0; i < 4; i++) {
                    if (state->playerB.x + dx[i] == curr.x && state->playerB.y + dy[i] == curr.y) {
                        actionB = dir_char[i];
                        state->playerB = curr;
                        break;
                    }
                }
            } else if (countDestroy(state, state->playerB.x, state->playerB.y) > 0) {
                actionB = 'B';
            }
        }

        // [다오 행동 역추적 및 결정]
        if (has_other && !d_done) {
            if (!(targetD.x == state->playerD.x && targetD.y == state->playerD.y)) {
                Point curr = targetD;
                while (!(parentD[curr.x][curr.y].x == state->playerD.x && parentD[curr.x][curr.y].y == state->playerD.y)) {
                    curr = parentD[curr.x][curr.y];
                }
                for (int i = 0; i < 4; i++) {
                    if (state->playerD.x + dx[i] == curr.x && state->playerD.y + dy[i] == curr.y) {
                        actionD = dir_char[i];
                        state->playerD = curr;
                        break;
                    }
                }
            } else if (countDestroy(state, state->playerD.x, state->playerD.y) > 0) {
                actionD = 'B';
            }
        }

        // 2. 명령어 출력 조합 생성 및 콘솔 출력
        if (has_other) {
            // 2인용 포맷: 배찌 행동 + 다오 행동 (행동이 없으면 U로 벽에 헤딩하며 대기)
            printf("%c%c", actionB == '.' ? 'U' : actionB, actionD == '.' ? 'U' : actionD);
        } else {
            // 1인용 포맷: 배찌 행동만 순차 출력
            if (actionB != '.') printf("%c", actionB);
        }

        // 3. 폭탄 동시 폭발 처리 및 맵 동기화
        if (actionB == 'B') applyExplosion(state, state->playerB.x, state->playerB.y);
        if (actionD == 'B') applyExplosion(state, state->playerD.x, state->playerD.y);
    }
    printf("\n");
}

int main() {
    int row, col, players;
    int K, dummy;
    
    if (scanf("%d %d %d", &row, &col, &players) != 3) return 0;
    if (scanf("%d %d", &K, &dummy) != 2) return 0;

    GameState state;
    state.K = K;
    state.num_players = players;
    state.playerB = (Point){-1, -1};
    state.playerD = (Point){-1, -1};

    for (int i = 0; i < N; i++) {
        char line[100];
        if (scanf("%s", line) != 1) return 1;
        
        for (int j = 0; j < N; j++) {
            if (line[j] == '.') {
                state.map[i][j] = CELL_EMPTY;
            } else if (line[j] == '@') {
                state.map[i][j] = CELL_BLOCK;
            } else if (line[j] == 'X' || line[j] == '#') {
                state.map[i][j] = CELL_WALL;
            } else if (line[j] == 'B') {
                state.playerB.x = i;
                state.playerB.y = j;
                state.map[i][j] = CELL_EMPTY;
            } else if (line[j] == 'D') {
                state.playerD.x = i;
                state.playerD.y = j;
                state.map[i][j] = CELL_EMPTY;
            }
        }
    }

    solve(&state);
    return 0;
}