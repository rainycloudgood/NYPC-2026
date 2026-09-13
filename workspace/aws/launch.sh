#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  인스턴스 시작
#    ./launch.sh              → 채점기와 동일 사양 (c7a.2xlarge)
#    ./launch.sh sweep        → 대량 탐색용 (c7a.8xlarge)
#    INSTANCE_TYPE=c7a.4xlarge ./launch.sh
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"
source ./config.sh
have_aws

case "${1:-}" in
    sweep) INSTANCE_TYPE="$TYPE_SWEEP" ;;   # 64 vCPU
    max)   INSTANCE_TYPE="$TYPE_MAX"   ;;   # 128 vCPU (할당량 상한)
    free)  INSTANCE_TYPE="$TYPE_FREE"  ;;   # 무료 t3.micro
esac

# ── 0. 사전검사 — 여기서 못 잡으면 "접속 안 되는 인스턴스에 과금"이 난다 ──
#    실측 위험(2026-08-15): 기본 KEY_NAME(nypc2026)이 도쿄에 실제로 존재해서,
#    당일 export 를 잊어도 launch 는 **성공한다**. 그런데 그 키의 .pem 은
#    대여 노트북에 없으므로 SSH 만 안 된다. 조용하고 비싼 실패다.
aws ec2 describe-key-pairs --region "$AWS_REGION" --key-names "$KEY_NAME"     >/dev/null 2>&1 || die "키페어 '$KEY_NAME' 이 $AWS_REGION 에 없습니다.
   당일 만든 이름을 쓰려면 aws/local.env 에  KEY_NAME=... / KEY_FILE=...  를 적으세요.
   (export 는 새 터미널에서 사라집니다)"

[[ -f "$KEY_FILE" ]] || die "개인키 파일이 없습니다: $KEY_FILE
   키페어 '$KEY_NAME' 은 AWS 에 있지만 이 PC 에 .pem 이 없으면 **접속이 불가능합니다.**
   띄워도 과금만 됩니다. aws/local.env 에서 KEY_FILE 을 실제 경로로 지정하세요."

echo "▶ 리전=$AWS_REGION  타입=$INSTANCE_TYPE  키=$KEY_NAME"

# ── 0. 이미 떠 있나? ────────────────────────────────────────────────
EXISTING="$(current_instance_id || true)"
if [[ -n "$EXISTING" && "$EXISTING" != "None" ]]; then
    echo "⚠️  이미 실행 중인 인스턴스가 있습니다: $EXISTING"
    echo "    접속: ./connect.sh      종료: ./teardown.sh"
    exit 0
fi

# ── 1. 자격증명 확인 ────────────────────────────────────────────────
aws sts get-caller-identity --region "$AWS_REGION" >/dev/null \
    || die "AWS 자격증명이 없습니다. 'aws configure' 를 먼저 실행하세요."

# ── 2. 이 리전에 해당 타입이 있는지 확인 ────────────────────────────
echo "▶ $INSTANCE_TYPE 가용성 확인..."
AVAIL="$(aws ec2 describe-instance-type-offerings --region "$AWS_REGION" \
    --location-type availability-zone \
    --filters "Name=instance-type,Values=$INSTANCE_TYPE" \
    --query 'InstanceTypeOfferings[].Location' --output text)"
if [[ -z "$AVAIL" ]]; then
    echo "❌ $AWS_REGION 에 $INSTANCE_TYPE 가 없습니다."
    echo "   대안 확인:"
    aws ec2 describe-instance-type-offerings --region "$AWS_REGION" \
        --filters "Name=instance-type,Values=c7a.*,c7i.*,c6a.*,c6i.*" \
        --query 'InstanceTypeOfferings[].InstanceType' --output text | tr '\t' '\n' | sort -u | head -20
    exit 1
fi
echo "  가용 AZ: $AVAIL"

# ── 3. Ubuntu 24.04 AMI 조회 (하드코딩 금지 — 항상 최신) ────────────
AMI="$(resolve_ami)"
[[ "$AMI" == ami-* ]] || die "AMI 조회 실패 (반환값: $AMI)"
if [[ "$AMI" == "$READY_AMI" ]]; then
    echo "▶ AMI: $AMI (준비된 이미지 — 툴체인 포함, 부팅 즉시 사용 가능)"
else
    echo "▶ AMI: $AMI (기본 Ubuntu 24.04 — 툴체인 설치에 2~4분)"
fi

# ── 4. 보안그룹 — SSH를 내 IP에서만 허용 ────────────────────────────
MYIP="$(curl -s --max-time 10 https://checkip.amazonaws.com || true)"
[[ -n "$MYIP" ]] || die "공인 IP 확인 실패 (네트워크 문제)"
MYIP="${MYIP//[$'\r\n ']/}"
echo "▶ 내 IP: $MYIP (여기서만 SSH 허용)"

SG_ID="$(aws ec2 describe-security-groups --region "$AWS_REGION" \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo None)"

if [[ "$SG_ID" == "None" || -z "$SG_ID" ]]; then
    echo "▶ 보안그룹 생성: $SG_NAME"
    SG_ID="$(aws ec2 create-security-group --region "$AWS_REGION" \
        --group-name "$SG_NAME" --description "NYPC 2026 work instance" \
        --query 'GroupId' --output text)"
fi

# 현재 IP 규칙 추가 (이미 있으면 무시). 대회장 WiFi에서는 IP가 다르므로
# 그때 ./allow-ip.sh 를 다시 돌려야 한다.
aws ec2 authorize-security-group-ingress --region "$AWS_REGION" \
    --group-id "$SG_ID" --protocol tcp --port 22 --cidr "${MYIP}/32" \
    >/dev/null 2>&1 || echo "  (규칙이 이미 있음)"

# ── 5. user-data 생성 ───────────────────────────────────────────────
# ⚠️ 로컬에서 export 한 변수는 인스턴스로 전달되지 않는다. user-data 안에
#    직접 주입해야 AUTO_SHUTDOWN_MIN 이 실제로 먹는다.
#    (경로는 상대경로로 — MSYS_NO_PATHCONV=1 이라 /tmp/... 는 aws.exe 가 못 읽는다)
UD=".user-data.gen.sh"
trap 'rm -f "$UD"' EXIT
{
    echo "#!/bin/bash"
    echo "export AUTO_SHUTDOWN_MIN=${AUTO_SHUTDOWN_MIN}"
    tail -n +2 user-data.sh
} > "$UD"

# ── 6. 시작 ─────────────────────────────────────────────────────────
echo "▶ 인스턴스 시작 중..."
IID="$(aws ec2 run-instances --region "$AWS_REGION" \
    --image-id "$AMI" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_GB,VolumeType=gp3,DeleteOnTermination=true}" \
    --user-data "fileb://$UD" \
    --instance-initiated-shutdown-behavior terminate \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TAG_NAME}]" \
    --query 'Instances[0].InstanceId' --output text)"

echo "  ID: $IID"
echo "▶ 실행 대기..."
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$IID"

IP="$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$IID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"

cat <<EOF

✅ 시작됨
   ID : $IID
   IP : $IP
   타입: $INSTANCE_TYPE

⏳ 부트스트랩(컴파일러 설치)에 2~4분 걸립니다.
   접속:  ./connect.sh
   코드 보내기: ./sync.sh
   ⚠️ 끝나면 반드시: ./teardown.sh

⏰ ${AUTO_SHUTDOWN_MIN}분 뒤 자동 종료됩니다(안전장치).
   shutdown 동작이 terminate 라서 자동 종료 = 인스턴스 삭제입니다.
EOF
