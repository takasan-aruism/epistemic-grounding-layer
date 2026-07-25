#!/usr/bin/env python3
"""s_intent_probe_armc2 — arm-C2: 二択に「定義+具体例」/ think on-off / seed多数決 / abstain(unsure)。

arm-C の弱点(b_probe_type / b_multi_type の細分・seed一貫5/8)を、**LLM に細分させないまま**締める:
- 各二択に**用語定義(1文)+対比する具体例**(few-shot・RRI §9 準拠・固定記録)。
- **unsure(abstain)許容**: 定義+例でも弁別できなければ正直に unsure → 決定論集計は UNRESOLVED_AGG(捏造で埋めない・measure-first)。
- **think OFF/ON 両測**(tiny ゆえ ON でも終端しやすい・論理系二択が think で改善するかを見る)。
- **seed 多数決**(各二択 N seed→多数決・tie=unsure)で一貫性改善を測る。3B 並列ゆえ安い。
- **弁別は決定論集計ツリー(§9)のまま**(LLM は二択のみ)。

record-occurrence: main が Qwen 実行し raw を記録。--check は LLM 再実行せず記録に parser/多数決/集計ツリーを再適用。

usage:  s_intent_probe_armc2.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys
from collections import Counter

import s_intent_probe_proto as P   # FIXTURES / PROBE_STRATS 共有

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_PROBE_ARMC2.jsonl")
MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
PROMPT_ID = "armc2-defs-v1"
MAX_PARALLEL = 16
THINK_CONFIGS = [("off", False, 128), ("on", True, 4096)]   # (think_id, enable_thinking, max_tokens)

# 二択(A=第1/B=第2)+定義+具体例+unsure。A/B ラベルの意味は集計ツリーが持つ。
_TAIL = '\n出力は JSON のみ: {{"choice":"A" または "B" または "unsure","note":"10字以内"}}'
BINARIES = [
    ("b_malformed",
     "依頼:「{req}」\nこの依頼は意味の通る依頼か、記号の羅列等で解釈不能な不正形か。"
     "例:「Windows10 の発売日は?」→意味が通る /「asdf ;; //」→不正形。\n→ A(意味が通る) / B(不正形)"),
    ("b_needs_probe",
     "依頼:「{req}」{ctx}\nそのまま解釈して回答/調査を始められるか、始める前に一度確認(聞き返し)が要るか。"
     "定義: 対象と意図が十分特定できていれば始められる。指示語で対象不明・前提が怪しい等なら聞き返しが要る。"
     "例:「Windows10 の発売日は?」→始められる /「あれどこ?」→聞き返しが要る。\n→ A(始められる) / B(聞き返しが要る)"),
    ("b_probe_type",
     "依頼:「{req}」\n確認が要るとして、不確かなのは『対象が何を指すか(INTENT)』か『前提した事実/存在が在るか(PREMISE)』か。"
     "定義: INTENT=対象自体が不明(指示語 あれ/それ)。PREMISE=対象は名指しできるが、その存在/成立を確認せず信じられない。"
     "例:「あれどこにあったっけ?」→INTENT(対象不明) /「以前作った Watcher 仕様どこ?」→PREMISE(仕様の存在が前提・怪しい)。"
     "\n→ A(INTENT=対象不明) / B(PREMISE=前提/存在が怪しい)"),
    ("b_determinacy",
     "依頼:「{req}」{ctx}\n合理的な回答は概ね1つに絞れるか、絞れず複数ありうるか。"
     "例:「1024 は 2 の何乗?」→1つに絞れる /「プーチンの今後は?」→複数ありうる。\n→ A(1つに絞れる) / B(複数ありうる)"),
    ("b_context",
     "依頼:「{req}」{ctx}\n直前の文脈を踏まえると、支配的な解釈があり文脈で絞れるか、文脈でも絞れないか。"
     "例: 直前がウクライナ戦争の議論で「プーチンの今後は?」→文脈で絞れる / 文脈なしなら→絞れない。"
     "\n→ A(文脈で絞れる) / B(絞れない)"),
    ("b_multi_type",
     "依頼:「{req}」\n複数ありうるとして、一つ選ばせる有限選択肢型か、複数観点を比較提示する型か。"
     "定義: CHOICE=主要 branch が有限でユーザは一つを選びたい(選択肢提示)。BMV=複数観点を比較して見せること自体が答え。"
     "例:「どの DB を使う?(Postgres/MySQL/SQLite)」→CHOICE(有限選択肢) /「X のメリット・デメリットは?」→BMV(観点比較が答え)。"
     "\n→ A(CHOICE=有限選択肢) / B(BMV=観点比較)"),
]

# 弱2二択の expected(的中率評価用)。A/B の意味は上の prompt に一致。
EXPECTED_BINARY = {
    "F6_INTENT_PROBE": {"b_probe_type": "A"},   # INTENT
    "F7_PREMISE_PROBE": {"b_probe_type": "B"},  # PREMISE
    "F4_CHOICE": {"b_multi_type": "A"},         # CHOICE
    "F5_BMV": {"b_multi_type": "B"},            # BMV
}


def _prompt(tmpl, fx):
    ctx = ("（直前文脈: %s）" % fx["context"]) if fx["context"] else ""
    return tmpl.format(req=fx["request"], ctx=ctx) + _TAIL


def _llm(prompt, seed, think, mt):
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "temperature": 0.7, "max_tokens": mt,
                       "chat_template_kwargs": {"enable_thinking": think}}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason"), out.get("usage", {}).get("completion_tokens")


def parse_binary(raw, finish_reason):
    if finish_reason == "length":
        return None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if m:
        try:
            c = json.loads(m.group(0)).get("choice")
            if c in ("A", "B", "unsure"):
                return c, "OK"
        except Exception:
            pass
    return None, "DIVERGE_SCHEMA"


# ── 決定論集計ツリー(§9・unsure/None は無理に倒さず UNRESOLVED_AGG)──────────────
def strategy_from_binaries(b):
    def d(k):
        v = b.get(k)
        return v if v in ("A", "B") else None   # unsure/None は決められない
    if d("b_malformed") is None:
        return "UNRESOLVED_AGG"
    if d("b_malformed") == "B":
        return "DEFER"
    if d("b_needs_probe") is None:
        return "UNRESOLVED_AGG"
    if d("b_needs_probe") == "B":
        pt = d("b_probe_type")
        if pt is None:
            return "UNRESOLVED_AGG"
        return "INTENT_PROBE" if pt == "A" else "PREMISE_PROBE"   # A=INTENT, B=PREMISE
    if d("b_determinacy") is None:
        return "UNRESOLVED_AGG"
    if d("b_determinacy") == "A":
        return "DIRECT"
    if d("b_context") is None:
        return "UNRESOLVED_AGG"
    if d("b_context") == "A":
        return "CONTEXT_RESOLVE"
    if d("b_multi_type") is None:
        return "UNRESOLVED_AGG"
    return "CHOICE" if d("b_multi_type") == "A" else "BOUNDED_MULTI_VIEW"


def _majority(vals):
    """seed 答え list → 多数決(A/B/unsure)。tie or 過半なし → unsure。"""
    c = Counter(v for v in vals if v is not None)
    if not c:
        return "unsure"
    top, n = c.most_common(1)[0]
    if n > len(vals) / 2:
        return top
    return "unsure"


def run():
    tasks = [(tid, think, mt, fx, bid, tmpl, s)
             for (tid, think, mt) in THINK_CONFIGS
             for fx in P.FIXTURES for bid, tmpl in BINARIES for s in SEEDS]

    def _one(t):
        tid, think, mt, fx, bid, tmpl, s = t
        raw, fr, ct = _llm(_prompt(tmpl, fx), s, think, mt)
        choice, verdict = parse_binary(raw, fr)
        return {"think": tid, "fixture_id": fx["id"], "binary_id": bid, "seed": s,
                "raw_output": raw, "finish_reason": fr, "completion_tokens": ct,
                "choice": choice, "parse_verdict": verdict}
    import time as _t
    wall = {}
    bin_rows = []
    for tid, think, mt in THINK_CONFIGS:
        sub = [t for t in tasks if t[0] == tid]
        t0 = _t.time()
        with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
            bin_rows += list(ex.map(_one, sub))
        wall[tid] = round(_t.time() - t0, 2)
    bin_rows.sort(key=lambda r: (r["think"], r["fixture_id"], r["binary_id"], r["seed"]))
    return bin_rows, wall


def _strategies(bin_rows, think, mode):
    """think config の bin_rows から (fixture→strategy)。mode='single'(seed0) or 'majority'(seed 多数決)。"""
    out = {}
    for fx in P.FIXTURES:
        prof = {}
        for bid, _ in BINARIES:
            vals = [r["choice"] for r in bin_rows
                    if r["think"] == think and r["fixture_id"] == fx["id"] and r["binary_id"] == bid]
            seed0 = [r["choice"] for r in bin_rows
                     if r["think"] == think and r["fixture_id"] == fx["id"] and r["binary_id"] == bid and r["seed"] == 0]
            prof[bid] = (seed0[0] if seed0 else None) if mode == "single" else _majority(vals)
        out[fx["id"]] = strategy_from_binaries(prof)
    return out


def aggregate(bin_rows):
    res = {}
    for tid, _think, _mt in THINK_CONFIGS:
        trows = [r for r in bin_rows if r["think"] == tid]
        diverge = [r for r in trows if r["parse_verdict"] != "OK"]
        unsure = [r for r in trows if r["choice"] == "unsure"]
        # 弱2二択の的中率(多数決基準)
        weak_tot = weak_hit = 0
        for fid, exp in EXPECTED_BINARY.items():
            for bid, ev in exp.items():
                vals = [r["choice"] for r in trows if r["fixture_id"] == fid and r["binary_id"] == bid]
                weak_tot += 1
                weak_hit += int(_majority(vals) == ev)
        block = {"diverge_rate": round(len(diverge) / len(trows), 4) if trows else 0.0,
                 "unsure_rate": round(len(unsure) / len(trows), 4) if trows else 0.0,
                 "weak2_binary_accuracy": "%d/%d" % (weak_hit, weak_tot)}
        for mode in ("single", "majority"):
            strat = _strategies(bin_rows, tid, mode)
            hit = sum(1 for fx in P.FIXTURES if strat[fx["id"]] == fx["expected_strategy"])
            unagg = sum(1 for v in strat.values() if v == "UNRESOLVED_AGG")
            probe_exp = [fx for fx in P.FIXTURES if fx["expected_strategy"] in P.PROBE_STRATS]
            probe_hit = sum(1 for fx in probe_exp if strat[fx["id"]] in P.PROBE_STRATS)
            block[mode] = {"strategy_match": round(hit / len(P.FIXTURES), 4),
                           "unresolved_agg": unagg,
                           "probe_recall": "%d/%d" % (probe_hit, len(probe_exp))}
        res[tid] = block
    return res


def _ser(bin_rows, wall, agg):
    hdr = {"_meta": "INTENT_PROBE_ARMC2(二択+定義例/think on-off/多数決/abstain)。弁別は決定論集計・LLM は二択のみ。",
           "arm": "C2", "aggregate": agg, "wall_seconds": wall, "model": MODEL, "prompt_id": PROMPT_ID,
           "binaries": [b[0] for b in BINARIES], "think_configs": [t[0] for t in THINK_CONFIGS], "seeds": list(SEEDS)}
    return "\n".join([json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
                     + [json.dumps(r, sort_keys=True, ensure_ascii=False) for r in bin_rows]) + "\n"


def check():
    if not os.path.isfile(OUT):
        print("INTENT_PROBE_ARMC2 --check: RED\n  NOT_GENERATED: 先に main(:8005)")
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header, bin_rows = lines[0], lines[1:]
    red = []
    for r in bin_rows:
        c, v = parse_binary(r["raw_output"], r["finish_reason"])
        if (c, v) != (r["choice"], r["parse_verdict"]):
            red.append("BIN_PARSE_NONDET[%s/%s/%s/s%d]" % (r["think"], r["fixture_id"], r["binary_id"], r["seed"]))
    if aggregate(bin_rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDET (parser/多数決/集計ツリー 再適用が記録と不一致)")
    if red:
        print("INTENT_PROBE_ARMC2 --check: RED")
        for m in red[:12]:
            print("  " + m)
        return 1
    print("INTENT_PROBE_ARMC2 --check: GREEN (二択parser/多数決/集計ツリー 決定論再現; provenance 完全)")
    _report(header["aggregate"])
    return 0


def _report(agg):
    for tid in [t[0] for t in THINK_CONFIGS]:
        a = agg[tid]
        print("  [think=%s] 弱2二択的中=%s abstain=%.2f 発散=%.2f | single: 戦略一致=%.2f UNRES=%d probe=%s | majority: 戦略一致=%.2f UNRES=%d probe=%s"
              % (tid, a["weak2_binary_accuracy"], a["unsure_rate"], a["diverge_rate"],
                 a["single"]["strategy_match"], a["single"]["unresolved_agg"], a["single"]["probe_recall"],
                 a["majority"]["strategy_match"], a["majority"]["unresolved_agg"], a["majority"]["probe_recall"]))


def main(argv):
    if "--check" in argv:
        return check()
    if not P._infra_ok():
        print("INTENT_PROBE_ARMC2: NO_INFRA — :8005 で実推論が返らない")
        return 2
    bin_rows, wall = run()
    agg = aggregate(bin_rows)
    open(OUT, "w", encoding="utf-8").write(_ser(bin_rows, wall, agg))
    print("Arm C2 実測: %d 呼出(think2×%d fixture×%d binary×%d seed) 並列=%d wall=%s"
          % (len(bin_rows), len(P.FIXTURES), len(BINARIES), len(SEEDS), MAX_PARALLEL, wall))
    _report(agg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
