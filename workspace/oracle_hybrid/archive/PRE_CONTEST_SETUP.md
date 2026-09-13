# 🔧 대회 전 준비 체크리스트 — **대여 기기 + 포터블 USB** 기준

> **전제 변경(2026-07-31)**: 노트북을 사지 않고 **주최측 대여 기기**를 사용한다.
> 준비·연습은 **현재 데스크탑(i5-9400F / 32GB)** 에서 하고, 대회장엔 **USB 하나**로 들어간다.

**주최측 확인 결과**
- OS: **윈도우** (작년 기준 추정)
- 관리자 권한: 있을 것으로 예상 (미확정)
- 개발도구 사전 설치: **불명** ← 최대 변수
- 사전 수령: ❌ 불가. 대신 **대회 시작 전 공통 세팅 시간**이 주어짐 ✅

> **핵심 방침: 기기에 아무것도 없다고 가정한다.**
> 관리자 권한이 있든 없든, **80명이 동시에 수 GB를 받는 상황**을 피하는 게 이득이다.
> 포터블 툴체인은 압축 해제 몇 분이면 끝난다.

---

## 1. USB 구성 (핵심 준비물)

- [ ] **MinGW-w64 포터블** (WinLibs 등 압축 해제형) ⭐ 최우선
  - [ ] ⚠️ 반드시 **POSIX threads** 빌드 — win32-threads 빌드엔 `<thread>` 가 없다
  - [ ] 집에서 미리 압축 풀어 `g++ --version` 확인
- [ ] **`seed_transport` 레포 통째로 (`.git` 포함)** — 오프라인에서도 커밋/롤백 가능
- [ ] **PortableGit** (압축 해제형, 선택)
- [ ] **Python embeddable / WinPython** (LP·검증 스크립트용, 선택)
- [ ] VS Code Portable (선택)
- [ ] 오프라인 문서: cppreference, STL, SciPy (백업용 — 현장 WiFi는 있음)
- [ ] ❌ **인증정보(토큰·비번) 절대 금지** — 현장 로그인. clone URL만 메모
- [ ] 대회 **직전에 다시 굽기** (그 사이 변경분 반영)

## 2. 집에서 미리 검증 (현재 데스크탑)

- [ ] **USB 포터블 MinGW만으로** 빌드되는지 확인 (MSVC를 PATH에서 뺀 상태로 테스트)
  ```bash
  export PATH="/d/portable/mingw64/bin:$PATH"   # 실제 경로로
  ./build.sh submission_oracle.cpp oracle
  SINGLE=1 ./build.sh submission_oracle.cpp oracle_st   # 1코어/구형툴체인 대응
  ```
- [ ] 채점기도 빌드: `./build.sh ../public1_offline_optimizer.cpp judge`
- [ ] **USB만 꽂은 상태**로 빌드→실행→채점 전 과정 리허설
- [ ] Claude Code 없이 **브라우저(claude.ai)만으로** 작업하는 흐름 한 번 체험

## 3. 당일 세팅 시간에 할 일 (순서대로)

1. **USB → 로컬 디스크로 복사** (⚠️ USB에서 직접 작업 금지 — 느리고 뽑히면 대참사)
2. MinGW `bin` 을 PATH에 추가 → `g++ --version` 확인
3. `./build.sh` 로 빌드 1회 성공 확인
4. **Claude Code 설치 시도** → 막히면 즉시 **브라우저 claude.ai** 로 전환 (여기서 시간 끌지 말 것)
5. 제출 사이트 접속 · 로그인 확인
6. (여유 되면) `gh auth login` → 대회 중 30~60분마다 커밋+push 백업

## 4. 물리 준비물

- [ ] **신분증** ← 없으면 참가 제한
- [ ] **파이널리스트 유니폼 티셔츠** (착용 후 입장)
- [ ] USB (+ 여분 1개 백업)
- [ ] 마우스·키보드 (익숙한 것 — 대여 기기 것이 안 맞을 수 있음)
- [ ] 대여 기기용 전원 어댑터 제공 여부 확인 / 멀티탭은 현장 제공
- [ ] 5시간 자리 지킬 준비 (물·간식) — 화장실 외 외출 불가

