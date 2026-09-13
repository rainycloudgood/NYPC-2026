#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

#define N 50

// 1. 상태 정의 및 구조체
typedef enum {
    CELL_EMPTY,   // '.' 이거나 원래 캐릭터가 있던 자리
    CELL_BLOCK,   // '@' (파괴 대상)
    CELL_WALL     // 'X' 또는 '#' (통과 불가능, 폭탄 막힘)
} CellType;

typedef struct {
    int x, y;
} Point;

typedef struct {
    CellType map[N][N];
    Point player;
    int K; // 폭탄 사거리
} GameState;

// BFS용 큐
typedef struct {
    Point data[N * N];
    int front, rear;
} Queue;

// 상하좌우 방향 정의
int dx[4] = {-1, 1, 0, 0};
int dy[4] = {0, 0, -1, 1};
char dir_char[4] = {'U', 'D', 'L', 'R'};

// 큐 함수들
void initQueue(Queue* q) { q->front = 0; q->rear = 0; }
bool isEmpty(Queue* q) { return q->front == q->rear; }
void push(Queue* q, Point p) { q->data[q->rear++] = p; }
Point pop(Queue* q) { return q->data[q->front++]; }

// 2. 폭탄 시뮬레이션 (사거리 K 반영)
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
                break; // 블록을 만나면 폭풍이 더 나아가지 못함
            }
        }
    }
    return count;
}

// 3. 메인 알고리즘 및 명령어 생성
void solve(GameState* state) {
    // 명령어들을 임시로 저장할 버퍼 (충분히 크게 잡음)
    char* total_commands = (char*)malloc(sizeof(char) * 1000000);
    int cmd_idx = 0;

    while (true) {
        int dist[N][N];
        Point parent[N][N];
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) dist[i][j] = -1;
        }

        // BFS 시작 (현재 배찌 위치 기준)
        Queue q;
        initQueue(&q);
        
        Point start = state->player;
        dist[start.x][start.y] = 0;
        parent[start.x][start.y] = start;
        push(&q, start);

        while (!isEmpty(&q)) {
            Point curr = pop(&q);

            for (int i = 0; i < 4; i++) {
                int nx = curr.x + dx[i];
                int ny = curr.y + dy[i];

                if (nx >= 0 && nx < N && ny >= 0 && ny < N) {
                    // 빈 칸이고 아직 방문하지 않은 곳 이동
                    if (state->map[nx][ny] == CELL_EMPTY && dist[nx][ny] == -1) {
                        dist[nx][ny] = dist[curr.x][curr.y] + 1;
                        parent[nx][ny] = curr;
                        push(&q, (Point){nx, ny});
                    }
                }
            }
        }

        // 휴리스틱 평가 함수를 통한 최적의 목적지 선정
        int best_score = -999999;
        Point target = state->player;
        int target_destroy_cnt = 0;

        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                if (dist[i][j] != -1) { 
                    int destroy_cnt = countDestroy(state, i, j);
                    if (destroy_cnt == 0) continue;

                    // 가중치 공식: (부수는 개수 * 20) - 이동 거리
                    int score = (destroy_cnt * 20) - dist[i][j];

                    if (score > best_score) {
                        best_score = score;
                        target = (Point){i, j};
                        target_destroy_cnt = destroy_cnt;
                    }
                }
            }
        }

        // 더 이상 깰 블록이 없거나 갈 수 있는 곳이 없으면 탈출
        if (target_destroy_cnt == 0) {
            break; 
        }

        // 경로 복원 (역추적)
        char path[N * N];
        int path_len = 0;
        Point curr = target;

        while (!(curr.x == state->player.x && curr.y == state->player.y)) {
            Point p = parent[curr.x][curr.y];
            for (int i = 0; i < 4; i++) {
                if (p.x + dx[i] == curr.x && p.y + dy[i] == curr.y) {
                    path[path_len++] = dir_char[i];
                    break;
                }
            }
            curr = p;
        }

        // 정방향으로 버퍼에 이동 명령 저장
        for (int i = path_len - 1; i >= 0; i--) {
            total_commands[cmd_idx++] = path[i];
        }

        // 폭탄 설치 명령 'B' 저장
        total_commands[cmd_idx++] = 'B'; 

        // 맵 상태 갱신 (폭탄 폭발 시뮬레이션)
        for (int i = 0; i < 4; i++) {
            for (int len = 1; len <= state->K; len++) {
                int nx = target.x + dx[i] * len;
                int ny = target.y + dy[i] * len;

                if (nx < 0 || nx >= N || ny < 0 || ny >= N) break;
                if (state->map[nx][ny] == CELL_WALL) break;
                if (state->map[nx][ny] == CELL_BLOCK) {
                    state->map[nx][ny] = CELL_EMPTY; 
                    break;
                }
            }
        }

        // 플레이어 실제 이동
        state->player = target;
    }

    total_commands[cmd_idx] = '\0';
    
    // 최종 결과 출력
    printf("%s\n", total_commands);
    free(total_commands);
}

// 4. 입력 파싱 및 메인 함수
int main() {
    int row, col, players;
    int K, dummy;
    
    // 첫째 줄: 50 50 2
    if (scanf("%d %d %d", &row, &col, &players) != 3) return 0;
    // 둘째 줄: 1 2 (폭탄 사거리 K와 미공개 변수)
    if (scanf("%d %d", &K, &dummy) != 2) return 0;

    GameState state;
    state.K = K;

    // 맵 데이터 읽기
    for (int i = 0; i < N; i++) {
        char line[100];
        scanf("%s", line);
        for (int j = 0; j < N; j++) {
            if (line[j] == '.') {
                state.map[i][j] = CELL_EMPTY;
            } else if (line[j] == '@') {
                state.map[i][j] = CELL_BLOCK;
            } else if (line[j] == 'X' || line[j] == '#') {
                state.map[i][j] = CELL_WALL; // X와 # 둘 다 벽으로 인지
            } else if (line[j] == 'B') {
                // 배찌 발견 시 좌표 기억 후 빈칸 처리
                state.player.x = i;
                state.player.y = j;
                state.map[i][j] = CELL_EMPTY;
            } else if (line[j] == 'D') {
                // 1인용 코드이므로 다오('D') 자리는 일단 빈칸(벽이 아님)으로 처리해 둡니다.
                state.map[i][j] = CELL_EMPTY;
            }
        }
    }

    solve(&state);

    return 0;
}