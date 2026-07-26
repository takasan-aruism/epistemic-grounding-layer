#!/usr/bin/env python3
"""s_menu_restriction_build4 — Build 4 PART 1: 構造的に成立しない戦略をメニューに載せない。

★貫く原則（Taka）: **存在／非存在をまず決定論で確定する。確定した側だけを別の分岐に渡す。**
  **LLM に「在るかどうか」を判断させない。選べてしまう時点で選ぶ。**

現行は「7戦略を全部見せてから、後で CONTEXT_RESOLVE を消す」（後置フィルタ = Build 1b）。
本スライスは「**そもそもメニューに載せない**」に変える。

★前提は data として持つ（code に埋め込まない・後から反証できる形にする）。
★受入①は **LLM を呼ばずに示せる**（prompt 文字列を検査するだけ）。最初にこれを出す。

usage: s_menu_restriction_build4.py [--check]
"""
import json
import os
import sys

STRUCT = os.path.dirname(os.path.abspath(__file__))
for _p in (STRUCT, "/home/takasan", "/home/takasan/ds", "/home/takasan/rri", "/home/takasan/egl",
           "/home/takasan/dev-workcell", "/home/takasan/twoder"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import s_intent_role_split_d2p2 as D2P2   # noqa: E402  監査済み（改変しない・比較の baseline）

OUT = os.path.join(STRUCT, "MENU_RESTRICTION_BUILD4.json")
PROMPT_LEDGER = os.path.join(STRUCT, "MENU_RESTRICTION_BUILD4_PROMPTS.jsonl")

# ── 各戦略の「成立の前提」（★data として宣言・BUILD SPEC §2 / D-3 の洗い出し結果）─────────────────
#    kind: CONTEXT_NONEMPTY = context が非空でなければ定義上あり得ない / NONE = 前提なし
STRATEGY_PRECONDITIONS = {
    "CONTEXT_RESOLVE": {"kind": "CONTEXT_NONEMPTY",
                        "why": "定義が『直前の文脈に支配的な解釈があり文脈で絞れる』。文脈が無ければ定義上あり得ない"},
    "DIRECT": {"kind": "NONE", "why": "前提なし"},
    "CHOICE": {"kind": "NONE", "why": "前提なし"},
    "BOUNDED_MULTI_VIEW": {"kind": "NONE", "why": "前提なし"},
    "INTENT_PROBE": {"kind": "NONE", "why": "前提なし"},
    "PREMISE_PROBE": {"kind": "NONE", "why": "前提なし"},
    "DEFER": {"kind": "NONE", "why": "前提なし"},
}
# ★前提にしてはいけないもの（D-3-2 で DESIGN が封じた・記録して再発を防ぐ）
FORBIDDEN_PRECONDITIONS = [
    {"signal": "指示語の束縛先の有無 (Build 1a BIND-RULE-001)",
     "why_not": "束縛先が在っても INTENT_PROBE が正しい場合がある（束縛先が複数ある等）。前提にすると正しい選択肢を殺す"},
    {"signal": "対象の接地状態 (Build 1c existence_grounding)",
     "why_not": "接地していても PREMISE_PROBE が正しい場合がある（存在はするが別物かもしれない）。同上"},
]


def is_empty_context(context):
    """決定論。Build 1b の is_empty_context と同一の判定規則。"""
    import re
    if context is None:
        return True
    return re.sub(r"[\s　\x00-\x1f]", "", str(context)) == ""


def menu_for(fx):
    """★成立の前提を満たす戦略だけを返す。前提の判定は完全決定論・LLM ゼロ。
    返り: (menu, excluded, reasons)"""
    menu, excluded, reasons = [], [], {}
    for s in D2P2.STRAT_NAMES:
        pre = STRATEGY_PRECONDITIONS.get(s, {"kind": "NONE"})
        if pre["kind"] == "CONTEXT_NONEMPTY" and is_empty_context(fx.get("context")):
            excluded.append(s)
            reasons[s] = "前提 CONTEXT_NONEMPTY が不成立（context が空）: " + pre["why"]
        else:
            menu.append(s)
    return menu, excluded, reasons


def restricted_rel_prompt(fx):
    """メニュー制限版の選別 prompt。**D2P2._rel_prompt と同じ文面で、戦略一覧だけを差し替える。**
    （文面を変えると差が prompt 文言に帰属してしまうため、変えるのは一覧だけにする。）"""
    menu, _exc, _r = menu_for(fx)
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    lst = "\n".join("- %s = %s" % (s, D2P2.STRAT_DEF[s]) for s in menu)
    return ("依頼:「%s」%s\n次の%d戦略のうち、この依頼に当てはまるものに YES を付けよ。"
            "あなたは観測者であり分類器ではない。通常当てはまるのは1〜2個。最大2個まで。"
            "当てはまる根拠を1文で言えないものは付けない。\n%s"
            '\n出力は JSON のみ: {"yes":["戦略名", ...],"reason":"40字以内"}' % (fx["request"], ctx, len(menu), lst))


# ── 受入①〜③（★LLM を呼ばない）─────────────────────────────────────────────────────────────────────
def prompt_receipts():
    rows, r1, r2, r3 = [], [], [], []
    for fx in D2P2.FIXTURES:
        base = D2P2._rel_prompt(fx)
        restricted = restricted_rel_prompt(fx)
        menu, excluded, reasons = menu_for(fx)
        empty = is_empty_context(fx.get("context"))
        rec = {"fixture_id": fx["id"], "context_empty": empty, "menu": menu, "excluded": excluded,
               "reasons": reasons,
               "baseline_has_CONTEXT_RESOLVE": "CONTEXT_RESOLVE" in base,
               "restricted_has_CONTEXT_RESOLVE": "CONTEXT_RESOLVE" in restricted,
               "restricted_prompt": restricted}
        rows.append(rec)
        if empty:
            r1.append((fx["id"], rec["restricted_has_CONTEXT_RESOLVE"] is False))
        else:
            r2.append((fx["id"], rec["restricted_has_CONTEXT_RESOLVE"] is True))
        others = [s for s in D2P2.STRAT_NAMES if s != "CONTEXT_RESOLVE"]
        r3.append((fx["id"], all(s in restricted for s in others)))
    return rows, r1, r2, r3


def assess():
    rows, r1, r2, r3 = prompt_receipts()
    return {
        "preconditions": STRATEGY_PRECONDITIONS,
        "forbidden_preconditions": FORBIDDEN_PRECONDITIONS,
        "receipt1_empty_context_no_CONTEXT_RESOLVE": {"n": len(r1), "ok": all(v for _i, v in r1),
                                                      "failed": [i for i, v in r1 if not v]},
        "receipt2_with_context_has_CONTEXT_RESOLVE": {"n": len(r2), "ok": all(v for _i, v in r2),
                                                      "fixtures": [i for i, _v in r2],
                                                      "failed": [i for i, v in r2 if not v]},
        "receipt3_other_six_always_present": {"n": len(r3), "ok": all(v for _i, v in r3),
                                              "failed": [i for i, v in r3 if not v]},
        "baseline_shows_CONTEXT_RESOLVE_even_when_empty": sum(
            1 for r in rows if r["context_empty"] and r["baseline_has_CONTEXT_RESOLVE"]),
        "rows": rows,
    }


# ── 受入③（振り直しの有無）— LLM を使う比較。★2アームで prompt が違うので分布で出す（最低10run・2batch）──
def _arm_run(fx, seed, arm):
    import s_intent_role_split as RS
    if arm == "A_postfilter":
        raw, fr = RS._llm([{"role": "user", "content": D2P2._rel_prompt(fx)}], seed)
        yes, verdict = D2P2._parse_rel(raw, fr)
        cand = list(yes or [])
        # Build 1b の後置フィルタ: context が空なら CONTEXT_RESOLVE を候補から除く
        if is_empty_context(fx.get("context")):
            cand = [c for c in cand if c != "CONTEXT_RESOLVE"]
    else:
        raw, fr = RS._llm([{"role": "user", "content": restricted_rel_prompt(fx)}], seed)
        yes, verdict = D2P2._parse_rel(raw, fr)
        menu, _e, _r = menu_for(fx)
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


STOP_SET = {"INTENT_PROBE", "PREMISE_PROBE", "DEFER"}


def _agg(rows):
    out = {}
    for arm in ("A_postfilter", "B_menurestrict"):
        a = [r for r in rows if r["arm"] == arm]
        n = len(a)
        far = uns = was = 0
        for r in a:
            e, c = r["expected"], r["choice"]
            if c is None or c == e:
                continue
            if (e in STOP_SET) != (c in STOP_SET):
                far += 1
                uns += int(e in STOP_SET)
                was += int(e not in STOP_SET)
        out[arm] = {"n": n, "M1_far": round(far / n, 4), "M1a_unsafe": round(uns / n, 4),
                    "M1b_wasteful": round(was / n, 4),
                    "M2_match": round(sum(1 for r in a if r["choice"] == r["expected"]) / n, 4),
                    "NO_CANDIDATE": sum(1 for r in a if r["status"] == "NO_CANDIDATE")}
    return out


def llm_compare(runs=10, batches=2):
    import s_intent_role_split as RS
    if not RS._infra_ok():
        return {"error": "NO_INFRA"}
    batch_out = []
    for b in range(batches):
        rows = []
        import concurrent.futures as _cf
        for i in range(runs):
            tasks = [(fx, seed, arm) for fx in D2P2.FIXTURES for seed in D2P2.SEEDS
                     for arm in ("A_postfilter", "B_menurestrict")]

            def _go(t):
                fx, seed, arm = t
                r = _arm_run(fx, seed, arm)
                return {"batch": b, "run": i, "fixture_id": fx["id"], "seed": seed, "arm": arm,
                        "expected": fx["expected_strategy"], **r}
            with _cf.ThreadPoolExecutor(max_workers=D2P2.MAX_PARALLEL) as ex:
                rows.extend(ex.map(_go, tasks))
            print("    batch%d run%d done" % (b, i), flush=True)
        # ★振り直し: 同一 (fixture, seed, run) で A が NO_CANDIDATE だった回、B は何を返したか
        reass = []
        for r in rows:
            if r["arm"] != "A_postfilter" or r["status"] != "NO_CANDIDATE":
                continue
            m = next((x for x in rows if x["arm"] == "B_menurestrict" and x["run"] == r["run"]
                      and x["fixture_id"] == r["fixture_id"] and x["seed"] == r["seed"]), None)
            if m:
                reass.append({"fixture_id": r["fixture_id"], "seed": r["seed"], "run": r["run"],
                              "B_status": m["status"], "B_choice": m["choice"],
                              "reassigned": m["status"] != "NO_CANDIDATE",
                              "reassigned_correct": m["choice"] == r["expected"]})
        # ★D5-V: per-(fixture,seed,run) の選択結果を必ず保存する（前回は保存しておらず再集計できなかった）
        with open(os.path.join(STRUCT, "MENU_RESTRICTION_BUILD4_ROWS.jsonl"), "a", encoding="utf-8") as _fh:
            for _r in rows:
                _fh.write(json.dumps(_r, ensure_ascii=False) + "\n")
        batch_out.append({"batch": b, "aggregate": _agg(rows), "reassignment": {
            "A_no_candidate_n": len(reass),
            "reassigned_n": sum(1 for x in reass if x["reassigned"]),
            "reassigned_correct_n": sum(1 for x in reass if x["reassigned_correct"]),
            "cases": reass[:40]}})
    return {"batches": batch_out}


def check():
    r = assess()
    ok = True
    for key, label in (("receipt1_empty_context_no_CONTEXT_RESOLVE",
                        "受入① context が空 → prompt に CONTEXT_RESOLVE が現れない"),
                       ("receipt2_with_context_has_CONTEXT_RESOLVE",
                        "受入② context が在る(CR1/CR2/CR3) → 従来どおり現れる"),
                       ("receipt3_other_six_always_present",
                        "受入③ 他の6戦略は context の有無によらず常に現れる")):
        v = r[key]
        print("[%s] %s (%d件%s)" % ("PASS" if v["ok"] else "FAIL", label, v["n"],
                                    "" if v["ok"] else " / 失敗=%s" % v["failed"]))
        ok &= v["ok"]
    n = r["baseline_shows_CONTEXT_RESOLVE_even_when_empty"]
    print("[INFO] 現行(後置フィルタ)は context が空でも CONTEXT_RESOLVE を提示していた: %d 件" % n)
    a = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(assess(), ensure_ascii=False, sort_keys=True)
    print("[%s] 決定論再現" % ("PASS" if a == b else "FAIL"))
    ok &= (a == b)
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    r = assess()
    if "--llm" in argv:
        runs = next((int(a.split("=")[1]) for a in argv if a.startswith("--runs=")), 10)
        batches = next((int(a.split("=")[1]) for a in argv if a.startswith("--batches=")), 2)
        print("LLM 比較: A_postfilter vs B_menurestrict  runs=%d batches=%d" % (runs, batches))
        r["llm_compare"] = llm_compare(runs, batches)
        for b in r["llm_compare"].get("batches", []):
            print("  batch%d: %s" % (b["batch"], b["aggregate"]))
            print("    振り直し: A の NO_CANDIDATE %d件 → B で振り直された %d件 (うち正解 %d件)"
                  % (b["reassignment"]["A_no_candidate_n"], b["reassignment"]["reassigned_n"],
                     b["reassignment"]["reassigned_correct_n"]))
    with open(PROMPT_LEDGER, "w", encoding="utf-8") as fh:
        for row in r["rows"]:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({k: v for k, v in r.items() if k != "rows"}, fh, ensure_ascii=False, indent=1)
    print("Build 4 PART 1 メニュー制限 — 受入①②③（★LLM を呼んでいない）")
    for key in ("receipt1_empty_context_no_CONTEXT_RESOLVE", "receipt2_with_context_has_CONTEXT_RESOLVE",
                "receipt3_other_six_always_present"):
        v = r[key]
        print("  %-46s n=%-3d ok=%s" % (key, v["n"], v["ok"]))
    print("  現行(後置フィルタ)が空 context でも CONTEXT_RESOLVE を提示していた件数: %d"
          % r["baseline_shows_CONTEXT_RESOLVE_even_when_empty"])
    print("  前提あり: %s / 前提なし: %d戦略"
          % ([s for s, p in STRATEGY_PRECONDITIONS.items() if p["kind"] != "NONE"],
             sum(1 for p in STRATEGY_PRECONDITIONS.values() if p["kind"] == "NONE")))
    print("  ★前提にしてはいけない信号（D-3-2 で封じたもの）:")
    for f in FORBIDDEN_PRECONDITIONS:
        print("     - %s" % f["signal"])
    print("  → %s / prompt 全文=%s" % (OUT, os.path.basename(PROMPT_LEDGER)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
