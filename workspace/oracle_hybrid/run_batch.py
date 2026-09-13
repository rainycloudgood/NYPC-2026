#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────
#  병렬 배치 러너 — 문제 비의존
#
#  하는 일:  솔버 × 입력들 × 파라미터 조합  을 코어 수만큼 병렬 실행하고
#            결과를 CSV 한 줄씩 모은다. 채점은 외부 바이너리에 위임한다.
#
#  왜 미리 만드나: exact 채점기는 문제 규칙에 100% 의존해서 사전 제작이
#  불가능하지만, "여러 설정으로 돌려 표로 모으기"는 문제와 무관하다.
#  32코어를 놀리지 않으려면 이게 있어야 하고, 당일 짜면 20~30분이 날아간다.
#
#  ── 규약 (이것만 지키면 어떤 문제든 붙는다) ─────────────────────────
#   · 솔버: stdin 으로 입력 → stdout 으로 답
#   · 파라미터: **환경변수**로 전달 (솔버가 getenv 로 읽는다)
#   · 채점기: `--judge` 템플릿. {input} {output} 자리표시자
#   · 지표 수집: 솔버 stderr + 채점기 출력에서 `key=value` 토큰을 전부 긁는다
#     → 예선 채점기의 `START cost=15406 E=10954 L=0` 형식이 그대로 붙는다
#     → skeleton.cpp 의 -DLOG 출력도 그대로 붙는다
#
#  ── 사용 예 ────────────────────────────────────────────────────────
#   # 파라미터 격자 없이 전 입력 1회씩
#   ./run_batch.py --solver ./sol --inputs inputs/ \
#       --judge "./judge {input} {output} /dev/null 0 0" --timeout 10
#
#   # 파라미터 스윕 (2 x 3 = 6조합 x 입력수)
#   ./run_batch.py --solver ./sol --inputs "inputs/*.txt" \
#       --params "MODE=fast,deep;K=1,2,4" --judge "./judge {input} {output}" \
#       --timeout 10 --rank-by cost
#
#   # ⚠️ 시간을 재는 게 목적이면 반드시 --jobs 1
#   #    (병렬로 돌리면 코어 경합 때문에 개별 실행시간이 왜곡된다)
#   ./run_batch.py --solver ./sol --inputs inputs/ --jobs 1
# ─────────────────────────────────────────────────────────────────────────
import argparse
import csv
import itertools
import json
import math
import os
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from pathlib import Path

# 🔥 윈도우 콘솔은 기본 CP949 라 ─ ⚠ ★ 같은 문자에서 UnicodeEncodeError 로 **죽는다**.
#    스윕을 다 돌린 뒤 요약을 찍다가 죽으면 결과를 통째로 잃는다. (2026-08-15 발견)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VERSION = "2026-08-24e"   # 낡은 사본(예: AMI 내장본)을 쓰면 배너로 바로 드러난다

KV = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=(-?[0-9]+(?:\.[0-9]+)?)\b")
_lock = threading.Lock()


def split_cmd(s):
    """명령 문자열을 인자 배열로.

    ⚠️ 윈도우에서 shlex.split() 을 그대로 쓰면 경로의 백슬래시를 **이스케이프로
       먹어버린다** (C:\\Users\\x -> C:Usersx). 그러면 채점기가 없는 파일을 열고
       빈 입력으로 읽은 뒤 **exit 0 으로 조용히 틀린 결과**를 내놓는다.
       실제로 겪은 사고라 posix=False 로 분기한다.
    """
    if os.name == "nt":
        return [t[1:-1] if len(t) > 1 and t[0] == t[-1] == '"' else t
                for t in shlex.split(s, posix=False)]
    return shlex.split(s)


KV_STR = re.compile(r"(err[a-z_]*|reason|status)=([A-Za-z_][A-Za-z0-9_]*)")


def harvest(text):
    """텍스트에서 key=value 토큰을 뽑는다. 문제 비의존 지표 수집.

    수치는 전부, 그리고 **실패 사유 계열(err*/reason)은 문자열도** 가져온다.
    숫자만 긁으면 `err=overlap` 같은 결정적 단서를 놓쳐 진단이 막힌다."""
    out = {}
    for k, v in KV.findall(text or ""):
        out[k] = float(v) if ("." in v) else int(v)
    for k, v in KV_STR.findall(text or ""):
        if k != "status":
            out[k] = v
    return out


