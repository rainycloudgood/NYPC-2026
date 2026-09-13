#!/usr/bin/env python3
"""지형 판별 — SA 가 먹히는 문제인가를 **숫자로** 판정한다.  (12:00~12:30 구간)

왜 이 파일이 미리 있는가
────────────────────────
당일에 짤 수 없는 건 변이 연산자뿐이고 그건 10줄이다. 미리 못 박아야 하는 건
**판정 임계값**이다. 기존 기준("대부분 작게 변함 / 자주 폭발")은 숫자가 아니라,
12:30 의 압박 속에서 원하는 답 쪽으로 기운다. 리허설에서 직관이 5/5 로 틀렸던
것과 같은 실패 모드다. 이해관계가 없는 지금 정해두고, 당일엔 읽기만 한다.

당일 채울 것 — 아래 ★ 세 함수뿐
────────────────────────
    load(path)  /  dump(sol, path)  /  mutate(sol, rng)

사용법
────────────────────────
    python terrain.py --input in.txt --base sol_good.txt \
        --judge "./judge.exe {input} {output}" --trials 200

    # 최대화 문제면 반드시
    python terrain.py ... --maximize
"""
import argparse
import os
import random
import re
import shlex
import statistics
import subprocess
import sys
import tempfile

# 🔥 윈도우 콘솔은 기본 CP949 라 ─ ⚠ ★ 같은 문자에서 UnicodeEncodeError 로 **죽는다**.
#    출력 한 줄 때문에 판정 결과를 통째로 잃는다. (2026-08-15 실측으로 발견)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VERSION = "2026-08-15a"   # 낡은 사본을 쓰면 배너로 바로 드러난다

# ════════════════════════════════════════════════════════════════════
#  ★ 당일 채울 곳 — 여기 세 개가 전부다
# ════════════════════════════════════════════════════════════════════

def load(path):
    """해 파일 → 파이썬 객체. 리스트/딕트 뭐든 mutate 가 다룰 수 있으면 된다."""
    return open(path).read().split("\n")


def dump(sol, path):
    """파이썬 객체 → 해 파일 (채점기가 읽을 형식 그대로)."""
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(sol))


def mutate(sol, rng):
    """★ 1-변이. **가장 작은 국소 변경 하나**를 가한 새 해를 돌려준다.

    이게 이 판정의 전부다. '작다'의 기준이 곧 SA 가 쓸 이웃 구조가 된다.
    변이가 불가능하면 None 을 돌려준다(별도 집계됨).

    ⚠️ 여기에 수리(repair)를 넣지 말 것. 날것의 무효율을 봐야 판정이 된다.
       수리를 붙일지 말지는 판정 결과를 보고 정한다.
    """
    raise NotImplementedError("mutate() 를 채우세요 — 이 파일의 유일한 당일 작업")


# ════════════════════════════════════════════════════════════════════
#  아래는 완성됨 — 손대지 않는다
# ════════════════════════════════════════════════════════════════════

# 판정 임계값 ★ 사전 확정 (2026-08-15). 당일에 바꾸지 말 것.
# ⚠️ 이 숫자들은 이론값이 아니라 **사전 약속**이다. 정밀해서가 아니라
#    당일에 흔들리지 않기 위해 존재한다. 뒤집으려면 아래 규율을 따른다.
TH_INVALID_OK   = 0.20   # 무효율 이하 → SA 쪽
TH_INVALID_BAD  = 0.40   # 무효율 이상 → SA 부적합 (대부분의 시도를 버리게 됨)
TH_DELTA_OK     = 0.10   # |Δ|/기준 중앙값 이하 → 지형이 매끄럽다
TH_DELTA_BAD    = 0.25   # 이상 → 거칠다. 온도 스케줄이 의미를 잃는다
TH_IMPROVE_MIN  = 0.01   # 개선 이웃 비율이 이 미만이면 이웃 구조가 무의미

KV = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=(-?[0-9]+(?:\.[0-9]+)?)\b")
KV_STR = re.compile(r"(err[a-z_]*|reason|status)=([A-Za-z_][A-Za-z0-9_]*)")


def split_cmd(s):
    """윈도우에서 posix=True 로 쪼개면 백슬래시가 먹혀 경로가 깨진다."""
    if os.name == "nt":
        return [t[1:-1] if len(t) > 1 and t[0] == t[-1] == '"' else t
                for t in shlex.split(s, posix=False)]
    return shlex.split(s)


