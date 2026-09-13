#!/usr/bin/env python3
"""격차 해석기 — "하한의 N배"를 **항별 분해**로 바꿔 할 일을 알려준다.

왜 이 파일이 있는가
────────────────────────
하한 **계산**은 문제마다 달라 미리 못 짠다. 하지만 리허설에서 두 번 틀린 건
계산이 아니라 **해석**이었다.

  · "22배 격차"   → 그 하한은 **존재 불가능**했다 (필요 자원이 가용의 132%)
  · "14.8배 격차" → 정체는 **미연결 3쌍**이었다 (벌점이 평균 단위비용의 65배)

배수는 지표가 아니다. 벌점항이 단위비용보다 크면 몇 건만 놓쳐도 폭발한다.
"경로를 14.8배 줄이기"와 "3쌍을 더 연결하기"는 **완전히 다른 문제**이고,
전자로 착각하면 몇 시간을 태운다.

사용법
────────────────────────
    python gap.py --ours "배선=15406,벌점=0" --bound "배선=12000,벌점=3400"

    # 하한의 도달 가능성까지 검사 (자원 제약이 있는 문제)
    python gap.py --ours "..." --bound "..." --capacity "필요=1320,가용=1000"

    # 최대화 문제 (하한 대신 상한)
    python gap.py --ours "..." --bound "..." --maximize

항 이름은 아무거나 좋다. **우리 해와 하한을 같은 항으로 쪼개는 것**이 전부다.
쪼갤 수 없으면 그건 아직 하한을 이해하지 못한 것이다.
"""
import argparse
import sys

# 🔥 윈도우 콘솔은 기본 CP949 라 ─ ⚠ ★ 같은 문자에서 UnicodeEncodeError 로 **죽는다**.
#    다 계산해놓고 출력 한 줄에서 죽는다. (2026-08-15 발견)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VERSION = "2026-08-15a"


def eul(word):
    """한글 받침에 따라 을/를. 항 이름이 영문이면 '를'."""
    if not word:
        return "를"
    c = word[-1]
    if "가" <= c <= "힣":
        return "을" if (ord(c) - 0xAC00) % 28 else "를"
    return "를"


