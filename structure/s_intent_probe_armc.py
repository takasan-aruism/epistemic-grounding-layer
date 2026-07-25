#!/usr/bin/env python3
"""s_intent_probe_armc — 意図調べ Arm C: 二択(A or B)並列分解 + 決定論集計(Taka 核心思想)。

「Qwen に総合判断させる」でなく、各判断を **A or B の tiny 二択**に削ぎ、**並列**実行し、
近縁戦略の細分(CONTEXT_RESOLVE↔CHOICE↔BMV / INTENT_PROBE↔PREMISE_PROBE)を **LLM でなく決定論ツリー**で弁別する。
狙い: 単発複雑(Arm A=0.54・細分弱)を、二択に削げば thinking 不要で正確にできるか(Arm A/B と比較)。

- LLM は粗い二択(得意)のみ・tiny prompt(発散しにくい)。戦略の弁別語は §9 準拠で**集計側**に埋める。
- Qwen3.6-35B-**A3B**(active 3B)ゆえ並列は安い(ThreadPool で束ね、vLLM max-num-seqs 内で batch)。
- 決定論部(二択 prompt/parser/集計ツリー/fixture)は byte 再現。LLM 判断(二択答え)のみ非決定論=record-occurrence。

usage:  s_intent_probe_armc.py [--check]
"""
import concurrent.futures as _cf
import json
import os
import re
import sys

import s_intent_probe_proto as P   # FIXTURES / PROBE_STRATS を共有(同 fixture で3アーム比較)

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "INTENT_PROBE_ARMC.jsonl")
MODEL = "Qwen3.6-35B-A3B"
ENDPOINT = "http://localhost:8005/v1/chat/completions"
SEEDS = (0, 1, 2)
MAX_TOKENS = 96             # tiny 二択ゆえ小。length は DIVERGE。
ENABLE_THINKING = False     # 二択は tiny=thinking 不要(Taka: 二択に削げば松葉杖不要)。ON でも即終端の想定。
PROMPT_ID = "armc-binary-v1"
MAX_PARALLEL = 16           # vLLM max-num-seqs(32)内。並列数を記録。

# ── 二択分解(A or B tiny・決定論固定)。conditional な問いも全て並列発行し、集計ツリーが取捨。──────────
_CTX = "（直前文脈: %s）"
BINARIES = [
    ("b_malformed", "依頼:「{req}」\nこの依頼は (A)意味の通る依頼 / (B)不正形で解釈不能。どちらか。"),
    ("b_needs_probe", "依頼:「{req}」{ctx}\nこの依頼は (A)そのまま解釈して回答/調査を始められる / (B)始める前に一度確認(聞き返し)が要る。どちらか。"),
    ("b_probe_type", "依頼:「{req}」\nもし確認が要るなら (A)対象は特定されるが存在/成立が怪しい(前提の確認) / (B)そもそも何を指すか意図が不明(意図の確認)。どちらか。"),
    ("b_determinacy", "依頼:「{req}」{ctx}\n合理的な回答は (A)概ね1つに絞れる / (B)絞れず複数ありうる。どちらか。"),
    ("b_context", "依頼:「{req}」{ctx}\n直前の文脈を踏まえると (A)支配的な解釈があり文脈で絞れる / (B)文脈でも絞れない。どちらか。"),
    ("b_multi_type", "依頼:「{req}」\nもし複数解釈があるなら (A)有限の選択肢から一つ選ぶ形 / (B)複数の観点を短く比較する形。どちらか。"),
]
_INSTR = '\nJSON のみ出力: {{"choice":"A" または "B","note":"10字以内"}}'


def _prompt(tmpl, fx):
    ctx = (_CTX % fx["context"]) if fx["context"] else ""
    return tmpl.format(req=fx["request"], ctx=ctx) + _INSTR


def _llm(prompt, seed):
    import urllib.request
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "seed": seed, "temperature": 0.7, "max_tokens": MAX_TOKENS,
                       "chat_template_kwargs": {"enable_thinking": ENABLE_THINKING}}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out = json.load(resp)
    ch = out["choices"][0]
    return (ch["message"].get("content") or ""), ch.get("finish_reason"), out.get("usage", {}).get("completion_tokens")


def parse_binary(raw, finish_reason):
    """raw → (choice∈{A,B} or None, verdict)。enum/schema 逸脱=DIVERGE。"""
    if finish_reason == "length":
        return None, "DIVERGE_LENGTH"
    m = re.search(r"\{.*\}", raw or "", re.S)
    if m:
        try:
            c = json.loads(m.group(0)).get("choice")
            if c in ("A", "B"):
                return c, "OK"
        except Exception:
            pass
    return None, "DIVERGE_SCHEMA"