def judge(cmd_tpl, inp, out, metric, timeout):
    """채점기 실행 → (점수, 실패사유). 실패면 점수가 None."""
    cmd = cmd_tpl.replace("{input}", inp).replace("{output}", out)
    try:
        p = subprocess.run(split_cmd(cmd), capture_output=True, text=True,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    blob = (p.stdout or "") + "\n" + (p.stderr or "")
    if p.returncode != 0:
        m = KV_STR.search(blob)
        return None, (m.group(2) if m else f"exit{p.returncode}")
    kv = {k: v for k, v in KV.findall(blob)}
    if metric not in kv:
        m = KV_STR.search(blob)
        return None, (m.group(2) if m else f"no_{metric}")
    return float(kv[metric]), None


def verdict(inv_rate, dmed, imp_rate):
    """★ 사전 확정된 규칙. 사람이 히스토그램을 보고 감으로 정하지 않는다."""
    reasons = []
    if inv_rate >= TH_INVALID_BAD:
        reasons.append(f"무효율 {inv_rate:.0%} ≥ {TH_INVALID_BAD:.0%} "
                       f"— SA 가 시도 대부분을 버린다")
    if dmed >= TH_DELTA_BAD:
        reasons.append(f"|Δ| 중앙값 {dmed:.0%} ≥ {TH_DELTA_BAD:.0%} "
                       f"— 온도 스케줄이 의미를 잃는다")
    if reasons:
        return "구성 + 오라클", reasons

    if inv_rate < TH_INVALID_OK and dmed < TH_DELTA_OK:
        if imp_rate < TH_IMPROVE_MIN:
            return "구성 + 오라클", [
                f"지형은 매끄러우나 개선 이웃이 {imp_rate:.1%} 뿐 "
                f"— 이웃 구조가 무의미(랜덤 재시작과 차이 없음)"]
        return "SA", [f"무효율 {inv_rate:.0%} · |Δ| 중앙값 {dmed:.0%} — 둘 다 안전 구간"]

    return "구성 + 오라클 (회색지대 → 안전한 쪽)", [
        f"무효율 {inv_rate:.0%} · |Δ| 중앙값 {dmed:.0%} — 어느 쪽도 명확하지 않다",
        "SA 를 원하면 변이에 **수리(repair)** 를 붙여 무효율을 낮추고 재측정할 것",
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="문제 입력 파일")
    ap.add_argument("--base", required=True, help="기준 해 파일 (baseline 제출본)")
    ap.add_argument("--judge", required=True,
                    help="채점 명령 템플릿. {input} {output} 자리표시자")
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--metric", default="cost", help="채점기 출력의 key=value 키 이름")
    ap.add_argument("--maximize", action="store_true",
                    help="⚠️ 최대화 문제면 필수. 없으면 개선/악화를 반대로 센다")
    ap.add_argument("--seed", type=int, default=12345, help="고정 seed — 재현 가능해야 한다")
    ap.add_argument("--timeout", type=float, default=60)
    args = ap.parse_args()

    print(f"[terrain {VERSION}] {'클수록 좋음' if args.maximize else '작을수록 좋음'}"
          f" · 변이 {args.trials}회 · seed={args.seed}")

    base_score, err = judge(args.judge, args.input, args.base, args.metric, args.timeout)
    if base_score is None:
        sys.exit(f"❌ 기준 해가 채점되지 않는다 ({err}). 이것부터 고칠 것.")
    print(f"기준 해 {args.metric} = {base_score:g}\n")

    sol = load(args.base)
    rng = random.Random(args.seed)
    tmpd = tempfile.mkdtemp(prefix="terrain_")

    deltas, n_invalid, n_nomut, n_improve = [], 0, 0, 0
    fail_kinds = {}
    for i in range(args.trials):
        m = mutate(sol, rng)
        if m is None:
            n_nomut += 1
            continue
        path = os.path.join(tmpd, f"m{i:05d}.txt")
        dump(m, path)
        s, err = judge(args.judge, args.input, path, args.metric, args.timeout)
        os.unlink(path)
        if s is None:
            n_invalid += 1
            fail_kinds[err] = fail_kinds.get(err, 0) + 1
            continue
        deltas.append(abs(s - base_score) / max(abs(base_score), 1e-9))
        if (s > base_score) if args.maximize else (s < base_score):
            n_improve += 1

    n_eval = len(deltas)
    n_tried = args.trials - n_nomut
    if n_tried == 0:
        sys.exit("❌ 변이가 한 번도 생성되지 않았다. mutate() 를 확인할 것.")
    if n_eval == 0:
        print(f"무효율 100% ({n_invalid}/{n_tried}) — 실패 사유: {fail_kinds}")
        sys.exit("판정: 구성 + 오라클. 이웃이 전부 무효라 SA 가 움직일 수 없다.")

    inv_rate = n_invalid / n_tried
    imp_rate = n_improve / n_tried
    dmed = statistics.median(deltas)
    d90 = sorted(deltas)[int(0.9 * (n_eval - 1))]

    print(f"  변이 생성 실패    {n_nomut}")
    print(f"  무효 이웃         {n_invalid}/{n_tried}  = {inv_rate:.0%}"
          + (f"   사유: {fail_kinds}" if fail_kinds else ""))
    print(f"  개선 이웃         {n_improve}/{n_tried}  = {imp_rate:.1%}")
    print(f"  |Δ|/기준 중앙값   {dmed:.1%}")
    print(f"  |Δ|/기준 90분위   {d90:.1%}"
          + ("    ⚠️ 중앙값의 3배 초과 — 꼬리가 두껍다"
             if d90 > 3 * max(dmed, 1e-9) else ""))

    route, reasons = verdict(inv_rate, dmed, imp_rate)
    print(f"\n{'='*56}\n  판정:  {route}\n{'='*56}")
    for r in reasons:
        print(f"   · {r}")

    print("\n  ⚠️ 이 판정을 뒤집으려면 **왜 임계값이 이 문제에 안 맞는지**를 한 줄로")
    print("     적을 수 있어야 한다. 적히지 않으면 그건 근거가 아니라 희망이다.")
    print("     (임계값은 이해관계가 없던 2026-08-15 에 사전 확정한 값이다)")
    print("  ⚠️ 노선은 한 번 정하면 되돌리지 않는다.")


if __name__ == "__main__":
    main()