def parse_params(spec):
    """'A=1,2;B=x,y'  ->  [{'A':'1','B':'x'}, {'A':'1','B':'y'}, ...]"""
    if not spec:
        return [{}]
    names, values = [], []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            sys.exit(f"[params] '이름=값1,값2' 형식이어야 합니다: {part!r}")
        name, vals = part.split("=", 1)
        names.append(name.strip())
        values.append([v.strip() for v in vals.split(",")])
    return [dict(zip(names, combo)) for combo in itertools.product(*values)]


def collect_inputs(patterns):
    files = []
    for p in patterns:
        if os.path.isdir(p):
            files += sorted(str(x) for x in Path(p).iterdir() if x.is_file())
        else:
            files += sorted(glob(p))
    if not files:
        sys.exit(f"[inputs] 입력을 찾지 못했습니다: {patterns}")
    return files


def find_gnu_time():
    """/usr/bin/time 이 있으면 CPU time·최대메모리를 정확히 잰다 (리눅스)."""
    for cand in ("/usr/bin/time", "/bin/time"):
        if os.path.exists(cand):
            try:
                r = subprocess.run([cand, "-f", "x=1", "true"],
                                   capture_output=True, timeout=5)
                if r.returncode == 0:
                    return cand
            except Exception:
                pass
    return None


def run_one(job, cfg):
    """한 건 실행 → 결과 dict. 예외를 밖으로 내보내지 않는다(한 건 실패로 전체가 죽으면 안 됨)."""
    jid, inp, params = job
    row = {"input": os.path.basename(inp)}
    row.update({f"p_{k}": v for k, v in params.items()})

    env = os.environ.copy()
    env.update({k: str(v) for k, v in params.items()})

    cmd = split_cmd(cfg.solver)
    if cfg.gnu_time:
        # 지표를 key=value 로 뽑아두면 아래 harvest 가 그대로 주워담는다
        cmd = [cfg.gnu_time, "-f",
               "t_elapsed=%e t_user=%U t_sys=%S maxrss_kb=%M"] + cmd

    outdir = Path(cfg.workdir)
    # ⚠️ 작업 인덱스를 반드시 넣을 것. 없으면 --repeat 로 같은 (입력,설정)이 동시에
    #    돌 때 **같은 출력 파일에 겹쳐 써서** 채점기가 쓰다 만 파일을 읽는다.
    #    (조용히 무효가 되는 유형 — 실제로 겪음)
    tag = f"{jid:05d}_{Path(inp).stem}__" + "_".join(f"{k}-{v}" for k, v in params.items())
    outfile = outdir / (tag[:150] + ".out")
    # 채점기가 자기 출력 경로를 인자로 받는 경우가 흔하다 → {tmp} 로 준다.
    # 고정 경로를 쓰면 병렬 실행끼리 덮어써서 결과가 뒤섞인다.
    tmpfile = outdir / (tag[:150] + ".jtmp")

    t0 = time.perf_counter()
    status, rc, serr = "OK", None, ""
    try:
        with open(inp, "rb") as fi, open(outfile, "wb") as fo:
            proc = subprocess.run(cmd, stdin=fi, stdout=fo, stderr=subprocess.PIPE,
                                  env=env, timeout=cfg.timeout)
        rc = proc.returncode
        serr = proc.stderr.decode("utf-8", "replace")
        if rc != 0:
            status = "RTE"
    except subprocess.TimeoutExpired:
        status = "TLE"
    except Exception as e:                       # 실행 자체가 안 된 경우
        status, serr = "ERROR", f"{type(e).__name__}: {e}"
    wall = time.perf_counter() - t0

    row["status"] = status
    row["exit"] = rc
    row["t_run_s"] = round(wall, 4)
    row.update(harvest(serr))                    # 솔버가 stderr 로 뱉은 지표
    # 실패했으면 사유를 반드시 남긴다 (없으면 당일 원인 찾느라 시간을 날린다)
    if status in ("ERROR", "RTE"):
        row["err"] = " ".join(serr.split())[-300:] or "(stderr 비어 있음)"

    if status == "OK" and outfile.stat().st_size == 0:
        row["status"] = status = "EMPTY"

    # ── 채점 ────────────────────────────────────────────────────────
    if cfg.judge and status == "OK":
        jcmd = cfg.judge.format(input=inp, output=str(outfile), tmp=str(tmpfile))
        try:
            jr = subprocess.run(split_cmd(jcmd), capture_output=True,
                                timeout=cfg.judge_timeout)
            jtxt = (jr.stdout + b"\n" + jr.stderr).decode("utf-8", "replace")
            row.update(harvest(jtxt))
            if jr.returncode != 0:
                row["status"] = "JUDGE_FAIL"
        except subprocess.TimeoutExpired:
            row["status"] = "JUDGE_TLE"
        except Exception as e:
            row["status"], row["judge_err"] = "JUDGE_ERR", str(e)

    if not cfg.keep:
        for f in (outfile, tmpfile):
            try:
                f.unlink()
            except OSError:
                pass

    # 진행상황 + 유실 방지용 즉시 기록
    with _lock:
        cfg.done[0] += 1
        cfg.jsonl.write(json.dumps(row, ensure_ascii=False) + "\n")
        cfg.jsonl.flush()
        bad = ""
        if row["status"] != "OK":
            bad = f"  <-- {row['status']}"
            if row.get("err"):
                bad += f"  {row['err'][:120]}"
        print(f"[{cfg.done[0]:>4}/{cfg.total}] {row['input']:<24} "
              f"{row.get('t_run_s',0):>7.2f}s{bad}", file=sys.stderr)
    return row


