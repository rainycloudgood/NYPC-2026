#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  로컬 코드 → 인스턴스로 전송.  rsync 없이 tar+ssh 로 (Git Bash 호환)
#  기본은 oracle_hybrid + 공개입력만. 레포 전체는 ALL=1 ./sync.sh
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh

IP="$(current_instance_ip)"
[[ -n "$IP" && "$IP" != "None" ]] || die "실행 중인 인스턴스가 없습니다."
[[ -f "$KEY_FILE" ]] || die "개인키가 없습니다: $KEY_FILE"

REPO="$(cd .. && pwd)"
SSH_OPTS=(-i "$KEY_FILE" -o StrictHostKeyChecking=accept-new)

if [[ "${ALL:-0}" == "1" ]]; then
    echo "▶ 레포 전체 전송 (.git 제외)"
    PATHS=(.)
    EXCLUDES=(--exclude=.git --exclude='*.exe' --exclude='*.obj' --exclude=__pycache__ --exclude=final_eval)
else
    echo "▶ oracle_hybrid + 공개입력 전송"
    PATHS=(oracle_hybrid public_1_input.txt public_3_input.txt public_4_input.txt public1_offline_optimizer.cpp validate.py)
    EXCLUDES=(--exclude='*.exe' --exclude='*.obj' --exclude=__pycache__ --exclude=data1_experiments)
fi

tar -C "$REPO" -czf - "${EXCLUDES[@]}" "${PATHS[@]}" \
    | ssh "${SSH_OPTS[@]}" "ubuntu@$IP" \
        'mkdir -p ~/work && tar -C ~/work -xzf - && echo "  전송 완료:" && ls ~/work'

echo "✅ 완료 →  ~/work"
