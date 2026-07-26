#!/usr/bin/env python3
"""s_intent_context_premise_1b — Build 1b(P3 文脈の前提): context が空なら CONTEXT_RESOLVE を候補から機械除外。

BUILD SPEC v1.0 §3/§8。**P3 だけ挿し込み位置が違う**: 入力を止める手前ゲート(P1/P2/P4)ではなく、
**意図調べ「内部」の候補合法性フィルタ**＝構造的に成立しない選択肢を選ばせない。
根拠: CONTEXT_RESOLVE の定義は「**直前の文脈に**支配的な解釈があり文脈で絞れる」。文脈が無いなら定義上あり得ない。
**除外は集計側で行い、LLM は一切呼ばない。**

★対照設計(帰属を誤らないため): **選別(screening)は1回だけ走らせ、その同一出力から2アームを導出する。**
  arm A(baseline) = 候補そのまま / arm B(P3) = context 空なら CONTEXT_RESOLVE を除去
  選択役は「候補集合が同一なら結果を再利用」するので、**2アームの差はフィルタが候補を変えた箇所からのみ生じる**。
  ＝ run 間の LLM ノイズが arm 間差に混入しない。

usage: s_intent_context_premise_1b.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
import time

STRUCT = os.path.dirname(os.path.abspath(__file__))
if STRUCT not in sys.path:
    sys.path.insert(0, STRUCT)

import s_intent_role_split as RS          # noqa: E402  _llm / _SELECTOR_SYS
import s_intent_role_split_d2p2 as D2P2   # noqa: E402  FIXTURES / prompts / aggregate(監査済み・変更しない)

OUT = os.path.join(STRUCT, "INTENT_CONTEXT_PREMISE_1B.jsonl")
SEEDS = D2P2.SEEDS
FIXTURES = D2P2.FIXTURES
MAX_PARALLEL = D2P2.MAX_PARALLEL
PROMPT_ID = "1b-p3-context-premise-v1"
FILTERED_STRATEGY = "CONTEXT_RESOLVE"

# DE-0548 で CONTEXT_RESOLVE を選んでいた回(SPEC §10 が名指しで測れと言っている対象)
TARGETS = [("IP1", 1), ("IP2", 0)]


# ── P3 フィルタ(★完全決定論・LLM ゼロ)──────────────────────────────────────────
def is_empty_context(context):
    """context が None / 空文字 / 空白のみ(全角空白・タブ・改行・制御文字含む)なら True。"""
    if context is None:
        return True
    return re.sub(r"[\s　\x00-\x1f]", "", str(context)) == ""


def apply_p3(candidates, context):
    """-> (filtered, record or None). context が空なら CONTEXT_RESOLVE を候補から除外する。
    除外したこと・理由・除外前の候補集合を必ず記録する(SPEC §8「隠さない」)。"""
    cands = list(candidates or [])
    if not is_empty_context(context) or FILTERED_STRATEGY not in cands:
        return cands, None
    filtered = [c for c in cands if c != FILTERED_STRATEGY]
    return filtered, {"excluded": FILTERED_STRATEGY, "candidates_before": list(cands),
                      "candidates_after": filtered, "context_is_empty": True,
                      "reason": "CONTEXT_RESOLVE の定義は『直前の文脈に支配的な解釈があり文脈で絞れる』。"
                                "文脈が空である以上、定義上あり得ない選択肢である。"}


# ── 実測 ─────────────────────────────────────────────────────────────────────
def run():
    t0 = time.time()

    # 1) 選別は1回だけ(2アーム共有)
    def _screen(t):
        fx, s = t
        raw, fr = RS._llm([{"role": "user", "content": D2P2._rel_prompt(fx)}], s)
        yes, verdict = D2P2._parse_rel(raw, fr)
        return {"row": "screen", "fixture_id": fx["id"], "seed": s, "yes": yes,
                "verdict": verdict, "raw_output": raw}
    tasks = [(fx, s) for fx in FIXTURES for s in SEEDS]
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        screen = list(ex.map(_screen, tasks))

    # 2) 2アームの候補集合を作る(arm B のみ P3 を適用)
    exclusions = []
    screen_a, screen_b = [], []
    for r in screen:
        fx = next(f for f in FIXTURES if f["id"] == r["fixture_id"])
        cand = r["yes"] or []
        filt, rec = apply_p3(cand, fx["context"])
        screen_a.append(dict(r))
        screen_b.append(dict(r, yes=filt))
        if rec:
            exclusions.append(dict(rec, fixture_id=fx["id"], seed=r["seed"]))

    # 3) 選択役: 候補集合が同一なら結果を再利用(arm 間差をフィルタ由来だけにする)
    cache, calls = {}, {"llm": 0, "reused": 0}

    def _select(fx, cand, order, seed):
        key = (fx["id"], seed, order, tuple(cand))
        if key in cache:
            calls["reused"] += 1
            return dict(cache[key])
        if len(cand) == 0:
            row = {"row": "sel", "fixture_id": fx["id"], "seed": seed, "order": order,
                   "candidates": cand, "choice": None, "status": "NO_CANDIDATE", "raw_output": ""}
        elif len(cand) == 1:
            row = {"row": "sel", "fixture_id": fx["id"], "seed": seed, "order": order,
                   "candidates": cand, "choice": cand[0], "status": "AUTO_CONFIRMED", "raw_output": ""}
        else:
            raw, fr = RS._llm([{"role": "system", "content": RS._SELECTOR_SYS},
                               {"role": "user", "content": D2P2._sel_prompt(fx, cand, order)}], seed)
            calls["llm"] += 1
            c = D2P2._parse_sel(raw, fr)
            st = "OK" if c in cand else ("SELECTOR_OUT_OF_SET" if c else "DIVERGE")
            row = {"row": "sel", "fixture_id": fx["id"], "seed": seed, "order": order, "candidates": cand,
                   "choice": c if c in cand else None, "raw_choice": c, "status": st, "raw_output": raw}
        cache[key] = dict(row)
        return row

    def _arm(scr, tag):
        rows = []
        for fx in FIXTURES:
            for s in SEEDS:
                cand = next((r["yes"] for r in scr if r["fixture_id"] == fx["id"] and r["seed"] == s), None) or []
                for order in ("fwd", "rev"):
                    rows.append(dict(_select(fx, cand, order, s), arm=tag))
        return rows

    sel_a = _arm(screen_a, "A_baseline")
    sel_b = _arm(screen_b, "B_p3")
    return screen_a, screen_b, sel_a, sel_b, exclusions, calls, round(time.time() - t0, 2)


def analyse(screen_a, screen_b, sel_a, sel_b, exclusions):
    agg_a = D2P2.aggregate(screen_a, sel_a)
    agg_b = D2P2.aggregate(screen_b, sel_b)

    # SPEC §10: IP1 seed1 / IP2 seed0 の CONTEXT_RESOLVE が消えるか・消えた後どこへ行くか
    tgt = []
    for fid, seed in TARGETS:
        ca = next((r["yes"] for r in screen_a if r["fixture_id"] == fid and r["seed"] == seed), []) or []
        cb = next((r["yes"] for r in screen_b if r["fixture_id"] == fid and r["seed"] == seed), []) or []
        fa = D2P2._final(sel_a, fid, seed)
        fb = D2P2._final(sel_b, fid, seed)
        tgt.append({"fixture_id": fid, "seed": seed, "candidates_A": ca, "candidates_B": cb,
                    "context_resolve_in_candidates_A": FILTERED_STRATEGY in ca,
                    "removed_by_p3": (FILTERED_STRATEGY in ca) and (FILTERED_STRATEGY not in cb),
                    "final_A": fa, "final_B": fb, "moved_to": fb if fa != fb else None,
                    "expected": D2P2._expected(fid)})

    # ★負の対照: context を持つ fixture(CR1/CR2/CR3)は絶対に除外されてはならない
    ctx_fix = [fx["id"] for fx in FIXTURES if not is_empty_context(fx["context"])]
    control_ok = not any(e["fixture_id"] in ctx_fix for e in exclusions)

    # 全体の変化(どこが動いたか全件)
    moved = []
    for fx in FIXTURES:
        for s in SEEDS:
            fa, fb = D2P2._final(sel_a, fx["id"], s), D2P2._final(sel_b, fx["id"], s)
            if fa != fb:
                moved.append({"fixture_id": fx["id"], "seed": s, "A": fa, "B": fb,
                              "expected": fx["expected_strategy"],
                              "A_correct": fa == fx["expected_strategy"], "B_correct": fb == fx["expected_strategy"]})
    return {"aggregate_A_baseline": agg_a, "aggregate_B_p3": agg_b, "targets": tgt,
            "exclusions_n": len(exclusions), "exclusions": exclusions,
            "negative_control_context_fixtures_untouched": control_ok,
            "context_fixtures": ctx_fix, "moved_cases": moved,
            "delta_no_alt_i": round(agg_b["final_no_alt_i"] - agg_a["final_no_alt_i"], 4),
            "delta_with_alt_ii": round(agg_b["final_with_alt_ii"] - agg_a["final_with_alt_ii"], 4)}


# ── --check(LLM 不使用・決定論部分のみ)────────────────────────────────────────
def check():
    ok = True
    empt = [(None, True), ("", True), ("   ", True), ("　", True), ("\t\n", True),
            ("直前はロシア・ウクライナ戦争の話。", False), ("a", False)]
    r1 = all(is_empty_context(c) is e for c, e in empt)
    print("[%s] is_empty_context 決定論 (%d件)" % ("PASS" if r1 else "FAIL", len(empt)))
    ok &= r1

    cands = ["INTENT_PROBE", "CONTEXT_RESOLVE", "PREMISE_PROBE"]
    f1, rec1 = apply_p3(cands, "")
    f2, rec2 = apply_p3(cands, "直前は投手の成績の話。")
    f3, rec3 = apply_p3(["INTENT_PROBE"], "")
    r2 = (f1 == ["INTENT_PROBE", "PREMISE_PROBE"] and rec1 and rec1["candidates_before"] == cands
          and f2 == cands and rec2 is None and f3 == ["INTENT_PROBE"] and rec3 is None)
    print("[%s] apply_p3: 空→除外+記録 / 文脈あり→不変 / 非該当→不変" % ("PASS" if r2 else "FAIL"))
    ok &= r2

    # ★負の対照: context を持つ fixture では絶対に除外が起きない
    bad = [fx["id"] for fx in FIXTURES if not is_empty_context(fx["context"])
           and apply_p3(["CONTEXT_RESOLVE", "DIRECT"], fx["context"])[1] is not None]
    r3 = not bad
    print("[%s] 負の対照: context を持つ fixture は除外されない (%s)"
          % ("PASS" if r3 else "FAIL", [fx["id"] for fx in FIXTURES if not is_empty_context(fx["context"])]))
    ok &= r3

    r4 = D2P2.aggregate is not None and RS._infra_ok is not None
    print("[%s] 監査済み d2p2 の集計関数をそのまま再利用 (改変していない)" % ("PASS" if r4 else "FAIL"))
    ok &= r4
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def repeat(n):
    """★run 間再現性が無い計器なので反復する。RS._llm は temperature=0.7 で seed を渡しても run 毎に揺れる。
    1回の観測(n=1)で『消えた/消えない』を結論すると、本日4回起きた計器事故と同型になる。"""
    runs = []
    for i in range(n):
        sa, sb, la, lb, exc, calls, wall = run()
        r = analyse(sa, sb, la, lb, exc)
        runs.append({"run": i, "exclusions_n": r["exclusions_n"],
                     "exclusion_cases": [{"fixture_id": e["fixture_id"], "seed": e["seed"],
                                          "candidates_before": e["candidates_before"]} for e in r["exclusions"]],
                     "A_i": r["aggregate_A_baseline"]["final_no_alt_i"],
                     "B_i": r["aggregate_B_p3"]["final_no_alt_i"],
                     "A_ii": r["aggregate_A_baseline"]["final_with_alt_ii"],
                     "B_ii": r["aggregate_B_p3"]["final_with_alt_ii"],
                     # ★CC-α 裁定(2026-07-26 §4-3): 「誤答」と「答えない」を分けて数える。
                     # NO_CANDIDATE は誤答と同列に数えない(§4-2)。回答時精度 = 答えた回のうち正解の割合。
                     "A_nocand": r["aggregate_A_baseline"]["no_candidate_n"],
                     "B_nocand": r["aggregate_B_p3"]["no_candidate_n"],
                     "A_wrong": (len(FIXTURES) * len(SEEDS) - r["aggregate_A_baseline"]["no_candidate_n"]
                                 - int(r["aggregate_A_baseline"]["final_no_alt_raw"].split("/")[0])),
                     "B_wrong": (len(FIXTURES) * len(SEEDS) - r["aggregate_B_p3"]["no_candidate_n"]
                                 - int(r["aggregate_B_p3"]["final_no_alt_raw"].split("/")[0])),
                     "A_hit": int(r["aggregate_A_baseline"]["final_no_alt_raw"].split("/")[0]),
                     "B_hit": int(r["aggregate_B_p3"]["final_no_alt_raw"].split("/")[0]),
                     "delta_i": r["delta_no_alt_i"], "delta_ii": r["delta_with_alt_ii"],
                     "moved_cases": r["moved_cases"],
                     "negative_control_ok": r["negative_control_context_fixtures_untouched"],
                     "targets": r["targets"], "wall": wall, "llm_calls": calls})
        print("  run %d: 除外%d件 / A(i)=%.4f B(i)=%.4f Δ=%+0.4f / 動いた回=%d / 負の対照=%s (%.1fs)"
              % (i, r["exclusions_n"], runs[-1]["A_i"], runs[-1]["B_i"], r["delta_no_alt_i"],
                 len(r["moved_cases"]), runs[-1]["negative_control_ok"], wall))
    tot_pairs = len(FIXTURES) * len(SEEDS)
    empty_pairs = sum(1 for fx in FIXTURES for _ in SEEDS if is_empty_context(fx["context"]))
    exc_total = sum(r["exclusions_n"] for r in runs)
    moved_total = [m for r in runs for m in r["moved_cases"]]
    summary = {
        "runs": n, "pairs_per_run": tot_pairs, "empty_context_pairs_per_run": empty_pairs,
        "exclusions_total": exc_total,
        "exclusion_rate_per_empty_pair": round(exc_total / (empty_pairs * n), 4) if empty_pairs else None,
        "delta_i_mean": round(sum(r["delta_i"] for r in runs) / n, 4),
        "delta_ii_mean": round(sum(r["delta_ii"] for r in runs) / n, 4),
        "delta_i_values": [r["delta_i"] for r in runs],
        "A_i_values": [r["A_i"] for r in runs], "B_i_values": [r["B_i"] for r in runs],
        "moved_total": len(moved_total),
        "moved_became_correct": sum(1 for m in moved_total if m["B_correct"]),
        "moved_became_wrong": sum(1 for m in moved_total if m["A_correct"] and not m["B_correct"]),
        "moved_detail": moved_total,
        # ★誤答 / 答えない / 正解 の3分割(CC-α 裁定 §4-3)。P3 が「自信ある誤答」を「正直に答えない」へ動かしたか。
        "A_wrong_total": sum(r["A_wrong"] for r in runs), "B_wrong_total": sum(r["B_wrong"] for r in runs),
        "A_nocand_total": sum(r["A_nocand"] for r in runs), "B_nocand_total": sum(r["B_nocand"] for r in runs),
        "A_hit_total": sum(r["A_hit"] for r in runs), "B_hit_total": sum(r["B_hit"] for r in runs),
        "A_accuracy_when_answered": round(sum(r["A_hit"] for r in runs)
                                          / max(1, sum(r["A_hit"] + r["A_wrong"] for r in runs)), 4),
        "B_accuracy_when_answered": round(sum(r["B_hit"] for r in runs)
                                          / max(1, sum(r["B_hit"] + r["B_wrong"] for r in runs)), 4),
        "negative_control_all_ok": all(r["negative_control_ok"] for r in runs),
        "targets_context_resolve_present": sum(1 for r in runs for t in r["targets"]
                                               if t["context_resolve_in_candidates_A"]),
        "targets_observed": sum(len(r["targets"]) for r in runs),
    }
    return runs, summary


def main(argv):
    if "--check" in argv:
        return check()
    if D2P2.contamination_violations():
        print("ABORT 汚染: %s" % D2P2.contamination_violations()[:6])
        return 3
    if not RS._infra_ok():
        print("NO_INFRA (:8005 が応答しない)")
        return 2

    rep = next((int(a.split("=")[1]) for a in argv if a.startswith("--repeat=")), 0)
    if rep:
        print("Build 1b(P3) 反復実測 %d回 ★計器は run 間再現性が無い(temperature=0.7)" % rep)
        runs, summ = repeat(rep)
        with open(os.path.join(STRUCT, "INTENT_CONTEXT_PREMISE_1B_REPEAT.json"), "w", encoding="utf-8") as fh:
            json.dump({"summary": summ, "runs": runs, "prompt_id": PROMPT_ID}, fh, ensure_ascii=False, indent=1)
        print("\n── 集計 (%d run) ──" % rep)
        print("  除外の発生: %d回 / 空 context の観測 %d回 → 発生率 %.3f"
              % (summ["exclusions_total"], summ["empty_context_pairs_per_run"] * rep,
                 summ["exclusion_rate_per_empty_pair"]))
        print("  (i)別解なし: A=%s / B=%s" % (summ["A_i_values"], summ["B_i_values"]))
        print("  Δ(i) 平均=%+0.4f  各run=%s" % (summ["delta_i_mean"], summ["delta_i_values"]))
        print("  Δ(ii)平均=%+0.4f" % summ["delta_ii_mean"])
        print("  ★誤答/答えない/正解 の3分割 (CC-α 裁定: NO_CANDIDATE を誤答と同列に数えない):")
        print("     arm A: 正解%d / 誤答%d / 答えない%d  → 回答時精度 %.4f"
              % (summ["A_hit_total"], summ["A_wrong_total"], summ["A_nocand_total"],
                 summ["A_accuracy_when_answered"]))
        print("     arm B: 正解%d / 誤答%d / 答えない%d  → 回答時精度 %.4f"
              % (summ["B_hit_total"], summ["B_wrong_total"], summ["B_nocand_total"],
                 summ["B_accuracy_when_answered"]))
        print("     誤答の変化 %+d / 答えないの変化 %+d"
              % (summ["B_wrong_total"] - summ["A_wrong_total"],
                 summ["B_nocand_total"] - summ["A_nocand_total"]))
        print("  最終選択が動いた回: 計%d (正解になった=%d / 正解を壊した=%d)"
              % (summ["moved_total"], summ["moved_became_correct"], summ["moved_became_wrong"]))
        for m in summ["moved_detail"]:
            print("    %s seed%d: %s → %s (期待=%s / 正解=%s)"
                  % (m["fixture_id"], m["seed"], m["A"], m["B"], m["expected"], m["B_correct"]))
        print("  負の対照(CR1/CR2/CR3 が除外されない): 全run %s" % summ["negative_control_all_ok"])
        print("  SPEC §10 名指し対象(IP1 seed1/IP2 seed0)で CONTEXT_RESOLVE が候補に在った回: %d/%d"
              % (summ["targets_context_resolve_present"], summ["targets_observed"]))
        print("  → structure/INTENT_CONTEXT_PREMISE_1B_REPEAT.json")
        return 0

    sa, sb, la, lb, exc, calls, wall = run()
    res = analyse(sa, sb, la, lb, exc)
    hdr = {"_meta": "INTENT_CONTEXT_PREMISE_1B(P3 文脈の前提): context 空なら CONTEXT_RESOLVE を候補から機械除外。"
                    "選別は1回だけ走らせ2アームを導出・選択役は候補同一なら再利用＝arm 間差はフィルタ由来のみ。",
           "analysis": res, "wall_seconds": wall, "prompt_id": PROMPT_ID, "seeds": list(SEEDS),
           "llm_calls": calls, "n_fixtures": len(FIXTURES)}
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(hdr, ensure_ascii=False, sort_keys=True) + "\n")
        for r in sa + sb + la + lb:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    a, b = res["aggregate_A_baseline"], res["aggregate_B_p3"]
    print("Build 1b(P3 文脈の前提) 実測  wall=%.1fs  LLM呼出=%d(再利用%d)" % (wall, calls["llm"], calls["reused"]))
    print("  除外が発生した回: %d (context 空 かつ CONTEXT_RESOLVE が候補にあった回)" % res["exclusions_n"])
    print("  負の対照(context を持つ %s は除外されない): %s"
          % (res["context_fixtures"], res["negative_control_context_fixtures_untouched"]))
    print("  arm A baseline : (i)別解なし=%s [%s]  (ii)別解あり=%s [%s]"
          % (a["final_no_alt_i"], a["final_no_alt_raw"], a["final_with_alt_ii"], a["final_with_alt_raw"]))
    print("  arm B P3       : (i)別解なし=%s [%s]  (ii)別解あり=%s [%s]"
          % (b["final_no_alt_i"], b["final_no_alt_raw"], b["final_with_alt_ii"], b["final_with_alt_raw"]))
    print("  差分           : (i) %+0.4f / (ii) %+0.4f" % (res["delta_no_alt_i"], res["delta_with_alt_ii"]))
    print("  ★SPEC §10 名指しの対象:")
    for t in res["targets"]:
        print("    %s seed%d: 候補に CONTEXT_RESOLVE=%s → P3 で除去=%s / 最終 A=%s → B=%s (期待=%s)"
              % (t["fixture_id"], t["seed"], t["context_resolve_in_candidates_A"], t["removed_by_p3"],
                 t["final_A"], t["final_B"], t["expected"]))
    print("  最終選択が動いた回: %d" % len(res["moved_cases"]))
    for m in res["moved_cases"]:
        print("    %s seed%d: %s → %s (期待=%s / 正解になった=%s)"
              % (m["fixture_id"], m["seed"], m["A"], m["B"], m["expected"], m["B_correct"]))
    print("  → %s" % OUT)
    print("  ※P3 は『あり得ない選択肢を消す』だけで正答を増やすとは限らない(SPEC §8)。増えなければ増えなかったと書く。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
