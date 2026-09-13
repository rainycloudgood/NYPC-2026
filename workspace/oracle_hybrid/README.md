# oracle_hybrid — C++ exact-oracle + 하이브리드 제출본 (2026-07-15, opus 세션)

이 폴더는 2026-07-15 세션에서 새로 만든 파일만 모은 것이다.
상위 `seed_transport` 폴더의 기존 파일(v5·treegen·validate·public1 등)은 건드리지 않았다.

## 제출본 (핵심)

**`challenge_submission_hybrid.py`** — 실제 제출 진입점.
```
python challenge_submission_hybrid.py < input.txt > output.txt
```
동작: 입력마다 **v5와 C++ oracle을 모두 실행 → 두 격자를 채점 exe로 exact 평가 →
L=0 중 최저 Cost 출력**(동률 v5 우선). C<6은 comb 불가라 oracle 생략.
→ `min(v5, oracle)`이므로 **모든 입력에서 v5 이상(무회귀)**.

### 의존 파일 (상위 폴더에 있어야 함)
- `../challenge_submission_rating_v5_balanced.py`  (v5 baseline, 공개 known-case 격자 포함)
- `../public1_offline_optimizer.exe`               (공식 의미론 exact 채점기)
- `./cpp_oracle.exe`                               (이 폴더, comb 엔진)

즉 이 폴더를 통째로 옮기더라도 상위에 위 두 파일이 그대로 있어야 한다.

## C++ 오라클

- **`challenge_submission_cpp_oracle.cpp`** — 소스. whole(비트마스크 DP 안전 baseline)
  + parallel dyadic comb 후보를 스레드 병렬로 내장 시뮬 exact 평가 후 최저 선택.
- **`cpp_oracle.exe`** — 빌드 결과. `cpp_oracle.exe < input > output` 단독 실행 가능
  (단, 단독은 공개 격자·C5 안전후보가 없어 공개1·C5에서 v5보다 나쁨 → 반드시 하이브리드로 사용).
- 재빌드 (MSVC BuildTools, **`/utf-8` 필수**):
  ```
  cmd /c '"...\VC\Auxiliary\Build\vcvars64.bat" && cl /nologo /utf-8 /std:c++17 /O2 /EHsc ^
    /Fe:cpp_oracle.exe /Fo:cpp_oracle.obj challenge_submission_cpp_oracle.cpp'
  ```
- 튜닝 env: `ORACLE_STRIPS`(기본3), `ORACLE_SEEDS`(기본4), `ORACLE_STEPS`(기본30000),
  `ORACLE_LEAN=1`(depth{6,7,8}·cap{1.15,1.20,1.25}로 축소). 하이브리드는 STRIPS=2/LEAN=1/SEEDS=3 사용.

## 검증 도구

- **`compare_oracle_v5.py`** — 공식분포 케이스에서 v5/oracle/hybrid 비교.
  `python compare_oracle_v5.py <C> <n_per_band>`
- **`_hyb_smoke.py`** — C5~C10 하이브리드 end-to-end 점검.

## 검증 결과 요약 (2026-07-15)

- 공개: public1=15,406·public4=7,640(v5 유지), public3=6,392(oracle이 v5 10,840 개선). 회귀 0.
- 중간평가 sum 절감 vs v5: C5=0%(무회귀)·C6=−51%·C7=−52%·C8=−41%·C9=−40%·C10=−50%.
- 런타임: 입력당 v5(빠름)+oracle(≈35~60초). 오프라인 출력 생성엔 충분.

## data1_experiments/

공개 데이터1 offline 분석 실험물(E=0 정확분할 LP·버스빌더). 분석은 종료됐고
`public1_exact_flows.json`(데이터1 E=0 21유량)만 자산으로 보존. 스크립트는 상위
`seed_transport`의 treegen/validate/입력에 의존하므로 재실행하려면 그 폴더를
`sys.path`/작업경로에 둬야 한다.

## 남은 작업

- C5용 2-strip comb(마지막 미개선 구간), oracle 런타임 튜닝,
  (선택) v5 후보의 C++ 완전 이식으로 self-contained 단일 바이너리화.