def parse_terms(s, label):
    """'a=1,b=2' → {'a':1.0,'b':2.0}"""
    out = {}
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            sys.exit(f"❌ --{label} 형식 오류: '{part}' — '이름=숫자' 여야 한다")
        k, v = part.split("=", 1)
        try:
            out[k.strip()] = float(v)
        except ValueError:
            sys.exit(f"❌ --{label} 의 '{k}' 값이 숫자가 아니다: {v!r}")
    if not out:
        sys.exit(f"❌ --{label} 이 비어 있다")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", required=True, help="우리 해의 항별 내역 '이름=값,이름=값'")
    ap.add_argument("--bound", required=True, help="하한(상한)의 항별 내역. **같은 항 이름으로**")
    ap.add_argument("--capacity", default="",
                    help="'필요=N,가용=M' — 하한이 요구하는 자원 vs 실제 가용")
    ap.add_argument("--maximize", action="store_true",
                    help="최대화 문제(하한이 아니라 상한)")
    ap.add_argument("--total-ours", type=float, default=None,
                    help="채점기가 준 총점. 항 합계와 대조해 분해 오류를 잡는다")
    args = ap.parse_args()

    ours = parse_terms(args.ours, "ours")
    bound = parse_terms(args.bound, "bound")
    sense = "최대화(상한)" if args.maximize else "최소화(하한)"
    print(f"[gap {VERSION}] {sense}\n")

    # ── 분해 무결성 검사 ──────────────────────────────────────────
    only_o, only_b = set(ours) - set(bound), set(bound) - set(ours)
    if only_o or only_b:
        print("⚠️ 항 이름이 양쪽에서 다르다 — 없는 쪽은 0 으로 본다.")
        if only_o:
            print(f"   우리에만: {sorted(only_o)}")
        if only_b:
            print(f"   하한에만: {sorted(only_b)}")
        print()
    keys = sorted(set(ours) | set(bound))

    to, tb = sum(ours.values()), sum(bound.values())
    if args.total_ours is not None and abs(to - args.total_ours) > 1e-6:
        print(f"❌ **분해가 틀렸다.** 항 합계 {to:g} ≠ 채점기 총점 {args.total_ours:g}")
        print("   여기서 멈추고 분해를 고칠 것. 틀린 분해로 내리는 결론은 전부 무의미하다.\n")
        sys.exit(1)

    # ── 하한이 애초에 말이 되는가 ────────────────────────────────
    slack_ok = (to <= tb) if args.maximize else (to >= tb)
    if not slack_ok:
        print(f"❌ **하한이 우리 해보다 나쁘다** (우리 {to:g} / 하한 {tb:g}).")
        print("   하한 계산이 틀렸거나 부호/방향이 반대다. 격차 분석은 의미가 없다.")
        print("   → 하한을 고치기 전엔 이 값을 목표로 삼지 말 것.\n")
        sys.exit(1)

    print(f"  우리 해 총계 {to:g}   /   하한 총계 {tb:g}   (격차 {abs(to-tb):g})\n")

    # ── ★ 항별 분해 ─────────────────────────────────────────────
    rows = []
    for k in keys:
        o, b = ours.get(k, 0.0), bound.get(k, 0.0)
        rows.append((k, o, b, o - b))
    gap = to - tb
    rows.sort(key=lambda r: -abs(r[3]))

    w = max(len(k) for k in keys)
    print(f"  {'항':<{w}}  {'우리':>12}  {'하한':>12}  {'차이':>12}   격차 기여")
    print(f"  {'-'*w}  {'-'*12}  {'-'*12}  {'-'*12}   ---------")
    for k, o, b, d in rows:
        share = (d / gap * 100) if abs(gap) > 1e-12 else 0.0
        bar = "█" * int(max(0.0, min(share, 100)) / 5)
        print(f"  {k:<{w}}  {o:>12g}  {b:>12g}  {d:>+12g}   {share:>5.0f}% {bar}")

    top_k, _, _, top_d = rows[0]
    top_share = (top_d / gap * 100) if abs(gap) > 1e-12 else 0.0

    # ── 자원 점유율 (하한의 도달 가능성) ────────────────────────
    if args.capacity:
        cap = parse_terms(args.capacity, "capacity")
        need = cap.get("필요", cap.get("need"))
        avail = cap.get("가용", cap.get("avail"))
        if need is None or avail is None:
            sys.exit("❌ --capacity 는 '필요=N,가용=M' (또는 need/avail) 형식이어야 한다")
        util = need / avail if avail else float("inf")
        print(f"\n  점유율(필요/가용) = {need:g}/{avail:g} = {util:.0%}")
        if util > 1.0:
            print("  ❌ **100% 초과 → 이 하한은 존재할 수 없다.** 완화가 너무 느슨하다.")
            print("     지금 쫓고 있는 격차는 실재하지 않는다. 하한부터 조일 것.")
        else:
            print("  ⚠️ 100% 이하지만 **이것은 필요조건일 뿐이다.**")
            print("     자원이 남아도 기하적/조합적으로 불가능할 수 있다.")
            print("     (리허설: 점유율 32% 인데도 격차가 컸다. 낮은 점유율 ≠ 믿을 만한 하한)")

    # ── 판정 ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    if abs(gap) < 1e-12:
        print("  격차 없음 — 하한에 도달했다. 이 입력은 더 볼 것이 없다.")
        print(f"{'='*60}")
        return
    print(f"  격차의 {top_share:.0f}% 가 **{top_k}** 에서 온다")
    print(f"{'='*60}")
    if top_share >= 60:
        verb = "줄이는" if not args.maximize else "키우는"
        print(f"   → 할 일은 **{top_k}{eul(top_k)} {verb} 것** 하나다.")
        print(f"      나머지 항을 건드려봐야 최대 {100-top_share:.0f}% 밖에 못 줄인다.")
    else:
        print("   → 지배하는 항이 없다. 격차가 여러 항에 흩어져 있다.")
        print("      한 방이 없다는 뜻이므로, 전면 개선이거나 하한이 느슨한 것이다.")

    ratio = to / tb if tb else float("inf")
    print(f"\n  ⚠️ 참고로 배수는 {ratio:.1f}배다. **이 숫자를 지표로 쓰지 말 것.**")
    print("     벌점/고정비 항이 단위비용보다 크면 몇 건만 놓쳐도 배수가 폭발한다.")
    print("     (리허설: '14.8배 격차'의 정체가 미연결 3쌍이었다)")
    print("     읽어야 할 것은 배수가 아니라 위의 **지배 항**이다.")


if __name__ == "__main__":
    main()
