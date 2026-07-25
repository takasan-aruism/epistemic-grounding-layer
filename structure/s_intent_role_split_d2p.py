#!/usr/bin/env python3
"""s_intent_role_split_d2p — arm-D2': 再観測を廃止し、膨張対策を「削減圧」から「矛盾の機械除去」へ。

前回 arm-D の 0.46 は役割分割の実力でなく、監査flag→制約付き再観測が正解候補を10件落とした(spec バグ・DESIGN の責)結果。
本器は是正版。3構成を同 fixture で比較(既存 s_intent_role_split.py は不改変・比較用に残す):
- **A**: 独立選別・**再観測なし**・raw 候補集合 → 選択役。＝役割分割の素の実力。
- **B**: 独立選別 + **矛盾ペアの機械除去**(決定論・LLM に直させない=ESDE) → 選択役。
- **C**: **相対比較選別**(7戦略を1呼出・最大2 YES を員数強制) → 選択役。独立版も残す(短絡回避の根拠)。

★指標は4つ必ず併記(前回、最終一致だけ見て誤帰属しかけた):
  (a)最終一致 (b)候補集合の上限 (c)選択役効率=(a)/(b) (d)回答時精度(NO_CANDIDATE 除く)。
MUTEX 除去が正解を落としたら `MUTEX_DROPPED_CORRECT` で正直に。NO_CANDIDATE は `MENU_GAP_SUSPECT` を別枠(判定せず材料)。
metric=seed平均(arm-C3 0.5397 と同一物差し)。arm-C2 0.83(汚染)とは並べない。
モデル差留保: ESDE=QwQ-32B dense thinking / 本件=Qwen3.6-35B-**A3B**(active 3B)。同水準でなくとも失敗と結論しない。

usage:  s_intent_role_split_d2p.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
from collections import Counter

import s_intent_probe_armc3 as A3
import s_intent_role_split as RS   # STRATEGIES/MUTEX/選別prompt/parse/選択役/汚染ゲート を再利用

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_ROLE_SPLIT_D2P.jsonl")
SEEDS = (0, 1, 2)
PROMPT_ID = "role-split-d2p-v1"
MAX_PARALLEL = 16
CONFIGS = ["A_raw", "B_mutex", "C_relative"]

# MUTEX 機械除去の事前固定規則(先に書いて記録・実行時に変えない)。返り (kept set, drop log)。
def mutex_remove(yes):
    y = list(yes)
    dropped = []
    # 規則1: DEFER は他と両立しない → 他に YES があれば DEFER を落とす
    if "DEFER" in y and len(y) > 1:
        y.remove("DEFER")
        dropped.append(("DEFER", "rule1_defer_exclusive"))
    # 規則2: DIRECT と {INTENT_PROBE,PREMISE_PROBE} 同時 → DIRECT を落とす(確認要なら直接答えは不成立・安全側)
    if "DIRECT" in y and any(p in y for p in ("INTENT_PROBE", "PREMISE_PROBE")):
        y.remove("DIRECT")
        dropped.append(("DIRECT", "rule2_direct_vs_probe"))
    # 規則3: DIRECT と {BMV,CHOICE} は落とさず両方残す(選択役の仕事)
    return y, dropped


# 相対比較選別(C): 7戦略を1呼出・最大2 YES を員数強制
def _relative_prompt(fx):
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    lst = "\n".join("- %s = %s" % (s, RS.STRAT_DEF[s]) for s in RS.STRAT_NAMES)
    return ("依頼:「%s」%s\n次の7戦略のうち、この依頼に当てはまるものに YES を付けよ。"
            "あなたは観測者であり分類器ではない。通常当てはまるのは1〜2個。最大2個まで。"
            "当てはまる根拠を1文で言えないものは付けない。\n%s"
            '\n出力は JSON のみ: {"yes":["戦略名", ...],"reason":"40字以内"}' % (fx["request"], ctx, lst))


def _parse_relative(raw, fr):
    if fr == "length":
        return None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None, "DIVERGE_SCHEMA"
    try:
        y = json.loads(m.group(0)).get("yes") or []
    except Exception:
        return None, "DIVERGE_SCHEMA"
    return [s for s in RS.STRAT_NAMES if any(s in str(x) for x in y)], "OK"


def _expected(fid):
    return next(fx["expected_strategy"] for fx in A3.FIXTURES if fx["id"] == fid)


# ── 実測 ─────────────────────────────────────────────────────────────────────
def run():
    import time as _t
    t0 = _t.time()
    # 独立選別(A/B 共通・D1 YES/NO)
    ind_tasks = [(fx, st, s) for fx in A3.FIXTURES for st in RS.STRAT_NAMES for s in SEEDS]

    def _ind(t):
        fx, st, s = t
        raw, fr = RS._llm([{"role": "user", "content": RS._screen_prompt(fx, st, "D1")}], s)
        val, reason, verdict = RS._parse_screen("D1", raw, fr)
        return {"cfg": "IND", "fixture_id": fx["id"], "strategy": st, "seed": s,
                "value": val, "reason": reason, "parse_verdict": verdict, "raw_output": raw}

    # 相対選別(C)
    rel_tasks = [(fx, s) for fx in A3.FIXTURES for s in SEEDS]

    def _rel(t):
        fx, s = t
        raw, fr = RS._llm([{"role": "user", "content": _relative_prompt(fx)}], s)
        yes, verdict = _parse_relative(raw, fr)
        return {"cfg": "REL", "fixture_id": fx["id"], "seed": s, "yes": yes,
                "parse_verdict": verdict, "raw_output": raw}
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        ind = list(ex.map(_ind, ind_tasks))
        rel = list(ex.map(_rel, rel_tasks))

    # 候補集合を構成別に作る
    def _ind_yes(fid, s):
        d = {r["strategy"]: r for r in ind if r["fixture_id"] == fid and r["seed"] == s}
        return [st for st in RS.STRAT_NAMES if d.get(st, {}).get("value") is True]

    def _rel_yes(fid, s):
        r = next((r for r in rel if r["fixture_id"] == fid and r["seed"] == s), None)
        return r["yes"] if r and r["yes"] is not None else []

    cand_rows, sel_rows = [], []
    for cfg in CONFIGS:
        for fx in A3.FIXTURES:
            for s in SEEDS:
                if cfg == "A_raw":
                    cand, dropped = _ind_yes(fx["id"], s), []
                elif cfg == "B_mutex":
                    cand, dropped = mutex_remove(_ind_yes(fx["id"], s))
                else:  # C_relative
                    cand, dropped = _rel_yes(fx["id"], s), []
                exp = _expected(fx["id"])
                cand_rows.append({"row": "cand", "cfg": cfg, "fixture_id": fx["id"], "seed": s,
                                  "candidates": cand, "n": len(cand),
                                  "expected_in": exp in cand,
                                  "dropped": dropped,
                                  "dropped_correct": any(d[0] == exp for d in dropped)})
                for order in ("fwd", "rev"):
                    if len(cand) == 0:
                        sel_rows.append({"row": "sel", "cfg": cfg, "fixture_id": fx["id"], "seed": s, "order": order,
                                         "candidates": cand, "choice": None, "status": "NO_CANDIDATE", "raw_output": ""})
                    elif len(cand) == 1:
                        sel_rows.append({"row": "sel", "cfg": cfg, "fixture_id": fx["id"], "seed": s, "order": order,
                                         "candidates": cand, "choice": cand[0], "status": "SINGLE_CANDIDATE", "raw_output": ""})
                    else:
                        raw, fr = RS._llm([{"role": "system", "content": RS._SELECTOR_SYS},
                                           {"role": "user", "content": RS._select_prompt(fx, cand, order)}], s)
                        c, v = RS._parse_select(raw, fr)
                        st = "OK" if c in cand else ("SELECTOR_OUT_OF_SET" if c else v)
                        sel_rows.append({"row": "sel", "cfg": cfg, "fixture_id": fx["id"], "seed": s, "order": order,
                                         "candidates": cand, "choice": c if c in cand else None,
                                         "raw_choice": c, "status": st, "raw_output": raw})
    wall = round(_t.time() - t0, 2)
    return ind, rel, cand_rows, sel_rows, wall


# ── 集計(4指標 × 3構成)───────────────────────────────────────────────────────
def aggregate(ind, rel, cand_rows, sel_rows):
    out = {}
    for cfg in CONFIGS:
        crows = [c for c in cand_rows if c["cfg"] == cfg]
        # (b) 候補上限
        upper = sum(1 for c in crows if c["expected_in"])
        # (a) 最終一致(fwd)・(d) 回答時精度
        hit = answered = 0
        for c in crows:
            sel = next((r for r in sel_rows if r["cfg"] == cfg and r["fixture_id"] == c["fixture_id"]
                        and r["seed"] == c["seed"] and r["order"] == "fwd"), None)
            got = sel["choice"] if sel else None
            exp = _expected(c["fixture_id"])
            if got is not None:
                answered += 1
            if got == exp or got in next(fx.get("acceptable_strategies", []) for fx in A3.FIXTURES if fx["id"] == c["fixture_id"]):
                hit += 1
        n = len(crows)
        # 順序一致
        pb_t = pb_a = 0
        for c in crows:
            f = next((r for r in sel_rows if r["cfg"] == cfg and r["fixture_id"] == c["fixture_id"] and r["seed"] == c["seed"] and r["order"] == "fwd"), None)
            r = next((r for r in sel_rows if r["cfg"] == cfg and r["fixture_id"] == c["fixture_id"] and r["seed"] == c["seed"] and r["order"] == "rev"), None)
            if f and r and f["choice"] and r["choice"]:
                pb_t += 1
                pb_a += int(f["choice"] == r["choice"])
        yes_counts = [c["n"] for c in crows]
        no_cand = sum(1 for c in crows if c["n"] == 0)
        out[cfg] = {
            "a_final_seedavg": round(hit / n, 4) if n else None,
            "b_candidate_upper": round(upper / n, 4) if n else None,
            "c_selector_efficiency": round(hit / upper, 4) if upper else None,
            "d_answered_accuracy": round(hit / answered, 4) if answered else None,
            "final_raw": "%d/%d" % (hit, n), "upper_raw": "%d/%d" % (upper, n),
            "answered_raw": "%d/%d" % (hit, answered),
            "yes_count_mean": round(sum(yes_counts) / len(yes_counts), 2) if yes_counts else None,
            "yes_inflation_ge3": sum(1 for x in yes_counts if x >= 3),
            "no_candidate_n": no_cand,
            "selector_order_agreement": round(pb_a / pb_t, 4) if pb_t else None,
            "selector_out_of_set_n": sum(1 for r in sel_rows if r["cfg"] == cfg and r["status"] == "SELECTOR_OUT_OF_SET"),
            "mutex_dropped_correct_n": sum(1 for c in crows if c["dropped_correct"]),
            "mutex_dropped_total_n": sum(len(c["dropped"]) for c in crows),
        }
    # MENU_GAP_SUSPECT: A_raw で全 seed NO_CANDIDATE の fixture(材料・判定せず)
    menu_gap = []
    for fx in A3.FIXTURES:
        ncs = [c for c in cand_rows if c["cfg"] == "A_raw" and c["fixture_id"] == fx["id"]]
        if ncs and all(c["n"] == 0 for c in ncs):
            menu_gap.append(fx["id"])
    return {"per_config": out, "menu_gap_suspect": menu_gap,
            "note": "seed平均で arm-C3(0.5397)と比較・arm-C2 0.83汚染とは並べない・能力主張でない・A3B(active3B)差留保。"}


def _ser(ind, rel, cand_rows, sel_rows, agg, wall):
    hdr = {"_meta": "INTENT_ROLE_SPLIT_D2P(arm-D2': 再観測廃止/矛盾機械除去/相対選別/4指標)。役割分割の素の実力を測る。",
           "arm": "D2p", "aggregate": agg, "wall_seconds": wall, "prompt_id": PROMPT_ID,
           "configs": CONFIGS, "seeds": list(SEEDS), "mutex_rules": ["rule1_defer_exclusive", "rule2_direct_vs_probe", "rule3_direct_multi_keep_both"]}
    rows = ind + rel + cand_rows + sel_rows
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows]) + "\n"


def _report(agg):
    for cfg in CONFIGS:
        a = agg["per_config"][cfg]
        print("  [%s] (a)最終=%s [%s] (b)候補上限=%s [%s] (c)選択役効率=%s (d)回答時=%s [%s]"
              % (cfg, a["a_final_seedavg"], a["final_raw"], a["b_candidate_upper"], a["upper_raw"],
                 a["c_selector_efficiency"], a["d_answered_accuracy"], a["answered_raw"]))
        print("        YES平均=%.2f(≥3:%d) NO_CAND=%d 順序一致=%s OUT_OF_SET=%d MUTEX除去=%d(内正解落し=%d)"
              % (a["yes_count_mean"], a["yes_inflation_ge3"], a["no_candidate_n"], a["selector_order_agreement"],
                 a["selector_out_of_set_n"], a["mutex_dropped_total_n"], a["mutex_dropped_correct_n"]))
    print("  MENU_GAP_SUSPECT(判定せず材料): %s" % agg["menu_gap_suspect"])


def check():
    red = []
    if RS.contamination_violations():
        red.append("CONTAMINATION: %s" % RS.contamination_violations()[:6])
    _sv = RS.STRATEGIES[0]
    try:
        RS.STRATEGIES[0] = (_sv[0], _sv[1] + A3.FIXTURES[0]["request"])
        RS.STRAT_DEF[_sv[0]] = RS.STRATEGIES[0][1]
        if not RS.contamination_violations():
            red.append("CONTAMINATION_GATE_DEAD")
    finally:
        RS.STRATEGIES[0] = _sv
        RS.STRAT_DEF[_sv[0]] = _sv[1]
    if not os.path.isfile(OUT):
        red.append("NOT_GENERATED")
        print("INTENT_ROLE_SPLIT_D2P --check: RED")
        for m in red:
            print("  " + m)
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header = lines[0]
    ind = [l for l in lines[1:] if l.get("cfg") == "IND"]
    rel = [l for l in lines[1:] if l.get("cfg") == "REL"]
    cand_rows = [l for l in lines[1:] if l.get("row") == "cand"]
    sel_rows = [l for l in lines[1:] if l.get("row") == "sel"]
    # MUTEX 除去規則の決定論再現(記録 IND YES から B の候補が再現)
    for c in [c for c in cand_rows if c["cfg"] == "B_mutex"]:
        d = {r["strategy"]: r for r in ind if r["fixture_id"] == c["fixture_id"] and r["seed"] == c["seed"]}
        raw_yes = [st for st in RS.STRAT_NAMES if d.get(st, {}).get("value") is True]
        kept, _ = mutex_remove(raw_yes)
        if kept != c["candidates"]:
            red.append("MUTEX_NONDET[%s/s%d]" % (c["fixture_id"], c["seed"]))
            break
    if aggregate(ind, rel, cand_rows, sel_rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDET")
    if red:
        print("INTENT_ROLE_SPLIT_D2P --check: RED")
        for m in red[:10]:
            print("  " + m)
        return 1
    print("INTENT_ROLE_SPLIT_D2P --check: GREEN (汚染ゲート[negative control]; MUTEX規則/集計 決定論再現; ロール分離)")
    _report(header["aggregate"])
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if RS.contamination_violations():
        print("ABORT 汚染: %s" % RS.contamination_violations()[:6])
        return 3
    if not RS._infra_ok():
        print("NO_INFRA")
        return 2
    ind, rel, cand_rows, sel_rows, wall = run()
    agg = aggregate(ind, rel, cand_rows, sel_rows)
    open(OUT, "w", encoding="utf-8").write(_ser(ind, rel, cand_rows, sel_rows, agg, wall))
    print("arm-D2' 実測: 独立選別%d + 相対選別%d + 選択%d  wall=%.1fs think=OFF" % (len(ind), len(rel), len(sel_rows), wall))
    _report(agg)
    print("  ※4指標を分解してから結論を書く(前回、最終だけ見て誤帰属した反省)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
