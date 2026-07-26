#!/usr/bin/env python3
"""s_ambiguity_stage_build1 — Build 1a(P2 参照の前提)の測定ハーネス。BUILD SPEC v1.0 §10/§11。

測るもの(1a のみ。1b/1c は別スライス・指標を混ぜない):
  M1 捕捉      : IP1/IP2/IP3 が preflight で triggered=True になるか
  M2 自己解決  : BV3「この設計案の得失は？」が非発火か
  M3 誤発火率  : ds/ds_events.jsonl の USER 発話 → 機械生成19件除外 → **dedup 済ユニーク298件** への発火率
  M4 非回帰    : 既存 HBB-30 ゲートの5決定 + NEXT_LEGAL_OPERATION の文面が従来と逐語一致(★最優先)
  M5 束縛先    : context を与えると IP1 が発火しなくなるか(AND 条件が効いているか)

完全決定論・:8005 不使用・LLM 呼出ゼロ。usage: s_ambiguity_stage_build1.py [--check]
"""
import json
import os
import sys

for _r in ("", "rri", "ds", "egl", "dev-workcell", "twoder"):
    _p = os.path.join("/home/takasan", _r)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rri import preflight_gate as PG   # noqa: E402

STRUCT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(STRUCT, "AMBIGUITY_STAGE_BUILD1.jsonl")
CORPUS = "/home/takasan/ds/ds_events.jsonl"
MACHINE_PREFIX = "開発エビデンスを登録"

# 意図調べ fixture(s_intent_probe_armc3.FIXTURES と同一文言。ここでは LLM を呼ばないので文言のみ複製)
FIXTURES = [
    ("IP1", "あれ、どこにあったっけ？", True),
    ("IP2", "それ、その後どうなった？", True),
    ("IP3", "例のやつ、進んでる？", True),
    ("BV3", "この設計案の得失は？", False),
    ("D1", "Windows 10 の一般提供開始日は？", False),
    ("D2", "1024 は 2 の何乗ですか？", False),
    ("D3", "1 マイルは何キロメートル？", False),
    ("BV1", "白樺の木材としての価値は？", False),
    ("CH1", "どのデータベースを採用すべき？", False),
    ("PP1", "以前作った Watcher 仕様ってどこ？", False),   # P4(1c)の領域。1a では発火しないのが正
    ("PP2", "先週決めた方針のメモある？", False),
    ("PP3", "君が言ってた予備の鍵はどこ？", False),
]

# 既存 HBB-30 の凍結入力と、従来 hardcode されていた NEXT_LEGAL_OPERATION の文面(逐語)
HBB_AMBIG = ("a theoretical document says ternary systems show about 6x higher emergence score than binary "
             "systems; recover the derivation")
HBB_CLEAR = ("Smith et al. (2020), https://arxiv.org/abs/2001.00001, report 6x higher emergence score in "
             "ternary systems; explain the metric")
LEGACY_NLO = ("CLARIFY_FIRST (gate RRI-GATE-AMBIGUOUS-QUANT-001): ambiguous quantitative claim — concrete "
              "number + vague/missing source. RRI holds before DW/acquisition; provide a clear source "
              "(author/title/venue/url) to proceed. proposed EGL status=WEAK_UNSOURCED_QUANTITATIVE_CLAIM")

# 意図調べとの重複についての決定(BUILD SPEC 統合元 handoff §5.5 — どちらでもよいが記録が要る)
STAGE_ORDER_DECISION = ("段で triggered=True になった入力は front door 3d 段で return TRACE となり意図調べに"
                        "到達しない(既存 preflight の挙動をそのまま継承)。＝両方は走らない。")


