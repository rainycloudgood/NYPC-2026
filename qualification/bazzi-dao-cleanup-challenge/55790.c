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
    Point playerB; // 배찌 위치
    Point playerD; // 다오 위치
    int K;
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

// 폭탄 파괴 개수 예측 함수 (상대방 위치는 고려 안 함)
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

// 단일 캐릭터용 BFS 및 최적 목표 탐색 함수
// 다른 캐릭터의 위치를 '장애물'로 인식하여 겹치지 않게 만듭니다.
Point findBestTarget(GameState* state, Point self, Point other, int dist[N][N], Point parent[N][N]) {
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
                // 빈 칸이고, 방문 안 했고, '상대방 캐릭터 위치가 아닌 곳'만 지나감
                if (state->map[nx][ny] == CELL_EMPTY && dist[nx][ny] == -1) {
                    if (!(nx == other.x && ny == other.y)) {
                        dist[nx][ny] = dist[curr.x][curr.y] + 1;
                        parent[nx][ny] = curr;
                        push(&q, (Point){nx, ny});
                    }
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

                int score = (destroy_cnt * 20) - dist[i][j];
                if (score > best_score) {
                    best_score = score;
                    target = (Point){i, j};
                }
            }
        }
    }
    return target;
}

// 실제 맵에 폭탄 터뜨리기
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

        // 1. 배찌와 다오 각자의 시점에서 가장 좋은 목표 칸 찾기
        Point targetB = findBestTarget(state, state->playerB, state->playerD, distB, parentB);
        Point targetD = findBestTarget(state, state->playerD, state->playerB, distD, parentD);

        // 둘 다 더 이상 깰 블록이 없다면 종료
        if (targetB.x == state->playerB.x && targetB.y == state->playerB.y && countDestroy(state, targetB.x, targetB.y) == 0 &&
            targetD.x == state->playerD.x && targetD.y == state->playerD.y && countDestroy(state, targetD.x, targetD.y) == 0) {
            break;
        }

        // 2. 이번 턴에 행할 배찌와 다오의 Action 결정하기
        char actionB = '.';
        char actionD = '.';

        // [배찌 Action 결정]
        if (!(targetB.x == state->playerB.x && targetB.y == state->playerB.y)) {
            // 목적지가 멀다면 첫 발걸음 방향 구하기
            Point curr = targetB;
            while (!(parentB[curr.x][curr.y].x == state->playerB.x && parentB[curr.x][curr.y].y == state->playerB.y)) {
                curr = parentB[curr.x][curr.y];
            }
            for (int i = 0; i < 4; i++) {
                if (state->playerB.x + dx[i] == curr.x && state->playerB.y + dy[i] == curr.y) {
                    actionB = dir_char[i];
                    state->playerB = curr; // 위치 갱신
                    break;
                }
            }
        } else if (countDestroy(state, state->playerB.x, state->playerB.y) > 0) {
            // 목적지에 도착했다면 폭탄 설치
            actionB = 'B';
        }

        // [다오 Action 결정]
        if (!(targetD.x == state->playerD.x && targetD.y == state->playerD.y)) {
            Point curr = targetD;
            while (!(parentD[curr.x][curr.y].x == state->playerD.x && parentD[curr.x][curr.y].y == state->playerD.y)) {
                curr = parentD[curr.x][curr.y];
            }
            for (int i = 0; i < 4; i++) {
                if (state->playerD.x + dx[i] == curr.x && state->playerD.y + dy[i] == curr.y) {
                    actionD = dir_char[i];
                    state->playerD = curr; // 위치 갱신
                    break;
                }
            }
        } else if (countDestroy(state, state->playerD.x, state->playerD.y) > 0) {
            actionD = 'B';
        }

        // 아무도 할 일이 없다면(움직이지도 않고 폭탄도 안 놓음) 교착 방지를 위해 루프 탈출
        if (actionB == '.' && actionD == '.') break;

        // 3. 명령어 출력 (배찌행동 + 다오행동 순서로 항상 짝을 맞춤)
        // 만약 가만히 서 있어야 한다면 대기 명령(예: '.' 이나 문제의 무동작 포맷) 출력
        // 문제 조건에 맞춰 무동작 시의 문자를 조절해야 할 수 있습니다. 
        printf("%c%c", actionB == '.' ? 'U' : actionB, actionD == '.' ? 'U' : actionD);

        // 4. 폭탄이 설치되었다면 맵 갱신
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