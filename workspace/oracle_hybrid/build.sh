#!/usr/bin/env bash
# 포터블 툴체인 우선 빌드 스크립트 (g++ / clang++).
#
#   ./build.sh <소스.cpp> [출력이름]
#   SINGLE=1 ./build.sh ...      # 단일 스레드 (채점은 1코어이므로 제출본은 이쪽)
#
# 대여 기기 + USB 포터블 MinGW 상황을 전제로 한다.
# MSVC로 빌드하려면 PowerShell에서 build.bat 를 쓸 것 (bash에서 cmd 경유는 경로 문제로 불안정).
set -u
SRC="${1:?usage: ./build.sh <source.cpp> [outname]}"
OUT="${2:-$(basename "${SRC%.*}")}"
DEF=""; [ "${SINGLE:-0}" = "1" ] && DEF="-DSINGLE_THREAD"
# ★ 공식 환경(Ubuntu 24.04·gcc 14.2.0)은 -std=gnu++20 이다. C++17은 선택지에 없다.
#   (공식 전체 명령: g++ -std=gnu++20 -O2 -DONLINE_JUDGE -DNYPC -Wall -Wextra
#                    -march=native -mtune=native -o main main.cpp)
#   -march=native 는 여기(로컬 대여 노트북)엔 넣지 않는다 — 채점기 CPU와 다르므로
#   의미가 없고 배율 측정에 잡음만 늘린다. AWS(EC2, 같은 CPU세대)에서만 재현할 것.
NATIVE=""; [ "${MARCH_NATIVE:-0}" = "1" ] && NATIVE="-march=native -mtune=native"

for CC in g++ clang++; do
  command -v "$CC" >/dev/null 2>&1 || continue
  echo "[build] $CC -std=gnu++20 ${DEF:+($DEF)} ${NATIVE:+($NATIVE)}"
  "$CC" -std=gnu++20 -O2 -pthread $DEF $NATIVE -o "$OUT" "$SRC" && { echo "[ok] -> $OUT"; exit 0; }
  echo "[fail] $CC 빌드 실패"; exit 1
done

cat <<'MSG'
[fail] g++/clang++ 를 찾지 못했습니다.

  USB 포터블 MinGW-w64 를 쓰는 경우:
    export PATH="/d/portable/mingw64/bin:$PATH"      # 실제 경로로 교체
    g++ --version                                    # 확인 후 재실행

  ⚠️ MinGW 는 반드시 **POSIX threads** 빌드를 받을 것 (win32-threads 빌드엔 <thread> 없음).
     그런 툴체인뿐이라면:  SINGLE=1 ./build.sh <소스>   로 스레드 없이 빌드.

  MSVC(현재 PC)로 빌드하려면 PowerShell 에서:  .\build.bat <소스.cpp> [출력이름]
MSG
exit 1