def corpus():
    """dedup 済ユニーク発話。478 → 機械生成19件除外 → 459 → dedup → 298。"""
    raw = []
    with open(CORPUS, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("record_type") == "UTTERANCE" and r.get("speaker") == "USER":
                raw.append(r.get("raw_text", ""))
    filtered = [x for x in raw if not x.startswith(MACHINE_PREFIX)]
    uniq = list(dict.fromkeys(filtered))
    return raw, filtered, uniq


def measure():
    rows, results = [], {}

    # ── M1/M2/M5 fixture ──────────────────────────────────────────────────────────────────────────────
    fx = []
    for fid, text, expect in FIXTURES:
        g = PG.detect(text, context=None)
        ok = (g["triggered"] is expect)
        fx.append({"id": fid, "text": text, "expected_triggered": expect, "triggered": g["triggered"],
                   "gate_id": g["gate_id"] if g["triggered"] else None,
                   "decision": g["decision"], "ok": ok})
    results["M1_capture"] = {f["id"]: f["triggered"] for f in fx if f["id"].startswith("IP")}
    results["M2_bv3_non_fire"] = next(f["triggered"] for f in fx if f["id"] == "BV3") is False
    results["fixture_all_ok"] = all(f["ok"] for f in fx)
    rows.append({"row_type": "FIXTURE", "cases": fx})

    # M5: 束縛先がある文脈を与えたら撃たない(AND 条件の実証)
    bound_ctx = "直前は DE-0548 の意図調べ再監査と s_intent_probe_armc3.py の fixture の話をしていた。"
    m5 = []
    for fid, text, _ in FIXTURES[:3]:
        g_no = PG.detect(text, context=None)
        g_yes = PG.detect(text, context=bound_ctx)
        g_empty = PG.detect(text, context="   ")
        m5.append({"id": fid, "no_context": g_no["triggered"], "with_binder": g_yes["triggered"],
                   "whitespace_context": g_empty["triggered"],
                   "binder_reason": g_yes["signals"].get("binder_reason") if g_yes["triggered"]
                   else PG.binder_state(bound_ctx)[1]})
    results["M5_binder_suppresses"] = all(m["no_context"] and not m["with_binder"] and m["whitespace_context"]
                                          for m in m5)
    rows.append({"row_type": "BINDER", "cases": m5})

    # ── M3 誤発火率(★dedup 済) ────────────────────────────────────────────────────────────────────────
    raw, filtered, uniq = corpus()
    fires = [(u, PG.detect(u, context=None)) for u in uniq if PG.detect(u, context=None)["triggered"]]
    ref_fires = [(u, g) for u, g in fires if g["gate_id"] == "RRI-GATE-UNBOUND-REFERENT-001"]
    by_pattern = {}
    for _u, g in ref_fires:
        by_pattern[g["claim_pattern_id"]] = by_pattern.get(g["claim_pattern_id"], 0) + 1
    results["M3_corpus"] = {"user_utterances": len(raw), "machine_generated_excluded": len(raw) - len(filtered),
                            "after_exclusion": len(filtered), "unique_deduped": len(uniq),
                            "fired_total": len(fires), "fired_referent_gate": len(ref_fires),
                            "referent_fire_rate_pct": round(100.0 * len(ref_fires) / len(uniq), 2),
                            "by_pattern": by_pattern, "dedup_applied": True}
    # ★CC-α の恒久規律(2026-07-26 再監査 §2): 率を出したらヒットを必ず目視列挙する。全件を台帳に残す。
    hits = [{"text": u, "pattern": g["claim_pattern_id"], "matched_surface": g["signals"].get("matched_surface"),
             "surface_rule": g["signals"].get("surface_rule")} for u, g in ref_fires]
    results["M3_hits"] = hits
    rows.append({"row_type": "CORPUS", "summary": results["M3_corpus"], "fired_hits_all": hits})

    # ── M6 束縛先条件を★実データで測る(1a' の目的)。上のヒットに束縛先つき context を与えて撃たなくなるか ──
    # 実発話は本物・context は合成(実 context は preceding_utterance_ref から取れるが CC-α §7-3「今は使わない」に従う)。
    synth_ctx = "直前は QwenとCoderの切替タスク(3分のボトルネック)の話をしていた。対象は DE-0549。"
    m6 = [{"text": u, "no_context": True,
           "with_binder_context": PG.detect(u, context=synth_ctx)["triggered"],
           "whitespace_context": PG.detect(u, context="  ")["triggered"]} for u, _g in ref_fires]
    results["M6_binder_on_real_data"] = {
        "n": len(m6), "suppressed_by_binder": sum(1 for m in m6 if not m["with_binder_context"]),
        "context_is_synthetic": True,
        "all_discriminated": bool(m6) and all(not m["with_binder_context"] and m["whitespace_context"] for m in m6)}
    rows.append({"row_type": "BINDER_REAL_DATA", "cases": m6, "context_used": synth_ctx,
                 "note": "発話は実データ(ユニーク298件由来)・context は合成。実 context 配線は Build 2。"})

    # ── M4 既存ゲート非回帰(★最優先) ─────────────────────────────────────────────────────────────────
    a = PG.detect(HBB_AMBIG)
    b = PG.detect(HBB_AMBIG, failure_hits=[{"failure_id": "FAIL-002"}])
    c = PG.detect(HBB_AMBIG, user_insists=True)
    d = PG.detect(HBB_CLEAR)
    e = PG.detect("what does emergence mean in ternary vs binary systems, conceptually?")
    nlo = PG.next_legal_operation(a)
    m4 = {"CLARIFY_FIRST": a["decision"] == "CLARIFY_FIRST" and a["blocks_dw_escalation"] is True,
          "STRONGLY_DISCOURAGE_DW": b["decision"] == "STRONGLY_DISCOURAGE_DW",
          "ALLOW_WITH_WARNING": c["decision"] == "ALLOW_WITH_WARNING" and c["blocks_dw_escalation"] is False,
          "ALLOW_clear_source": d["triggered"] is False and d["decision"] == "ALLOW",
          "ALLOW_abstract": e["triggered"] is False and e["decision"] == "ALLOW",
          "allow_result_keeps_quant_shape": (e["gate_id"] == PG.GATE_ID
                                             and "clear_source_present" in e["signals"]),
          "next_legal_operation_verbatim": nlo == LEGACY_NLO}
    results["M4_non_regression"] = m4
    results["M4_all_green"] = all(m4.values())
    rows.append({"row_type": "NON_REGRESSION", "checks": m4, "next_legal_operation": nlo})

    rows.append({"row_type": "DECISION", "stage_order": STAGE_ORDER_DECISION,
                 "context_wiring": "front door(twoder/submit.py 3d 段)は detect() に context を渡していない＝未配線(Build 2)。"})
    return rows, results


def determinism():
    """同一入力で2回走らせ、直列化が完全一致するか(--check の核)。"""
    a = json.dumps(measure()[0], ensure_ascii=False, sort_keys=True)
    b = json.dumps(measure()[0], ensure_ascii=False, sort_keys=True)
    return a == b


def schema_check():
    pats = PG.load_patterns(use_cache=False)
    errs = []
    if not pats:
        errs.append("pattern DB が空")
    for p in pats:
        for f in PG.PATTERN_REQUIRED_FIELDS:
            if f not in p:
                errs.append("%s: 欠落 %s" % (p.get("pattern_id"), f))
        if p.get("decision") not in ("CLARIFY_FIRST", "HOLD_AS_WEAK_CLAIM", "STRONGLY_DISCOURAGE_DW",
                                     "ALLOW_WITH_WARNING", "ALLOW"):
            errs.append("%s: 未知の decision %r" % (p.get("pattern_id"), p.get("decision")))
    return pats, errs


def suppression_check():
    """抑制カウンタの適用が決定論であること。"""
    base = {"pattern_id": "T", "ignored_warning_count": 0, "accepted_warning_count": 0, "suppressed": False}
    cases = [
        (dict(base), False),
        (dict(base, suppressed=True), True),
        (dict(base, ignored_warning_count=PG.AUTO_SUPPRESS_IGNORED_THRESHOLD), True),
        (dict(base, ignored_warning_count=PG.AUTO_SUPPRESS_IGNORED_THRESHOLD - 1), False),
        (dict(base, ignored_warning_count=99, accepted_warning_count=1), False),   # 一度でも採用されたら抑制しない
    ]
    return [(c, PG.is_suppressed(c) is exp) for c, exp in cases]


def check():
    ok = True
    pats, errs = schema_check()
    print("[%s] pattern DB スキーマ  (%d パターン)" % ("PASS" if not errs else "FAIL", len(pats)))
    for e in errs:
        print("       - %s" % e)
    ok &= not errs

    sup = suppression_check()
    sok = all(r for _, r in sup)
    print("[%s] 抑制カウンタが決定論  (%d/%d)" % ("PASS" if sok else "FAIL", sum(1 for _, r in sup if r), len(sup)))
    ok &= sok

    det = determinism()
    print("[%s] 決定論再現(2回走らせて完全一致)" % ("PASS" if det else "FAIL"))
    ok &= det

    _, res = measure()
    print("[%s] 既存 HBB-30 非回帰(★最優先): %s" % ("PASS" if res["M4_all_green"] else "FAIL",
                                                    res["M4_non_regression"]))
    ok &= res["M4_all_green"]
    print("[%s] fixture 期待どおり" % ("PASS" if res["fixture_all_ok"] else "FAIL"))
    ok &= res["fixture_all_ok"]
    print("\n%s" % ("--check GREEN" if ok else "--check RED"))
    return 0 if ok else 1


def main(argv):
    if "--check" in argv:
        return check()
    rows, res = measure()
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = res["M3_corpus"]
    print("Build 1a 実測 (完全決定論・LLM ゼロ)")
    print("  M1 捕捉      : IP1=%s IP2=%s IP3=%s" % (res["M1_capture"]["IP1"], res["M1_capture"]["IP2"],
                                                     res["M1_capture"]["IP3"]))
    print("  M2 BV3 非発火: %s" % res["M2_bv3_non_fire"])
    print("  M3 誤発火    : %d/%d = %.2f%%  ★dedup 済ユニーク(%d→除外%d→%d→dedup→%d)"
          % (c["fired_referent_gate"], c["unique_deduped"], c["referent_fire_rate_pct"],
             c["user_utterances"], c["machine_generated_excluded"], c["after_exclusion"], c["unique_deduped"]))
    print("  M4 非回帰    : %s (文面逐語一致=%s)" % (res["M4_all_green"],
                                                     res["M4_non_regression"]["next_legal_operation_verbatim"]))
    print("  M5 束縛先AND : %s (fixture: context を与えると撃たない)" % res["M5_binder_suppresses"])
    m6 = res["M6_binder_on_real_data"]
    print("  M6 束縛先(実データ): 該当 %d件 → 束縛先つき context で非発火 %d件 / 判別成立=%s ※context は合成"
          % (m6["n"], m6["suppressed_by_binder"], m6["all_discriminated"]))
    print("     内訳 by pattern: %s" % c["by_pattern"])
    for h in res["M3_hits"]:
        print("       [%s] %s | %s" % (h["pattern"], h["matched_surface"], h["text"][:60]))
    print("  → %s" % OUT)
    print("  ※ front door は context 未配線(Build 2)。fixture 試験と実 front door で挙動が変わる。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