# ── 決定論集計ツリー(§9 準拠・近縁戦略の弁別を集計側に持つ)────────────────────────
def strategy_from_binaries(b):
    """b={bin_id: 'A'/'B'/None}。返り strategy。必要な二択が欠ければ UNRESOLVED_AGG(捏造しない)。"""
    def g(k):
        return b.get(k)
    if g("b_malformed") is None:
        return "UNRESOLVED_AGG"
    if g("b_malformed") == "B":
        return "DEFER"
    if g("b_needs_probe") is None:
        return "UNRESOLVED_AGG"
    if g("b_needs_probe") == "B":                       # 聞き返しが要る=probe クラスタ
        if g("b_probe_type") is None:
            return "UNRESOLVED_AGG"
        return "PREMISE_PROBE" if g("b_probe_type") == "A" else "INTENT_PROBE"
    if g("b_determinacy") is None:
        return "UNRESOLVED_AGG"
    if g("b_determinacy") == "A":                       # 回答が絞れる
        return "DIRECT"
    if g("b_context") is None:                          # 絞れない=multi クラスタ
        return "UNRESOLVED_AGG"
    if g("b_context") == "A":                           # 文脈で絞れる→先に文脈解決(BMV でなく)
        return "CONTEXT_RESOLVE"
    if g("b_multi_type") is None:
        return "UNRESOLVED_AGG"
    return "CHOICE" if g("b_multi_type") == "A" else "BOUNDED_MULTI_VIEW"


def run():
    """全 (fixture×binary×seed) を並列発行 → binary 答えを集計ツリーで戦略へ。返り (rows, meta)。"""
    import time as _t   # wall-clock 用(実行時のみ・--check では使わない)
    tasks = [(fx, bid, tmpl, s) for fx in P.FIXTURES for bid, tmpl in BINARIES for s in SEEDS]

    def _one(task):
        fx, bid, tmpl, s = task
        raw, fr, ct = _llm(_prompt(tmpl, fx), s)
        choice, verdict = parse_binary(raw, fr)
        return {"fixture_id": fx["id"], "binary_id": bid, "seed": s, "raw_output": raw,
                "finish_reason": fr, "completion_tokens": ct, "choice": choice, "parse_verdict": verdict}
    t0 = _t.time()
    with _cf.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as ex:
        bin_rows = list(ex.map(_one, tasks))
    wall = round(_t.time() - t0, 2)

    # (fixture,seed) ごとに二択 profile → 戦略(決定論ツリー)
    prof = {}
    for r in bin_rows:
        prof.setdefault((r["fixture_id"], r["seed"]), {})[r["binary_id"]] = r["choice"]
    strat_rows = []
    for fx in P.FIXTURES:
        for s in SEEDS:
            b = prof.get((fx["id"], s), {})
            strat_rows.append({"fixture_id": fx["id"], "seed": s, "binaries": b,
                               "strategy": strategy_from_binaries(b),
                               "expected_strategy": fx["expected_strategy"]})
    bin_rows.sort(key=lambda r: (r["fixture_id"], r["binary_id"], r["seed"]))
    strat_rows.sort(key=lambda r: (r["fixture_id"], r["seed"]))
    meta = {"n_calls": len(bin_rows), "wall_seconds": wall, "max_parallel": MAX_PARALLEL,
            "enable_thinking": ENABLE_THINKING, "max_tokens": MAX_TOKENS}
    return bin_rows, strat_rows, meta


def aggregate(bin_rows, strat_rows):
    from collections import Counter
    diverge = [r for r in bin_rows if r["parse_verdict"] != "OK"]
    ok = [r for r in strat_rows if r["strategy"] != "UNRESOLVED_AGG"]
    strat_hit = sum(1 for r in ok if r["strategy"] == r["expected_strategy"])
    seedcons = {}
    for r in strat_rows:
        seedcons.setdefault(r["fixture_id"], set()).add(r["strategy"])
    consistent = sum(1 for v in seedcons.values() if len(v) == 1)
    probe_exp = [r for r in strat_rows if r["expected_strategy"] in P.PROBE_STRATS]
    probe_hit = sum(1 for r in probe_exp if r["strategy"] in P.PROBE_STRATS)
    nonprobe = [r for r in strat_rows if r["expected_strategy"] not in P.PROBE_STRATS]
    false_probe = sum(1 for r in nonprobe if r["strategy"] in P.PROBE_STRATS)
    return {
        "binary_diverge_rate": round(len(diverge) / len(bin_rows), 4) if bin_rows else 0.0,
        "binary_diverge_kinds": dict(Counter(r["parse_verdict"] for r in diverge)),
        "strategy_match": round(strat_hit / len(strat_rows), 4) if strat_rows else None,
        "unresolved_agg": sum(1 for r in strat_rows if r["strategy"] == "UNRESOLVED_AGG"),
        "seed_consistent_fixtures": "%d/%d" % (consistent, len(seedcons)),
        "probe_recall": "%d/%d" % (probe_hit, len(probe_exp)),
        "false_probe": "%d/%d" % (false_probe, len(nonprobe)),
    }


