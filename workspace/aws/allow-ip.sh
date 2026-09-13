#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  현재 공인 IP를 보안그룹에 추가.
#  ★ 대회장 WiFi는 집과 IP가 다르다 → 대회장 도착하면 이걸 먼저 실행!
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh
have_aws

MYIP="$(curl -s --max-time 10 https://checkip.amazonaws.com)"
MYIP="${MYIP//[$'\r\n ']/}"
[[ -n "$MYIP" ]] || die "공인 IP 확인 실패"

SG_ID="$(aws ec2 describe-security-groups --region "$AWS_REGION" \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' --output text)"
[[ "$SG_ID" != "None" ]] || die "보안그룹 $SG_NAME 이 없습니다. ./launch.sh 를 먼저 실행하세요."

echo "▶ 현재 IP: $MYIP → $SG_NAME ($SG_ID) 에 SSH 허용"
aws ec2 authorize-security-group-ingress --region "$AWS_REGION" \
    --group-id "$SG_ID" --protocol tcp --port 22 --cidr "${MYIP}/32" \
    >/dev/null 2>&1 && echo "✅ 추가됨" || echo "✅ 이미 허용되어 있음"

echo
echo "현재 허용된 IP 목록:"
aws ec2 describe-security-groups --region "$AWS_REGION" --group-ids "$SG_ID" \
    --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp' --output text | tr '\t' '\n'
