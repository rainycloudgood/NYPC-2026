#!/bin/bash
# 지금 뭐가 켜져 있나 + 과금 위험 점검
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh
have_aws

echo "=== $AWS_REGION 의 실행 중 인스턴스 (전체) ==="
aws ec2 describe-instances --region "$AWS_REGION" \
    --filters "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name,IP:PublicIpAddress,Name:Tags[?Key==`Name`]|[0].Value,Launch:LaunchTime}' \
    --output table

echo
echo "※ 다른 리전에 켜둔 게 있으면 여기 안 보입니다. 전 리전 점검:"
echo "   for r in \$(aws ec2 describe-regions --query 'Regions[].RegionName' --output text); do"
echo "     echo \"-- \$r\"; aws ec2 describe-instances --region \$r \\"
echo "       --filters Name=instance-state-name,Values=running \\"
echo "       --query 'Reservations[].Instances[].InstanceId' --output text; done"
