#!/usr/bin/env python3
"""SELF_GROUNDING の *構造トラック*(hermetic, ネットワーク非依存)。
決定的な部分のみ: corpus 取込 / source_class / supersession 検出 / retrieval / answer-contract 検証。
意味トラック(real Qwen が構造化 answer を生成)は demo_self_grounding.py(live)。
2トラックは互いに置換しない(JREV-0006 §13)。
"""
import sys
from egl import self_grounding as SG

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))


def t_corpus():
    recs = SG.load_corpus()
    des = [r for r in recs if r["source_class"] == "DESIGN_LEDGER"]
    jrev = [r for r in recs if r["source_class"] == "REVIEW_LEDGER"]
    check("corpus: DESIGN_LEDGER と REVIEW_LEDGER の両方を取込", len(des) > 20 and len(jrev) >= 6, f"DE={len(des)} JREV={len(jrev)}")
    check("corpus: DE-0005 が記録に存在", any(r["record_id"] == "DE-0005" for r in recs))
    check("corpus: JREV-0006 が記録に存在", any(r["record_id"] == "JREV-0006" for r in recs))
    check("corpus: ordinal は時系列(単調増)", [r["ordinal"] for r in recs] == list(range(len(recs))))


def t_supersession():
    recs = SG.load_corpus()
    sup = SG.detect_supersession(recs)
    # R7/DE-0029 は R5 を supersede すると台帳に明記 → R5 が superseded
    check("supersession: R5 が後続に supersede されたと検出(R7/DE-0029)",
          "R5" in sup and any("0029" in s["by"] or s["by"] == "DE-0029" for s in sup["R5"]), str(sup.get("R5")))


def t_retrieve():
    recs = SG.load_corpus()
    hits = SG.retrieve("What did R8 change about the evidence bag?", recs)
    ids = [h["record_id"] for h in hits]
    check("retrieve: R8 質問で DE-0030(R8 実装)が上位に", "DE-0030" in ids, str(ids[:5]))
    hits2 = SG.retrieve("What were the three JREV-0005 pre-remediation defects?", recs)
    check("retrieve: JREV-0005 質問で JREV-0005 記録が retrieval に入る",
          "JREV-0005" in [h["record_id"] for h in hits2])


def t_validate_contract():
    corpus_ids = ["DE-0030", "DE-0029", "JREV-0005"]
    good = {"answer_claims": [{"text": "R8 replaced the bag veto with typed paths", "record_ids": ["DE-0030"], "currentness": "CURRENT"}],
            "historical_claims": [], "open_gaps": ["search_operation_semantic_validity NOT_VERIFIED"], "source_trace": ["DE-0030"]}
    v = SG.validate_answer(good, corpus_ids)
    check("contract: 正しい構造 + 実在 record_id → ok", v["ok"] and v["metrics"]["source_trace_completeness"] == 1.0, str(v["problems"]))
    bad_missing = {"answer_claims": [{"text": "x", "record_ids": []}], "historical_claims": [], "open_gaps": [], "source_trace": []}
    v2 = SG.validate_answer(bad_missing, corpus_ids)
    check("contract: 無出典 assertion(record_ids 空)を検出", not v2["ok"] and any("unsupported" in p for p in v2["problems"]))
    bad_unknown = {"answer_claims": [{"text": "x", "record_ids": ["DE-9999"]}], "historical_claims": [], "open_gaps": [], "source_trace": ["DE-9999"]}
    v3 = SG.validate_answer(bad_unknown, corpus_ids)
    check("contract: 実在しない record_id 引用(捏造出典)を検出", not v3["ok"] and any("unknown" in p for p in v3["problems"]))
    v4 = SG.validate_answer("not json", corpus_ids)
    check("contract: 非 JSON → not ok", not v4["ok"])


def t_jrev0007_validator_fixes():
    ids = ["DE-0001", "DE-0002"]
    # NEW_DEFECT-1: superseded_by の捏造 id を検出
    bad_sb = {"answer_claims": [], "historical_claims": [{"text": "old", "record_ids": ["DE-0001"], "superseded_by": ["DE-FAKE-1234"]}],
              "open_gaps": [], "source_trace": ["DE-0001"]}
    v = SG.validate_answer(bad_sb, ids)
    check("NEW_DEFECT-1: superseded_by の捏造 record_id を検出(出典 class を漏らさない)",
          not v["ok"] and any("superseded_by" in p and "unknown" in p for p in v["problems"]), str(v["problems"]))
    good_sb = {"answer_claims": [], "historical_claims": [{"text": "old", "record_ids": ["DE-0001"], "superseded_by": ["DE-0002"]}],
               "open_gaps": [], "source_trace": ["DE-0001"]}
    check("NEW_DEFECT-1: 実在 superseded_by は ok", SG.validate_answer(good_sb, ids)["ok"])
    bare = {"answer_claims": [], "historical_claims": [{"text": "old", "record_ids": ["DE-0001"], "superseded_by": "DE-0002"}],
            "open_gaps": [], "source_trace": []}
    check("NEW_DEFECT-1: bare string の superseded_by(SG-I で発現)を不正検出",
          not SG.validate_answer(bare, ids)["ok"])
    # NEW_DEFECT-2: 非 dict claim entry で crash せず problem
    malformed = {"answer_claims": ["just a sentence"], "historical_claims": [], "open_gaps": [], "source_trace": []}
    try:
        v2 = SG.validate_answer(malformed, ids)
        crashed = False
    except Exception:
        crashed = True
    check("NEW_DEFECT-2: 非 dict claim entry で crash せず ok=False(total 関数)", (not crashed) and not v2["ok"])
    # scope-clarity: answer_claims に currentness=HISTORICAL の誤配置を検出
    misplaced = {"answer_claims": [{"text": "x", "record_ids": ["DE-0001"], "currentness": "HISTORICAL"}],
                 "historical_claims": [], "open_gaps": [], "source_trace": ["DE-0001"]}
    check("scope-clarity: answer_claims の currentness=HISTORICAL 誤配置を決定的検出",
          not SG.validate_answer(misplaced, ids)["ok"])


if __name__ == "__main__":
    print("=== SELF_GROUNDING 構造トラック (hermetic) ===")
    print("\n[corpus] bounded corpus 取込"); t_corpus()
    print("\n[supersession] 撤回/上書きの version-aware 検出"); t_supersession()
    print("\n[retrieve] naive keyword retrieval(baseline)"); t_retrieve()
    print("\n[contract] 構造化 answer contract 検証(無出典/捏造出典を検出)"); t_validate_contract()
    print("\n[JREV-0007] validator hardening(superseded_by 検証 / total 関数 / currentness placement)")
    t_jrev0007_validator_fixes()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("構造トラックは決定的。意味トラック(Qwen が現/歴史/open-gap/出典を再構築)は demo_self_grounding.py。")