---

## ⚠️ 알아둘 함정 (준비 중 실제로 겪음)

| 함정 | 대응 |
|---|---|
| **배치파일은 CRLF 필수** — LF면 `'.bat' is not recognized` 같은 괴상한 에러 | `build.bat` 은 CRLF로 저장 (반영됨) |
| **MSVC는 성공해도 exit code가 어긋남** | 빌드 성공 판정을 **파일 존재**로 (build.bat에 반영됨) |
| **`.exe` 잠김** → 낡은 바이너리를 검증하는 사고 (2회 발생) | 빌드 후 **타임스탬프 확인** |
| **PowerShell `>` 리다이렉션이 BOM 추가** → 출력 파일이 깨져 채점 폭발 | 출력은 bash 리다이렉션 또는 프로그램 내부에서 |
| bash에서 `cmd //c` 로 MSVC 호출 시 경로 오류 | MSVC는 PowerShell에서 `build.bat` 사용 |
| MSVC의 한글 주석 CP949 오독 | `/utf-8` 플래그 (g++는 불필요) |
| **exFAT USB에서 git이 "dubious ownership"으로 거부** | USB에서 직접 작업하지 말고 **로컬 디스크로 복사**. 그래도 뜨면 `git config --global --add safe.directory '*'` |
| 🔥 **Git Bash(MSYS)가 `/` 로 시작하는 인자를 윈도우 경로로 자동변환** — `/aws/service/...` → `C:/Program Files/Git/aws/service/...` 로 바뀌어 AMI 조회가 조용히 실패 | `export MSYS_NO_PATHCONV=1` + `MSYS2_ARG_CONV_EXCL='*'` (`aws/config.sh` 에 반영). `/dev/sda1` 같은 값도 같은 위험 |
| 🔥 **파이썬 `shlex.split()` 이 윈도우 경로의 `\` 를 이스케이프로 먹음** (`C:\Users\x` → `C:Usersx`). 채점기가 없는 파일을 열고 **빈 입력으로 읽은 뒤 exit 0 으로 조용히 틀린 결과**를 냄 | 윈도우에선 `shlex.split(s, posix=False)`. `run_batch.py` 의 `split_cmd()` 에 반영됨. **크래시가 아니라 조용히 틀리는 유형이라 가장 위험** |

## 빌드 도구 (레포에 포함)

| 파일 | 용도 |
|---|---|
| `build.sh` | g++/clang++ 용 (포터블 MinGW 전제). `SINGLE=1` 로 단일스레드 |
| `build.bat` | MSVC 용 (PowerShell/cmd 에서). 3번째 인자로 `/DSINGLE_THREAD` |

**`-DSINGLE_THREAD`**: `<thread>` 의존을 제거한다. **채점은 1코어(스레드 시간 합산)이므로 제출본은 이쪽이 정답**이고, `<thread>` 없는 구형 MinGW에서도 빌드된다.
*검증됨: 멀티/단일 스레드 빌드가 공개1에서 동일 출력(cost 15,406), 26s vs 62s.*
⚠️ 이 **62s 는 낡은 수치**다. 포터블 g++ 16.1.0 으로 다시 재니 **42.3s**(2026-08-05).
시간 환산에 이 값을 쓰지 말 것 — 정정된 배율은 `../aws/README.md` §4.5.

## 우선순위

1. **USB 포터블 툴체인 구성 + 집에서 검증** ← 사실상 전부
2. 물리 준비물 (신분증·유니폼)
3. (선택) 얇은 스켈레톤 150줄
4. ~~노트북 구매~~ / ~~풀 하네스~~ — 불필요

> 상세 전략: `FINAL_ROUND_STRATEGY.md` / 당일 진행: `CONTEST_DAY_CHECKLIST.md`
