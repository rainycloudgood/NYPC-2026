#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  공통 설정 — 다른 스크립트들이 source 한다.
#  ⚠️ 이 파일에 액세스 키를 절대 넣지 말 것. 키는 `aws configure` 로만.
# ─────────────────────────────────────────────────────────────────────

# 🔥 Git Bash(MSYS) 경로 자동변환 끄기 — 이거 없으면 조용히 틀린 인자가 들어간다.
#    `/aws/service/...` 가 `C:/Program Files/Git/aws/service/...` 로 바뀌어
#    AMI 조회가 실패했고, `/dev/sda1` 같은 값도 같은 위험이 있다.
#    aws CLI 에 윈도우 경로를 넘길 일이 없으므로 꺼도 안전하다.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

# 🔥 AWS CLI 가 파일을 읽을 때 쓰는 인코딩. 윈도우 기본(CP949)으로 읽으면
#    한글 주석이 든 user-data.sh 를 디코딩하지 못해 시작이 실패한다.
export AWS_CLI_FILE_ENCODING=UTF-8

# 🔑 당일 값은 여기 두면 **새 터미널에서도 유지된다.**
#    export 는 터미널을 새로 열면 사라진다 — 이것 때문에 조용히 기본값으로
#    돌아가 "접속 안 되는 인스턴스에 과금"이 나는 사고가 가능하다.
#    aws/local.env 를 만들어 두면 모든 스크립트가 자동으로 읽는다 (git 제외됨).
#      예)  KEY_NAME=nypc2026-final
#           KEY_FILE=$HOME/.ssh/nypc2026-final.pem
_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$_here/local.env" ]] && . "$_here/local.env"

# ⚠️ 리전: 도쿄. **서울(ap-northeast-2)에는 c7a 가 없다** (2026-08-05 확인).
#    채점기와 같은 CPU를 쓰려면 도쿄여야 한다. 서울을 고집한다면 m7a 를 쓸 것
#    (m7a 도 같은 AMD EPYC Genoa 3.7GHz — 램만 2배).
#    ※ 키페어·보안그룹은 리전별로 분리된다. 리전 바꾸면 새로 만들어야 함.
export AWS_REGION="${AWS_REGION:-ap-northeast-1}"

# 인스턴스 타입
#   TIMING : 채점기와 동일 사양. 시간제한 튜닝은 반드시 여기서.
#   SWEEP  : 대량 병렬 탐색용. 필요할 때만.
#   FREE   : 절차 연습·기능 검증용(프리티어). 버스터블이라 시간측정엔 부적합.
#   ※ C7a 는 SMT 가 꺼져 있어 **1 vCPU = 물리 코어 1개**다. 32 vCPU = 진짜 32코어.
#   ※ 도쿄 할당량 = **128 vCPU** (2026-08-05 증액 승인). c7a.32xlarge 까지 가능.
export TYPE_TIMING="${TYPE_TIMING:-c7a.2xlarge}"    # 8 vCPU  (채점기와 동일)
export TYPE_SWEEP="${TYPE_SWEEP:-c7a.16xlarge}"     # 64 vCPU — 기본 스윕
export TYPE_MAX="${TYPE_MAX:-c7a.32xlarge}"         # 128 vCPU — 할당량 상한
export TYPE_FREE="${TYPE_FREE:-t3.micro}"           # 무료 — 측정 결과는 ÷1.5 해서 환산

# 기본으로 띄울 타입
export INSTANCE_TYPE="${INSTANCE_TYPE:-$TYPE_TIMING}"

# 키페어 이름 (AWS 콘솔에서 만든 것과 동일해야 함)
export KEY_NAME="${KEY_NAME:-nypc2026}"

# 개인키 경로 (다운로드한 .pem) — 리전별로 다른 키다. 섞이지 않게 이름을 나눌 것.
#   서울: ~/.ssh/nypc2026.pem   /   도쿄: ~/.ssh/nypc2026-tokyo.pem
export KEY_FILE="${KEY_FILE:-$HOME/.ssh/nypc2026-tokyo.pem}"

# 리소스 이름표
export TAG_NAME="${TAG_NAME:-nypc2026}"
export SG_NAME="${SG_NAME:-nypc2026-sg}"

