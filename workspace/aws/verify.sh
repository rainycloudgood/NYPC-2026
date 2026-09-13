#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  인스턴스 리허설 — "채점 환경과 같은 곳에서 예선 결과가 재현되는가"
#    1) 제출본을 단일스레드(채점 조건)로 빌드
#    2) 공개1 실행 → 격자 생성 + 실행시간 측정
#    3) 공식 채점기로 비용 계산 → 15,406 인지 확인
#  선행: ./launch.sh && ./sync.sh
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

echo "▶ 인스턴스에서 검증 실행 (빌드 포함 2~3분)"
./connect.sh 'bash -s' <<'REMOTE'
set -euo pipefail
cd ~/work

echo "=== 환경 ==="
g++ --version | head -1
echo "vCPU: $(nproc)  /  $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-)"
echo

echo "=== 빌드 ==="
cd oracle_hybrid
chmod +x build.sh
SINGLE=1 ./build.sh submission_oracle.cpp oracle_st     # 제출 조건(1코어)
cd ..
g++ -std=c++17 -O2 -pthread -o judge public1_offline_optimizer.cpp
echo

echo "=== 공개1 실행 (단일스레드) ==="
START=$(date +%s.%N)
./oracle_hybrid/oracle_st < public_1_input.txt > grid_public1.txt
END=$(date +%s.%N)
ELAPSED=$(echo "$END - $START" | bc)
echo "실행시간: ${ELAPSED}s"
echo "출력 첫 줄(R): $(head -1 grid_public1.txt)"
echo

echo "=== 채점 (rounds=0 → 순수 평가) ==="
./judge public_1_input.txt grid_public1.txt /dev/null 0 0 2>/dev/null | head -3
REMOTE

cat <<'EOF'

─────────────────────────────────────────────
확인 포인트
  · 출력 첫 줄(R) = 20
  · START 줄의 cost = 15406   ← 윈도우 결과와 일치해야 함
  · L = 0
  · 실행시간 ← 이 값이 "채점기에서의 실제 시간". 로컬 시간과 비교해
    스켈레톤의 TIME_LIMIT 보정 계수를 정한다.
─────────────────────────────────────────────
EOF
