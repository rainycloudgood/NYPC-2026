#!/bin/bash
# 인스턴스 접속.  ./connect.sh            → 대화형 셸
#                 ./connect.sh "명령어"   → 한 줄 실행
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

IP="$(current_instance_ip)"
[[ -n "$IP" && "$IP" != "None" ]] || die "실행 중인 인스턴스가 없습니다. ./launch.sh 먼저."
[[ -f "$KEY_FILE" ]] || die "개인키가 없습니다: $KEY_FILE  (KEY_FILE 환경변수로 경로 지정 가능)"

SSH_OPTS=(-i "$KEY_FILE" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30)

if [[ $# -gt 0 ]]; then
    exec ssh "${SSH_OPTS[@]}" "ubuntu@$IP" "$@"
else
    echo "▶ ubuntu@$IP 접속"
    exec ssh "${SSH_OPTS[@]}" "ubuntu@$IP"
fi