def summarize(rows, key, maximize=False):
    """파라미터 조합별 비교표 — '어느 설정이 제일 나은가'에 답하는 부분.

    ⚠️ 평균만 보면 **점수 스케일이 큰 입력에 지배**된다. 본선 채점은
       **입력별 상대평가**이므로 '입력마다 누가 이겼는가(승수)'가 본질에 가깝다.
       그래서 승수를 1순위, 평균을 참고치로 낸다.
    """
    sign = -1.0 if maximize else 1.0          # 내부적으로는 항상 "작을수록 좋음"으로 통일
    groups = {}
    for r in rows:
        pk = tuple(sorted((k, v) for k, v in r.items() if k.startswith("p_")))
        groups.setdefault(pk, []).append(r)

    # ── 입력별 head-to-head 승수 ─────────────────────────────────
    # ⚠️ --repeat 로 같은 (입력, 설정)이 여러 줄이면 그대로 세면 승수가 입력 수를
    #    넘어간다. 조합별로 **그 입력에서의 최선값 하나**로 접은 뒤 비교한다.
    wins = {pk: 0 for pk in groups}
    folded = {}                                  # (input, pk) -> 최선값
    for pk, rs in groups.items():
        for r in rs:
            if r["status"] == "OK" and key in r:
                k2 = (r["input"], pk)
                v = sign * r[key]
                if k2 not in folded or v < folded[k2]:
                    folded[k2] = v
    # 승수만 보면 "작은 승리 여러 번 vs 큰 패배 한 번"을 구분 못 한다.
    # 승/무/패를 나누고(동점은 무승부), 입력별 "그 입력 최선 대비 비용비"의
    # 중앙값·최악값을 같이 낸다 - 최악값이 크면 승수만으론 안 보이는 위험이 있다.
    draws = {pk: 0 for pk in groups}
    losses = {pk: 0 for pk in groups}
    ratios = {pk: [] for pk in groups}   # 이 설정값 / 그 입력의 최선값 (내부 부호기준, >=1)
    ratio_inputs = {pk: [] for pk in groups}  # ratios 와 같은 순서로 입력 이름 병기
    per_input = {}
    for (inp, pk), v in folded.items():
        per_input.setdefault(inp, []).append((v, pk))
    for inp, lst in per_input.items():
        best = min(v for v, _ in lst)
        n_best = sum(1 for v, _ in lst if v == best)
        for v, pk in lst:
            if v == best:
                (wins if n_best == 1 else draws)[pk] += 1
            else:
                losses[pk] += 1
            # ⚠️ v/best 를 그대로 쓰면 maximize 에서 부호가 뒤집혀 "나쁠수록 1 미만"이
            # 나온다(내부적으로 음수라서). real_* 로 되돌려 항상 "몇 배 나쁜가(>=1)"로 통일.
            real_v, real_best = sign * v, sign * best
            if maximize:
                ratios[pk].append(real_best / real_v if real_v != 0
                                   else (1.0 if real_best == 0 else math.inf))
            else:
                ratios[pk].append(real_v / real_best if real_best != 0
                                   else (1.0 if real_v == 0 else math.inf))
            ratio_inputs[pk].append(inp)

    print("\n" + "=" * 82, file=sys.stderr)
    print(f"파라미터 조합별 요약  (지표: {key}, {'클수록' if maximize else '작을수록'} 좋음"
          f" / 입력 {len(per_input)}개)", file=sys.stderr)
    print("=" * 82, file=sys.stderr)

    table = []
    for pk, rs in groups.items():
        ok = [r for r in rs if r["status"] == "OK"]
        vals = [r[key] for r in ok if key in r]
        r_sorted = sorted(ratios[pk])
        # 최악비를 낸 게 어느 입력인지 같이 붙여둔다 - 경고를 봐도 어디를 봐야
        # 할지 몰라 헤매는 걸 막는다.
        worst_at = None
        if ratios[pk]:
            wi = max(range(len(ratios[pk])), key=lambda x: ratios[pk][x])
            worst_at = ratio_inputs[pk][wi]
        table.append({
            "params": ", ".join(f"{k[2:]}={v}" for k, v in pk) or "(기본)",
            "n": len(rs), "ok": len(ok), "bad": len(rs) - len(ok),
            "win": wins[pk], "draw": draws[pk], "loss": losses[pk],
            "mean": statistics.fmean(vals) if vals else (-math.inf if maximize else math.inf),
            "best": (max(vals) if maximize else min(vals)) if vals
                    else (-math.inf if maximize else math.inf),
            "med_ratio": statistics.median(r_sorted) if r_sorted else math.inf,
            "worst_ratio": max(r_sorted) if r_sorted else math.inf,
            "worst_at": worst_at,
            "t_max": max((r.get("t_run_s", 0) for r in rs), default=0),
        })
    # ①무효 적은 순 ②승수 많은 순 ③평균. 상대평가에선 무효가 가장 비싸다.
    table.sort(key=lambda t: (t["bad"], -t["win"], sign * t["mean"]))

    w = max(len(t["params"]) for t in table)
    print(f"{'params':<{w}}  {'n':>4} {'ok':>4} {'bad':>4} {'승':>4} {'무':>4} {'패':>4} "
          f"{'mean('+key+')':>16} {'중앙비':>7} {'최악비':>7} {'t_max':>7}", file=sys.stderr)
    for t in table:
        print(f"{t['params']:<{w}}  {t['n']:>4} {t['ok']:>4} {t['bad']:>4} "
              f"{t['win']:>4} {t['draw']:>4} {t['loss']:>4} "
              f"{t['mean']:>16.2f} {t['med_ratio']:>6.2f}x {t['worst_ratio']:>6.2f}x "
              f"{t['t_max']:>6.2f}s", file=sys.stderr)
    if table and table[0]["bad"] == 0:
        top = table[0]
        print(f"\n★ 최선: {top['params']}  "
              f"(입력 {top['win']}/{len(per_input)} 승, 무{top['draw']} 패{top['loss']})",
              file=sys.stderr)
        if top["worst_ratio"] > 1.5:
            print(f"   ⚠️ 이 설정의 최악 비용비 {top['worst_ratio']:.2f}x"
                  f" (입력: {top['worst_at']}) - 이기는 입력에선 이기지만, 여기서 크게 진다."
                  " 승수만 보고 고르면 놓치는 부분이다. 이 입력을 gap.py/terrain.py 로"
                  " 따로 확인할 것.", file=sys.stderr)
    else:
        print("\n⚠️ 모든 조합에 무효가 있습니다. 상대평가에서 무효는 그 입력 전손 -"
              " 점수보다 먼저 해결할 것.", file=sys.stderr)


