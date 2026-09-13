# NYPC 2026

Nexon Young Programmers Cup 2026 참가 기록 — Qualification Round 부터 Final Round 까지의
제출 코드, 실험 코드, 본선 준비 도구를 한곳에 모았습니다.

## 구성

```
NYPC-2026/
├── qualification/                    예선 공식 제출물
│   ├── seed-transport-challenge/     씨앗 운반 – 챌린지 (제출 57건, .py / .cpp)
│   ├── seed-transport-stepup/        씨앗 운반 – 스텝 업 (미션별 답안, subtask-N/)
│   └── bazzi-dao-cleanup-challenge/  배찌와 다오의 대청소 – 챌린지 (제출 3건)
├── final/                            본선 공식 제출물
│   └── superrookie/                  슈퍼루키 (제출 19건, .cpp)
└── workspace/                        작업 공간 (내부 상대경로 그대로 보존)
    ├── *.py, *.cpp                   예선 씨앗 운반 실험·탐색·검증 스크립트
    ├── oracle_hybrid/                예선 최종 오라클 + 본선 준비 도구와 문서
    └── aws/                          원격 병렬 스윕용 EC2 스크립트
```

제출물 파일 이름은 대회 플랫폼의 **제출 번호**입니다.

## 본선 준비 도구 (`workspace/oracle_hybrid/`)

| 파일 | 역할 |
|---|---|
| `run_batch.py` | 전 입력 × 전 파라미터 조합 병렬 실행. 입력별 승/무/패, 중앙 비용비, 최악 비용비 집계 |
| `gap.py` | 내 답과 하한의 격차를 항목별로 분해 |
| `terrain.py` | 국소 변이의 무효율·변화폭·개선율로 SA 적합성 판정 |
| `skeleton.cpp` | 시간 예산 기반 anytime 솔버 뼈대 (환경변수로 파라미터 주입) |
| `KICKOFF.md` 외 | 대회 당일 절차·체크리스트·인수인계 양식 |

도구 연동 규약: 솔버는 stdin → stdout, 지표는 stderr 에 `key=value`.

## 포함하지 않은 것

- **문제 원문, 채점 입력, 대회 제공 데이터** — 넥슨(NYPC) 자료이므로 재배포하지 않습니다.
- **본선 LLM 로그** — 문제 원문과 제공 데이터가 그대로 들어 있어 제외했습니다.

`workspace/` 의 스크립트 일부는 당시 로컬 경로(`C:\Users\<user>\Downloads` 등)나
공개 예제 입력을 전제로 작성되어 그대로는 실행되지 않을 수 있습니다.

## 회고

<!-- 대회 규정: 후기는 LLM 없이 직접 작성 -->