def _ser(bin_rows, strat_rows, meta, agg):
    hdr = {"_meta": "INTENT_PROBE_ARMC(二択並列分解+決定論集計)。LLM は A/B 二択のみ・戦略弁別は決定論ツリー。"
                    "近縁戦略の細分を集計側に持つ。--check=記録二択に parser/ツリー再適用。",
           "arm": "C", "aggregate": agg, "run_meta": meta, "model": MODEL, "prompt_id": PROMPT_ID,
           "binaries": [b[0] for b in BINARIES], "seeds": list(SEEDS)}
    lines = [json.dumps(hdr, sort_keys=True, ensure_ascii=False)]
    lines += [json.dumps({"row": "binary", **r}, sort_keys=True, ensure_ascii=False) for r in bin_rows]
    lines += [json.dumps({"row": "strategy", **r}, sort_keys=True, ensure_ascii=False) for r in strat_rows]
    return "\n".join(lines) + "\n"


def check():
    if not os.path.isfile(OUT):
        print("INTENT_PROBE_ARMC --check: RED\n  NOT_GENERATED: 先に main を実行(:8005)")
        return 1
    lines = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    header = lines[0]
    bin_rows = [l for l in lines[1:] if l.get("row") == "binary"]
    strat_rows = [l for l in lines[1:] if l.get("row") == "strategy"]
    red = []
    # 二択パーサ決定論再適用
    for r in bin_rows:
        c, v = parse_binary(r["raw_output"], r["finish_reason"])
        if (c, v) != (r["choice"], r["parse_verdict"]):
            red.append("BINARY_PARSE_NONDET[%s/%s/s%d]" % (r["fixture_id"], r["binary_id"], r["seed"]))
    # 集計ツリー決定論再適用: 記録 binaries → 戦略が一致
    for r in strat_rows:
        if strategy_from_binaries(r["binaries"]) != r["strategy"]:
            red.append("AGG_TREE_NONDET[%s/s%d]: %s vs %s"
                       % (r["fixture_id"], r["seed"], strategy_from_binaries(r["binaries"]), r["strategy"]))
    # 集計サマリ再現
    if aggregate(bin_rows, strat_rows) != header.get("aggregate"):
        red.append("AGGREGATE_NONDET")
    if red:
        print("INTENT_PROBE_ARMC --check: RED")
        for m in red[:12]:
            print("  " + m)
        return 1
    a = header["aggregate"]
    print("INTENT_PROBE_ARMC --check: GREEN (二択parser/集計ツリー 決定論再現; provenance 完全)")
    print("  [C 二択並列] 戦略一致=%s (UNRESOLVED_AGG=%d) 二択発散率=%.2f seed一貫=%s probe recall=%s 誤probe=%s"
          % (a["strategy_match"], a["unresolved_agg"], a["binary_diverge_rate"],
             a["seed_consistent_fixtures"], a["probe_recall"], a["false_probe"]))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    if not P._infra_ok():
        print("INTENT_PROBE_ARMC: NO_INFRA — :8005 で実推論が返らない(捏造の測定をしない)")
        return 2
    bin_rows, strat_rows, meta = run()
    agg = aggregate(bin_rows, strat_rows)
    open(OUT, "w", encoding="utf-8").write(_ser(bin_rows, strat_rows, meta, agg))
    print("Arm C 実測: %d 二択呼出(%d fixture×%d binary×%d seed) 並列=%d wall=%.1fs"
          % (meta["n_calls"], len(P.FIXTURES), len(BINARIES), len(SEEDS), meta["max_parallel"], meta["wall_seconds"]))
    print("  戦略一致=%s (UNRESOLVED_AGG=%d) 二択発散率=%.2f seed一貫=%s probe recall=%s 誤probe=%s"
          % (agg["strategy_match"], agg["unresolved_agg"], agg["binary_diverge_rate"],
             agg["seed_consistent_fixtures"], agg["probe_recall"], agg["false_probe"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