def main():
    # 윈도우 콘솔이 CP949 라 한글이 깨진다 → UTF-8 로 고정 (대여 기기 대비)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(
        description="병렬 배치 러너 (문제 비의존)",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solver", required=True, help="솔버 실행 명령 (stdin→stdout)")
    ap.add_argument("--inputs", required=True, nargs="+", help="입력 디렉터리 또는 glob")
    ap.add_argument("--judge", default="",
                    help="채점 명령 템플릿. {input}=입력 {output}=솔버출력 "
                         "{tmp}=이 실행 전용 임시경로(채점기가 쓰기용 인자를 요구할 때)")
    ap.add_argument("--params", default="", help="'A=1,2;B=x,y' 형식 파라미터 격자(환경변수로 전달)")
    ap.add_argument("--timeout", type=float, default=60, help="실행당 제한(초). 초과 시 TLE")
    ap.add_argument("--judge-timeout", type=float, default=120)
    ap.add_argument("--jobs", type=int, default=0, help="병렬도. 0=코어 수. ⚠️ 시간 측정 시엔 1")
    ap.add_argument("--repeat", type=int, default=1, help="같은 조합 반복 횟수(편차 확인용)")
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--rank-by", default="cost", help="요약 기준 지표명")
    ap.add_argument("--maximize", action="store_true",
                    help="지표가 **클수록 좋은** 문제일 때 (기본은 작을수록 좋음). "
                         "빠뜨리면 정반대 설정을 최선으로 고른다")
    ap.add_argument("--keep", action="store_true", help="솔버 출력 파일 보존")
    cfg = ap.parse_args()

    cfg.jobs = cfg.jobs or (os.cpu_count() or 1)
    cfg.gnu_time = find_gnu_time()
    inputs = collect_inputs(cfg.inputs)
    grid = parse_params(cfg.params)

    jobs = [(n, i, p) for n, (p, i, _) in enumerate(
        (p, i, k) for p in grid for i in inputs for k in range(cfg.repeat))]
    cfg.total, cfg.done = len(jobs), [0]

    print(f"[run_batch {VERSION}] 입력 {len(inputs)}개 × 조합 {len(grid)}개 × 반복 {cfg.repeat}"
          f" = {cfg.total}건 / 병렬 {cfg.jobs}"
          f" / CPU계측 {'ON' if cfg.gnu_time else 'OFF(벽시계만)'}", file=sys.stderr)
    if cfg.jobs > 1:
        print("⚠️ 병렬 실행 중엔 개별 t_run_s 가 코어 경합으로 부풀 수 있습니다."
              " 시간을 재려면 --jobs 1.", file=sys.stderr)

    workdir = tempfile.mkdtemp(prefix="batch_")
    cfg.workdir = workdir
    jsonl_path = str(Path(cfg.out).with_suffix(".jsonl"))

    t0 = time.perf_counter()
    rows = []
    with open(jsonl_path, "w", encoding="utf-8") as jf:
        cfg.jsonl = jf
        try:
            with ThreadPoolExecutor(max_workers=cfg.jobs) as ex:
                for r in ex.map(lambda j: run_one(j, cfg), jobs):
                    rows.append(r)
        except KeyboardInterrupt:
            print("\n중단됨 — 여기까지의 결과는 "
                  f"{jsonl_path} 에 남아 있습니다.", file=sys.stderr)

    # CSV 는 전체 키의 합집합으로 마지막에 쓴다 (지표 이름이 문제마다 다르므로)
    if rows:
        cols, seen = [], set()
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    cols.append(k)
        with open(cfg.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

        elapsed = time.perf_counter() - t0
        nbad = sum(1 for r in rows if r["status"] != "OK")
        print(f"\n완료 {len(rows)}건 / 무효·실패 {nbad}건 / {elapsed:.1f}s"
              f"  →  {cfg.out}", file=sys.stderr)
        if any(cfg.rank_by in r for r in rows):
            summarize(rows, cfg.rank_by, cfg.maximize)
        else:
            print(f"(요약 생략 — 지표 '{cfg.rank_by}' 가 결과에 없습니다. "
                  f"--rank-by 로 지정하세요)", file=sys.stderr)


if __name__ == "__main__":
    main()
