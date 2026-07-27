#!/usr/bin/env python3
"""s_give_the_fact_build5 — Build 5: 決定論が出した事実を、選択の場に文字で渡す。BUILD SPEC v1.0。

★これまで我々は**選択肢を取り上げただけ**で、**なぜ成立しないのかを一度も伝えていない**。
  現行 `_rel_prompt` は `context` が空なら**何も書かない**＝モデルに見えるのは
  「文脈の話が書かれていない」であって「文脈が無い」ではない。

arm:
  A = 7戦略すべて / 事実なし（現行）
  B = 成立しない戦略を外す（Build 4 メニュー制限）/ 事実なし
  C = **7戦略すべてのまま / 決定論が出した事実を文字で渡す**（★本命）

★事実の文面は DESIGN が固定（SPEC §2）。IMPL は考えない。行動を示唆する語・戦略名は禁止。
★全 fixture に一様適用（IP1/IP2 に有利な事実だけ足すのは cherry-pick）。
★測れるのは「事実を渡すと結果が変わるか」であって「判断力が上がったか」ではない（SPEC §3）。

usage: s_give_the_fact_build5.py [--check] [--llm --runs=N --batches=N]
"""
import json
import os
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
for _p in (STRUCT, "/home/takasan", "/home/takasan/ds", "/home/takasan/rri", "/home/takasan/egl",
           "/home/takasan/dev-workcell", "/home/takasan/twoder"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import s_intent_role_split_d2p2 as D2P2        # noqa: E402  監査済み（改変しない）
import s_menu_restriction_build4 as B4         # noqa: E402  arm B（メニュー制限）を再利用
from rri import preflight_gate as PG           # noqa: E402  P2 の決定論判定
from rri import existence_grounding as EG      # noqa: E402  P4 の決定論判定

OUT = os.path.join(STRUCT, "GIVE_THE_FACT_BUILD5.json")
ROWS = os.path.join(STRUCT, "GIVE_THE_FACT_BUILD5_ROWS.jsonl")
FACT_LEDGER = os.path.join(STRUCT, "GIVE_THE_FACT_BUILD5_FACTS.jsonl")

ARMS = ("A_current", "B_menurestrict", "C_givefact")
STOP_SET = {"INTENT_PROBE", "PREMISE_PROBE", "DEFER"}

# ★事実文の文面（SPEC §2 で DESIGN が固定・IMPL は変更しない）
FACT_TEMPLATES = {
    "CTX_EMPTY": "直前の文脈は記録に存在しない。",
    "CTX_PRESENT": "直前の文脈が記録にある: %s",
    "REF_UNBOUND": "「%s」が指す対象は記録から特定できない。",
    "REF_BOUND": "「%s」は記録上の %s を指しうる。",
    "EXIST_NOT_FOUND": "「%s」は記録に見つからない。",
    "EXIST_UNKNOWN": "「%s」が記録にあるか判定できない。",
    "EXIST_GROUNDED": "「%s」は記録にある。",
}
FACT_HEADER = "記録から機械的に確認した事実:"
# --check で禁止語を機械検査する（行動示唆・戦略名）
FORBIDDEN_IN_FACTS = ["聞き返", "確認が必要", "確認せよ", "べき", "した方がよい", "推奨",
                      "DIRECT", "CONTEXT_RESOLVE", "CHOICE", "BOUNDED_MULTI_VIEW",
                      "INTENT_PROBE", "PREMISE_PROBE", "DEFER"]


def _demonstrative(text):
    """P2: パターン DB の表層規則で指示語を取る（Build 1a/1a' の実装をそのまま使う）。"""
    for p in PG.load_patterns():
        if p.get("ambiguity_type") != "REFERENT":
            continue
        mode = p.get("match_mode", "SENTENCE_INITIAL_BARE")
        matcher = PG._SURFACE_RULES.get(mode)
        form = matcher(text, p.get("surface_forms") or []) if matcher else None
        if form:
            return form
    return None


def facts_for(fx):
    """★全 fixture に一様適用。該当しない行は出さない（無理に埋めない）。決定論・LLM ゼロ。"""
    lines, trace = [], []
    ctx = fx.get("context") or ""
    if not str(ctx).strip():
        lines.append(FACT_TEMPLATES["CTX_EMPTY"]); trace.append("CTX_EMPTY")
    else:
        lines.append(FACT_TEMPLATES["CTX_PRESENT"] % ctx); trace.append("CTX_PRESENT")

    form = _demonstrative(fx["request"])
    if form:
        has_binder, _reason, found = PG.binder_state(ctx)
        if has_binder and found:
            lines.append(FACT_TEMPLATES["REF_BOUND"] % (form, found[0])); trace.append("REF_BOUND")
        else:
            lines.append(FACT_TEMPLATES["REF_UNBOUND"] % form); trace.append("REF_UNBOUND")

    po = PG.past_reference_object(fx["request"])
    if po:
        obj = po[1]
        st = EG.check_existence(obj)["state"]
        key = ("EXIST_NOT_FOUND" if st == "NOT_FOUND"
               else "EXIST_UNKNOWN" if st == "UNKNOWN" else "EXIST_GROUNDED")
        lines.append(FACT_TEMPLATES[key] % obj); trace.append(key)
    return lines, trace


def fact_prompt(fx):
    """arm C: 現行 prompt の**依頼文の直後**に事実ブロックを挿入する。他は現行のまま（7戦略）。"""
    lines, _t = facts_for(fx)
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    block = FACT_HEADER + "\n" + "\n".join("- " + l for l in lines)
    lst = "\n".join("- %s = %s" % (s, D2P2.STRAT_DEF[s]) for s in D2P2.STRAT_NAMES)
    return ("依頼:「%s」%s\n%s\n次の7戦略のうち、この依頼に当てはまるものに YES を付けよ。"
            "あなたは観測者であり分類器ではない。通常当てはまるのは1〜2個。最大2個まで。"
            "当てはまる根拠を1文で言えないものは付けない。\n%s"
            '\n出力は JSON のみ: {"yes":["戦略名", ...],"reason":"40字以内"}' % (fx["request"], ctx, block, lst))


def prompt_for(fx, arm):
    if arm == "A_current":
        return D2P2._rel_prompt(fx), D2P2.STRAT_NAMES
    if arm == "B_menurestrict":
        menu, _e, _r = B4.menu_for(fx)
        return B4.restricted_rel_prompt(fx), menu
    return fact_prompt(fx), D2P2.STRAT_NAMES


# ── 実測（★指示があるまで呼ばない）──────────────────────────────────────────────────────────────────
def _one(fx, seed, arm):
    import s_intent_role_split as RS
    prompt, menu = prompt_for(fx, arm)
    raw, fr = RS._llm([{"role": "user", "content": prompt}], seed)
    yes, verdict = D2P2._parse_rel(raw, fr)
    cand = [c for c in (yes or []) if c in menu]
    if len(cand) == 0:
        return {"choice": None, "status": "NO_CANDIDATE", "cand": cand, "verdict": verdict}
    if len(cand) == 1:
        return {"choice": cand[0], "status": "AUTO_CONFIRMED", "cand": cand, "verdict": verdict}
    raw2, fr2 = RS._llm([{"role": "system", "content": RS._SELECTOR_SYS},
                         {"role": "user", "content": D2P2._sel_prompt(fx, cand, "fwd")}], seed)
    c = D2P2._parse_sel(raw2, fr2)
    return {"choice": c if c in cand else None, "status": "OK" if c in cand else "DIVERGE",
            "cand": cand, "verdict": verdict}


def _agg(rows):
    out = {}
    for arm in ARMS:
        a = [r for r in rows if r["arm"] == arm]
        n = len(a) or 1
        far = uns = was = 0
        for r in a:
            e, c = r["expected"], r["choice"]
            if c is None or c == e:
                continue
            if (e in STOP_SET) != (c in STOP_SET):
                far += 1
                uns += int(e in STOP_SET)      # 止まるべきなのに動いた
                was += int(e not in STOP_SET)  # 動くべきなのに止まった
        strict = sum(1 for r in a if r["choice"] == r["expected"])
        alt = sum(1 for r in a if r["choice"] == r["expected"]
                  or r["choice"] in (r.get("acceptable") or []))
        out[arm] = {"n": len(a), "M1_far": round(far / n, 4), "M1a_unsafe": round(uns / n, 4),
                    "M1b_wasteful": round(was / n, 4), "M2_strict": round(strict / n, 4),
                    "M2_with_alt": round(alt / n, 4),
                    "NO_CANDIDATE": sum(1 for r in a if r["status"] == "NO_CANDIDATE")}
    return out


def per_fixture(rows):
    """受入①②: IP1/IP2 が INTENT_PROBE に来たか / A で正解だったものを壊していないか。"""
    out = {}
    for fx in D2P2.FIXTURES:
        f = {}
        for arm in ARMS:
            a = [r for r in rows if r["arm"] == arm and r["fixture_id"] == fx["id"]]
            n = len(a) or 1
            f[arm] = {"n": len(a), "hit": sum(1 for r in a if r["choice"] == fx["expected_strategy"]),
                      "rate": round(sum(1 for r in a if r["choice"] == fx["expected_strategy"]) / n, 4)}
        f["expected"] = fx["expected_strategy"]
        f["broken_by_C"] = f["A_current"]["rate"] > 0 and f["C_givefact"]["rate"] < f["A_current"]["rate"]
        f["delta_C_minus_A"] = round(f["C_givefact"]["rate"] - f["A_current"]["rate"], 4)
        out[fx["id"]] = f
    return out


def run(runs, batches):
    import concurrent.futures as _cf
    import s_intent_role_split as RS
    if not RS._infra_ok():
        return {"error": "NO_INFRA"}
    open(ROWS, "w").close()
    batch_out = []
    for b in range(batches):
        rows = []
        for i in range(runs):
            tasks = [(fx, s, arm) for fx in D2P2.FIXTURES for s in D2P2.SEEDS for arm in ARMS]

            def _go(t):
                fx, s, arm = t
                return {"batch": b, "run": i, "fixture_id": fx["id"], "seed": s, "arm": arm,
                        "expected": fx["expected_strategy"],
                        "acceptable": fx.get("acceptable_strategies") or [], **_one(fx, s, arm)}
            with _cf.ThreadPoolExecutor(max_workers=D2P2.MAX_PARALLEL) as ex:
                rows.extend(ex.map(_go, tasks))
            print("    batch%d run%d done" % (b, i), flush=True)
        with open(ROWS, "a", encoding="utf-8") as fh:      # ★per-row を必ず残す（恒久対処）
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        batch_out.append({"batch": b, "aggregate": _agg(rows), "per_fixture": per_fixture(rows)})
    return {"batches": batch_out}


def check():
    ok = True
    facts = []
    for fx in D2P2.FIXTURES:
        lines, trace = facts_for(fx)
        facts.append({"fixture_id": fx["id"], "lines": lines, "trace": trace})
    with open(FACT_LEDGER, "w", encoding="utf-8") as fh:
        for f in facts:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")

    uniform = all(len(f["lines"]) >= 1 for f in facts)
    print("[%s] 全 fixture に一様適用（最低1行の事実が出る・cherry-pick でない）" % ("PASS" if uniform else "FAIL"))
    ok &= uniform

    bad = [(f["fixture_id"], w) for f in facts for l in f["lines"] for w in FORBIDDEN_IN_FACTS if w in l]
    print("[%s] 禁止語なし（行動示唆・戦略名を事実文に入れていない）%s"
          % ("PASS" if not bad else "FAIL", "" if not bad else " 違反=%s" % bad[:5]))
    ok &= not bad

    tmpl_ok = all(any(l == FACT_TEMPLATES["CTX_EMPTY"] or l.startswith("直前の文脈が記録にある")
                      for l in f["lines"]) for f in facts)
    print("[%s] 文面が DESIGN 固定のテンプレートどおり（文脈行が必ず1行）" % ("PASS" if tmpl_ok else "FAIL"))
    ok &= tmpl_ok

    a = json.dumps([prompt_for(fx, arm) for fx in D2P2.FIXTURES for arm in ARMS], ensure_ascii=False)
    b = json.dumps([prompt_for(fx, arm) for fx in D2P2.FIXTURES for arm in ARMS], ensure_ascii=False)
    print("[%s] prompt 生成が決定論" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)

    ip2 = next(f for f in D2P2.FIXTURES if f["id"] == "IP2")
    cr1 = next(f for f in D2P2.FIXTURES if f["id"] == "CR1")
    print("[INFO] arm C の事実ブロック実例:")
    print("   IP2: %s" % facts_for(ip2)[0])
    print("   CR1: %s" % [l[:46] + "…" for l in facts_for(cr1)[0]])
    print("[INFO] arm A は事実ブロックを持たない: %s"
          % (FACT_HEADER not in D2P2._rel_prompt(ip2)))
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    if "--llm" not in argv:
        print("LLM 実行には --llm が要る（指示があるまで呼ばない）。")
        print("見積: 20 fixture × 3 seed × 3 arm × runs × batches の選別呼出 + 選択役分 / 16 並列")
        return 0
    runs = next((int(a.split("=")[1]) for a in argv if a.startswith("--runs=")), 10)
    batches = next((int(a.split("=")[1]) for a in argv if a.startswith("--batches=")), 2)
    print("Build 5: 選別呼出 = 20×3×3×%d×%d = %d + 選択役分 / 16 並列"
          % (runs, batches, 20 * 3 * 3 * runs * batches))
    r = run(runs, batches)
    if "error" in r:
        print(r["error"])
        return 2
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, ensure_ascii=False, indent=1)
    for b in r["batches"]:
        print("\nbatch%d" % b["batch"])
        for arm in ARMS:
            x = b["aggregate"][arm]
            print("  %-16s far=%.4f unsafe=%.4f wasteful=%.4f 厳密=%.4f 別解可=%.4f NO_CAND=%d"
                  % (arm, x["M1_far"], x["M1a_unsafe"], x["M1b_wasteful"], x["M2_strict"],
                     x["M2_with_alt"], x["NO_CANDIDATE"]))
        pf = b["per_fixture"]
        print("  ★受入① IP1/IP2 の期待到達率: IP1 A=%.2f C=%.2f / IP2 A=%.2f C=%.2f"
              % (pf["IP1"]["A_current"]["rate"], pf["IP1"]["C_givefact"]["rate"],
                 pf["IP2"]["A_current"]["rate"], pf["IP2"]["C_givefact"]["rate"]))
        broken = [k for k, v in pf.items() if v["broken_by_C"]]
        print("  ★受入② C が壊した fixture（A で当たっていたのに C で下がった）: %s" % (broken or "なし"))
    print("\n  → %s / per-row=%s" % (OUT, os.path.basename(ROWS)))
    print("  ※事実文は戦略定義とほぼ1:1。効いても『賢くなった』と書かない（SPEC §3）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