# 디스크 (GB) — 레포+툴체인이면 20GB로 충분
export VOLUME_GB="${VOLUME_GB:-20}"

# 자동 종료까지 분 (과금 안전장치)
export AUTO_SHUTDOWN_MIN="${AUTO_SHUTDOWN_MIN:-480}"

# Ubuntu 24.04 AMI — Canonical 공식 이미지를 EC2 API 로 직접 조회 (ID 하드코딩 금지).
#   SSM 파라미터 방식도 되지만 권한(ssm:GetParameters)이 하나 더 필요하고
#   경로가 `/` 로 시작해 MSYS 변환 사고가 나기 쉬워서 EC2 조회로 통일했다.
export CANONICAL_OWNER="099720109477"                                   # Canonical 공식 계정
export UBUNTU_AMI_PATTERN="ubuntu/images/hvm-ssd*/ubuntu-noble-24.04-amd64-server-*"

# ★ 미리 구워둔 이미지 — 툴체인·레포·run_batch 가 전부 들어 있어 부팅 즉시 작업 가능.
#   당일 g++ 설치(2~4분)를 건너뛴다. 기본 Ubuntu 로 띄우려면  BASE=1 ./launch.sh
export READY_AMI="${READY_AMI:-ami-05e1dddb66c14c6a7}"   # nypc2026-ready-20260805-1359 (도쿄)

# 쓸 AMI 를 정한다
resolve_ami() {
    if [[ "${BASE:-0}" != "1" && -n "$READY_AMI" ]]; then
        # 이미지가 실제로 살아 있는지 확인 후 사용 (삭제됐으면 기본 Ubuntu 로 폴백)
        if aws ec2 describe-images --region "$AWS_REGION" --image-ids "$READY_AMI" \
               --query 'Images[0].State' --output text 2>/dev/null | grep -q available; then
            echo "$READY_AMI"; return
        fi
        echo "⚠️  준비된 AMI($READY_AMI)를 찾을 수 없어 기본 Ubuntu 로 진행합니다." >&2
    fi
    aws ec2 describe-images --region "$AWS_REGION" --owners "$CANONICAL_OWNER" \
        --filters "Name=name,Values=$UBUNTU_AMI_PATTERN" "Name=state,Values=available" \
        --query 'reverse(sort_by(Images,&CreationDate))[0].ImageId' --output text
}

# ── 헬퍼 ─────────────────────────────────────────────────────────────
die() { echo "❌ $*" >&2; exit 1; }
have_aws() { command -v aws >/dev/null 2>&1 || die "aws CLI 가 없습니다. aws/README.md 1단계를 먼저 하세요."; }

# 🔑 CLI 없이도 돌아가게 하는 탈출구.
#    대여 기기엔 aws CLI 가 없고, 자격증명은 USB 에 담을 수 없다.
#    콘솔에서 인스턴스를 띄우고 **IP 만 넘겨주면** connect/sync/fetch 는 그대로 쓴다.
#      INSTANCE_IP=1.2.3.4 ./sync.sh
export INSTANCE_IP="${INSTANCE_IP:-}"

# 실행 중인 우리 인스턴스 ID 얻기
current_instance_id() {
    aws ec2 describe-instances --region "$AWS_REGION" \
        --filters "Name=tag:Name,Values=$TAG_NAME" \
                  "Name=instance-state-name,Values=pending,running" \
        --query 'Reservations[].Instances[0].InstanceId' --output text 2>/dev/null | head -1
}

current_instance_ip() {
    if [[ -n "$INSTANCE_IP" ]]; then echo "$INSTANCE_IP"; return; fi
    command -v aws >/dev/null 2>&1 || {
        echo "❌ aws CLI 도 없고 INSTANCE_IP 도 없습니다." >&2
        echo "   콘솔에서 퍼블릭 IP 를 확인해  INSTANCE_IP=1.2.3.4 $0  형태로 실행하세요." >&2
        return 1; }
    aws ec2 describe-instances --region "$AWS_REGION" \
        --filters "Name=tag:Name,Values=$TAG_NAME" \
                  "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[0].PublicIpAddress' --output text 2>/dev/null | head -1
}
