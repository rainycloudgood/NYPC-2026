#!/bin/bash
# 인스턴스 → 로컬로 결과 회수.   ./fetch.sh  '~/work/results/*.csv'  [로컬디렉터리]
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

REMOTE="${1:-}"
[[ -n "$REMOTE" ]] || die "사용법: ./fetch.sh '~/work/*.csv' [로컬경로]"
DEST="${2:-./results}"

IP="$(current_instance_ip)"
[[ -n "$IP" && "$IP" != "None" ]] || die "실행 중인 인스턴스가 없습니다."

mkdir -p "$DEST"
scp -i "$KEY_FILE" -o StrictHostKeyChecking=accept-new \
    "ubuntu@$IP:$REMOTE" "$DEST"/
echo "✅ 회수 완료 → $DEST"
ls -la "$DEST"
