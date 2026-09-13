#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  인스턴스 종료(삭제) — 과금 정지
#  ⚠️ 인스턴스의 데이터는 사라집니다. 결과물은 미리 ./fetch.sh 로 회수하세요.
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh
have_aws

IDS="$(aws ec2 describe-instances --region "$AWS_REGION" \
    --filters "Name=tag:Name,Values=$TAG_NAME" \
              "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query 'Reservations[].Instances[].InstanceId' --output text)"

if [[ -z "$IDS" || "$IDS" == "None" ]]; then
    echo "✅ 실행 중인 인스턴스 없음 (과금 없음)"
    exit 0
fi

echo "다음 인스턴스를 삭제합니다: $IDS"
read -r -p "정말 삭제할까요? 데이터는 사라집니다 [y/N] " ans
[[ "$ans" == "y" || "$ans" == "Y" ]] || { echo "취소됨"; exit 1; }

aws ec2 terminate-instances --region "$AWS_REGION" --instance-ids $IDS \
    --query 'TerminatingInstances[].[InstanceId,CurrentState.Name]' --output text

echo "▶ 삭제 완료 대기..."
aws ec2 wait instance-terminated --region "$AWS_REGION" --instance-ids $IDS
echo "✅ 삭제 완료 — 과금 정지"
