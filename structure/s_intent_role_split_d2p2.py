#!/usr/bin/env python3
"""s_intent_role_split_d2p2 — 意図調べ cheap fix: 別解書き戻し / DEFER 定義是正 / 空入力を入口で切る + DE-0547 是正。

基本形 = **員数制約付き1回観測 + 決定論確定**（arm-D2' C。「役割分割」でなく。DE-0547 で 2つ目の LLM 役割は寄与ゼロと判明）。
本 fix は精度施策でなく **ラベル/メニュー定義の誤りの是正**。ゆえスコアは上がるが大半は「緩めた分」:
★必ず (i)別解なし(唯一解基準) と (ii)別解あり(許容解基準) を併記。見出しは (i)。(ii) は「別解込み」と明記。
(ii)だけ報告＝計器を緩めて点上げ＝arm-C2 汚染の轍(禁止)。

是正内容:
- 別解 4件を acceptable_strategies に理由付き追記(Taka 承認・「どちらでも応答が実質同じ」基準のみ・auto-collapse しない)。
- DEFER 定義を狭める(旧: 文脈不足/要明確化 が INTENT_PROBE を丸飲み → 新: 不正形/解釈不能で聞き返しすら組めない)。
- 空入力(空/空白/制御文字のみ)を EMPTY_INPUT で入口 reject(LLM 呼ばない)・DF3 を除外(DF1/DF2 は文字ありゆえ残す)。
- DE-0547: MUTEX 規則2 撤回(不使用)・(c)選択役効率は候補≥2件のみで算出・auto_confirmed_n を分離報告。

usage:  s_intent_role_split_d2p2.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
import unicodedata
from collections import Counter

import s_intent_role_split as RS   # _llm / _SELECTOR_SYS を再利用(HTTP 呼出のみ)
import s_intent_probe_armc3 as A3

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_ROLE_SPLIT_D2P2.jsonl")
SEEDS = (0, 1, 2)
PROMPT_ID = "d2p2-cheapfix-v1"
MAX_PARALLEL = 16

# 7戦略 + 定義(★DEFER を狭めた)
STRATEGIES = [
    ("DIRECT", "問いが安定し回答空間が狭く、そのまま単一の答えを返せる"),
    ("CONTEXT_RESOLVE", "単体では複数解釈できるが、直前の文脈に支配的な解釈があり文脈で絞れる"),
    ("CHOICE", "主要な解釈が有限個あり、ユーザに選択肢を提示して一つ選ばせるのが妥当"),
    ("BOUNDED_MULTI_VIEW", "複数の観点を短く比較して見せること自体が答えとして妥当"),
    ("INTENT_PROBE", "対象が何を指すか意図が不明で、調査前に極小の確認質問が要る"),
    ("PREMISE_PROBE", "依頼が前提する事実/存在が怪しく、確認せずに答えてはいけない"),
    ("DEFER", "不正形・解釈不能で、意味のある聞き返しすら組み立てられない"),   # ★狭めた(文脈不足/要明確化 を削除)
]
STRAT_DEF = dict(STRATEGIES)
STRAT_NAMES = [s for s, _ in STRATEGIES]

# 別解書き戻し(Taka 承認・「どちらでも応答が実質同じ」基準・理由記録)
ACCEPTABLE = {
    "CH3": (["BOUNDED_MULTI_VIEW"], "有限の選択肢が存在せず観点比較が答え。Taka 承認"),
    "CR1": (["BOUNDED_MULTI_VIEW"], "文脈で主題は絞れるが絞った上で答えは多観点比較。排他でない"),
    "CH1": (["BOUNDED_MULTI_VIEW"], "有限選択肢でもあり観点比較でもある"),
    "IP3": (["PREMISE_PROBE"], "対象不明かつ存在前提。どちらでも応答は「聞き返す」で実質同じ"),
}
# DF3(空白のみ)は入口 reject ゆえ除外。DF1/DF2 は残す。
FIXTURES = [dict(fx, acceptable_strategies=ACCEPTABLE.get(fx["id"], ([], ""))[0])
            for fx in A3.FIXTURES if fx["id"] != "DF3"]
DF3 = next(fx for fx in A3.FIXTURES if fx["id"] == "DF3")   # 接続確認用(旧条件で NO_CANDIDATE 相当)


# ── 空入力 入口 reject(決定論・LLM 呼ばない・縦串から再利用可)──────────────────
def is_empty_input(text):
    """空文字・空白のみ・タブ/改行/制御文字のみ → True(意図調べに到達させない)。"""
    if text is None:
        return True
    stripped = re.sub(r"[\s　\x00-\x1f]", "", text)
    return stripped == ""


# ── 相対選別(1呼出・最大2 YES 員数強制)+ 選択役(候補≥2 のみ)──────────────────
def _rel_prompt(fx):
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    lst = "\n".join("- %s = %s" % (s, STRAT_DEF[s]) for s in STRAT_NAMES)
    return ("依頼:「%s」%s\n次の7戦略のうち、この依頼に当てはまるものに YES を付けよ。"
            "あなたは観測者であり分類器ではない。通常当てはまるのは1〜2個。最大2個まで。"
            "当てはまる根拠を1文で言えないものは付けない。\n%s"
            '\n出力は JSON のみ: {"yes":["戦略名", ...],"reason":"40字以内"}' % (fx["request"], ctx, lst))


def _parse_rel(raw, fr):
    if fr == "length":
        return None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None, "DIVERGE_SCHEMA"
    try:
        y = json.loads(m.group(0)).get("yes") or []
    except Exception:
        return None, "DIVERGE_SCHEMA"
    return [s for s in STRAT_NAMES if any(s in str(x) for x in y)], "OK"


def _sel_prompt(fx, cands, order):
    c = list(cands) if order == "fwd" else list(reversed(cands))
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    lst = "\n".join("- %s = %s" % (s, STRAT_DEF[s]) for s in c)
    return ("依頼:「%s」%s\n次の候補のうち最も当てはまるもの1つを選び、理由を1文で。\n%s"
            '\n出力は JSON のみ: {"choice":"戦略名","reason":"40字以内"}' % (fx["request"], ctx, lst))


def _parse_sel(raw, fr):
    if fr == "length":
        return None
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None
    try:
        c = json.loads(m.group(0)).get("choice")
    except Exception:
        return None
    return next((s for s in STRAT_NAMES if c and s in c), None)


# ── 汚染ゲート(閾値4・機能語)──────────────────────────────────────────────────
EXCLUDE_WORDS = ["として", "ですか", "ますか", "でしょう", "について", "における", "のような", "すべき", "どちら"]


def _norm(s):
    return re.sub(r"[\s、。・「」『』（）()\[\]【】,.!?！？:：;；/／]", "", unicodedata.normalize("NFKC", s or ""))


def contamination_violations():
    tmpl = _norm(RS._SELECTOR_SYS + " ".join(s + d for s, d in STRATEGIES))
    viol = []
    for fx in FIXTURES:
        req = _norm(fx["request"])
        for i in range(len(req) - 3):
            frag = req[i:i + 4]
            if frag in EXCLUDE_WORDS:
                continue
            if frag and frag in tmpl:
                viol.append({"fixture_id": fx["id"], "fragment": frag})
                break
    return viol


def _expected(fid):
    return next(fx["expected_strategy"] for fx in FIXTURES if fx["id"] == fid)


def _accept(fid):
    return next(fx["acceptable_strategies"] for fx in FIXTURES if fx["id"] == fid)


# ── 実測 ─────────────────────────────────────────────────────────────────────
def run():
    import time as _t
    t0 = _t.time()
    tasks = [(fx, s) for fx in FIXTURES for s in SEEDS]

    def _screen(t):
        fx, s = t
        raw, fr = RS._llm([{"role": "user", "content": _rel_prompt(fx)}], s)
        yes, verdict = _parse_rel(raw, fr)
        return {"row": "screen", "fixture_id": fx["id"], "seed": s, "yes": yes,
                "verdict": verdict, "raw_output": raw}
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        screen = list(ex.map(_screen, tasks))

    sel_rows = []
    for fx in FIXTURES:
        for s in SEEDS:
            cand = next((r["yes"] for r in screen if r["fixture_id"] == fx["id"] and r["seed"] == s), None) or []
            for order in ("fwd", "rev"):
                if len(cand) == 0:
                    sel_rows.append({"row": "sel", "fixture_id": fx["id"], "seed": s, "order": order,
                                     "candidates": cand, "choice": None, "status": "NO_CANDIDATE", "raw_output": ""})
                elif len(cand) == 1:
                    sel_rows.append({"row": "sel", "fixture_id": fx["id"], "seed": s, "order": order,
                                     "candidates": cand, "choice": cand[0], "status": "AUTO_CONFIRMED", "raw_output": ""})
                else:
                    raw, fr = RS._llm([{"role": "system", "content": RS._SELECTOR_SYS},
                                       {"role": "user", "content": _sel_prompt(fx, cand, order)}], s)
                    c = _parse_sel(raw, fr)
                    st = "OK" if c in cand else ("SELECTOR_OUT_OF_SET" if c else "DIVERGE")
                    sel_rows.append({"row": "sel", "fixture_id": fx["id"], "seed": s, "order": order,
                                     "candidates": cand, "choice": c if c in cand else None,
                                     "raw_choice": c, "status": st, "raw_output": raw})
    wall = round(_t.time() - t0, 2)
    return screen, sel_rows, wall


def _final(sel_rows, fid, s):
    r = next((x for x in sel_rows if x["fixture_id"] == fid and x["seed"] == s and x["order"] == "fwd"), None)
    return r["choice"] if r else None


def aggregate(screen, sel_rows):
    n = len(FIXTURES) * len(SEEDS)
    hit_i = hit_ii = answered = upper = 0
    per_fix = {}
    for fx in FIXTURES:
        gots = []
        for s in SEEDS:
            got = _final(sel_rows, fx["id"], s)
            gots.append(got)
            exp, acc = fx["expected_strategy"], fx["acceptable_strategies"]
            cand = next((r["yes"] for r in screen if r["fixture_id"] == fx["id"] and r["seed"] == s), []) or []
            if got is not None:
                answered += 1
            if exp in cand or any(a in cand for a in acc):
                upper += 1
            if got == exp:
                hit_i += 1
            if got == exp or got in acc:
                hit_ii += 1
        per_fix[fx["id"]] = gots
    # (c) 選択役効率: 候補≥2 の件のみ(DE-0547 是正)。auto_confirmed 別途。
    ge2 = [r for r in sel_rows if r["order"] == "fwd" and len(r["candidates"]) >= 2]
    ge2_hit = sum(1 for r in ge2 if r["choice"] == _expected(r["fixture_id"])
                  or r["choice"] in _accept(r["fixture_id"]))
    auto = sum(1 for r in sel_rows if r["order"] == "fwd" and r["status"] == "AUTO_CONFIRMED")
    nocand = sum(1 for r in sel_rows if r["order"] == "fwd" and r["status"] == "NO_CANDIDATE")
    yes_counts = [len(next((r["yes"] for r in screen if r["fixture_id"] == fx["id"] and r["seed"] == s), []) or [])
                  for fx in FIXTURES for s in SEEDS]
    pb_t = pb_a = 0
    for fx in FIXTURES:
        for s in SEEDS:
            f = next((r for r in sel_rows if r["fixture_id"] == fx["id"] and r["seed"] == s and r["order"] == "fwd"), None)
            rv = next((r for r in sel_rows if r["fixture_id"] == fx["id"] and r["seed"] == s and r["order"] == "rev"), None)
            if f and rv and f["choice"] and rv["choice"]:
                pb_t += 1
                pb_a += int(f["choice"] == rv["choice"])
    return {
        "final_no_alt_i": round(hit_i / n, 4), "final_no_alt_raw": "%d/%d" % (hit_i, n),
        "final_with_alt_ii": round(hit_ii / n, 4), "final_with_alt_raw": "%d/%d" % (hit_ii, n),
        "candidate_upper_with_alt": round(upper / n, 4),
        "selector_eff_ge2_only": round(ge2_hit / len(ge2), 4) if ge2 else None,
        "selector_ge2_raw": "%d/%d" % (ge2_hit, len(ge2)),
        "auto_confirmed_n": auto, "no_candidate_n": nocand,
        "yes_mean": round(sum(yes_counts) / len(yes_counts), 2), "yes_ge3": sum(1 for c in yes_counts if c >= 3),
        "order_agreement": round(pb_a / pb_t, 4) if pb_t else None,
        "IP1": per_fix.get("IP1"), "IP2": per_fix.get("IP2"),
        "DF1": per_fix.get("DF1"), "DF2": per_fix.get("DF2"),
        # 接続: 旧条件(DF3込み・別解なし)。DF3 は空入力ゆえ 3×NO_CANDIDATE(決定論・LLM 不使用)。
        "connect_df3incl_no_alt": round(hit_i / (n + 3), 4), "connect_raw": "%d/%d" % (hit_i, n + 3),
        "note": "見出しは(i)別解なし。(ii)は別解込み(緩めた分)。arm-C2 0.83(汚染)とは並べない。能力主張でない・A3B。",
    }


def _ser(screen, sel_rows, agg, wall):
    hdr = {"_meta": "INTENT_ROLE_SPLIT_D2P2(cheap fix: 別解/DEFER是正/空入力reject/DE-0547)。基本形=員数制約付き1回観測+決定論確定。",
           "aggregate": agg, "wall_seconds": wall, "prompt_id": PROMPT_ID, "seeds": list(SEEDS),
           "defer_def": STRAT_DEF["DEFER"], "acceptable": {k: v for k, v in ACCEPTABLE.items()},
           "n_fixtures": len(FIXTURES), "exclude_words": EXCLUDE_WORDS}
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in screen + sel_rows]) + "\n"


def _report(a):
    print("  ★(i)別解なし=%s [%s]  (ii)別解あり=%s [%s]  接続(DF3込み別解なし)=%s [%s]"
          % (a["final_no_alt_i"], a["final_no_alt_raw"], a["final_with_alt_ii"], a["final_with_alt_raw"],
             a["connect_df3incl_no_alt"], a["connect_raw"]))
    print("  候補上限(別解込)=%s (c)選択役効率(候補≥2のみ)=%s [%s] auto_confirmed=%d NO_CAND=%d"
          % (a["candidate_upper_with_alt"], a["selector_eff_ge2_only"], a["selector_ge2_raw"],
             a["auto_confirmed_n"], a["no_candidate_n"]))
    print("  YES平均=%.2f(≥3:%d) 順序一致=%s | DEFER是正確認: IP1=%s IP2=%s / DF1=%s DF2=%s"
          % (a["yes_mean"], a["yes_ge3"], a["order_agreement"], a["IP1"], a["IP2"], a["DF1"], a["DF2"]))


def check():
    red = []
    if contamination_violations():
        red.append("CONTAMINATION: %s" % contamination_violations()[:6])
    _sv = STRATEGIES[0]
    try:
        STRATEGIES[0] = (_sv[0], _sv[1] + FIXTURES[0]["request"])
        STRAT_DEF[_sv[0]] = STRATEGIES[0][1]
        if not contamination_violations():
            red.append("CONTAMINATION_GATE_DEAD")
    finally:
        STRATEGIES[0] = _sv
        STRAT_DEF[_sv[0]] = _sv[1]
    # 空入力 reject の負の制御(LLM 呼ばない): DF3 と空白系を is_empty_input が拾う
    if not (is_empty_input(DF3["request"]) and is_empty_input("   \t\n  ") and is_empty_input("")):
        red.append("EMPTY_REJECT_DEAD: 空白入力を is_empty_input が拾えない")
    if is_empty_input("asdf") or is_empty_input(DF3["request"] and "。。。"):
        red.append("EMPTY_REJECT_OVERREACH: 文字ありを空扱いした")
    if not os.path.isfile(OUT):
        red.append("NOT_GENERATED")
        print("INTENT_ROLE_SPLIT_D2P2 --check: RED")
        for m in red:
            print("  " + m)
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header = lines[0]
    screen = [l for l in lines[1:] if l.get("row") == "screen"]
    sel_rows = [l for l in lines[1:] if l.get("row") == "sel"]
    if aggregate(screen, sel_rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDET")
    if red:
        print("INTENT_ROLE_SPLIT_D2P2 --check: RED")
        for m in red[:10]:
            print("  " + m)
        return 1
    print("INTENT_ROLE_SPLIT_D2P2 --check: GREEN (汚染ゲート[negative control]; 空入力reject[LLM不使用]; (i)(ii)(c)決定論再現)")
    _report(header["aggregate"])
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if contamination_violations():
        print("ABORT 汚染: %s" % contamination_violations()[:6])
        return 3
    if not RS._infra_ok():
        print("NO_INFRA")
        return 2
    screen, sel_rows, wall = run()
    agg = aggregate(screen, sel_rows)
    open(OUT, "w", encoding="utf-8").write(_ser(screen, sel_rows, agg, wall))
    print("d2p2 実測: 選別%d + 選択%d (%d fixture×%d seed・DF3は入口reject) wall=%.1fs think=OFF"
          % (len(screen), len(sel_rows), len(FIXTURES), len(SEEDS), wall))
    _report(agg)
    print("  ※見出しは(i)別解なし。(ii)は緩めた分込み。arm-C3 0.5397 / arm-D2' C 0.7143(旧DEFER・DF3込)と接続で比較。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
