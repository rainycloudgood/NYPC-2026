#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  EC2 부트스트랩 (user-data) — 인스턴스 첫 부팅 시 1회 실행
#  목표: 채점 환경(Ubuntu 24.04 / g++)과 동일한 작업 환경을 자동 구성
#  로그: /var/log/cloud-init-output.log
# ─────────────────────────────────────────────────────────────────────
set -eux

# ── 0. 폭주 방지: 지정 시간 뒤 자동 종료 ────────────────────────────
#    깜빡하고 켜둔 채 방치 → 과금 폭탄을 막는 최후 안전장치.
#    취소: sudo shutdown -c
AUTO_SHUTDOWN_MIN="${AUTO_SHUTDOWN_MIN:-480}"     # 기본 8시간
shutdown -h "+${AUTO_SHUTDOWN_MIN}" "auto-shutdown guard" || true

export DEBIAN_FRONTEND=noninteractive
apt-get update -y

# ── 1. 툴체인 (채점기와 동일 계열) ──────────────────────────────────
apt-get install -y --no-install-recommends \
    build-essential g++ gdb make cmake \
    git curl wget unzip zip \
    python3 python3-pip python3-venv \
    htop tmux jq time bc

# ── 2. 성능 확인용 (선택) ───────────────────────────────────────────
apt-get install -y --no-install-recommends linux-tools-common || true

# ── 3. 작업 디렉터리 ────────────────────────────────────────────────
install -d -o ubuntu -g ubuntu /home/ubuntu/work

# ── 4. 환경 요약을 남겨둔다 (접속하면 바로 확인 가능) ───────────────
{
    echo "=== NYPC 2026 작업 인스턴스 ==="
    echo "부팅:      $(date -Is)"
    # IMDSv2: 토큰을 먼저 받아야 메타데이터를 읽을 수 있다
    IMDS_TOK="$(curl -sX PUT --max-time 3 'http://169.254.169.254/latest/api/token' \
                 -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
    echo "인스턴스:  $(curl -s --max-time 3 -H "X-aws-ec2-metadata-token: $IMDS_TOK" \
                 http://169.254.169.254/latest/meta-data/instance-type || echo '?')"
    echo "vCPU:      $(nproc)"
    echo "메모리:    $(free -h | awk '/^Mem:/{print $2}')"
    echo "OS:        $(. /etc/os-release && echo "$PRETTY_NAME")"
    echo "g++:       $(g++ --version | head -1)"
    echo
    echo "!! 자동 종료가 ${AUTO_SHUTDOWN_MIN}분 뒤로 예약되어 있습니다."
    echo "   취소: sudo shutdown -c   /  확인: shutdown --show 2>/dev/null || true"
} > /home/ubuntu/ENVINFO.txt
chown ubuntu:ubuntu /home/ubuntu/ENVINFO.txt

# 로그인 시 자동 표시
echo 'cat ~/ENVINFO.txt' >> /home/ubuntu/.bashrc

touch /home/ubuntu/.bootstrap-done
chown ubuntu:ubuntu /home/ubuntu/.bootstrap-done
echo "BOOTSTRAP COMPLETE"
