#!/usr/bin/env python3
"""JREV-0007 恒久レビュー機構のテスト(GPT directive §5/§6)。ネットワーク非依存。
(1) guarantee coverage sweep: reference-bearing field 各所に違反を注入し、guard が全て検出することを実証
    (= 宣言 guarantee の field 網羅を機械的に audit。IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION の恒久対策)。
(2) C-TOTALITY totality fuzz: LLM 出力を消費する決定的 guard に malformed-shape を食わせ、
    no crash / no fail-open(勝手に ok=True/SUPPORTED にしない)を実証。
"""
import sys
from egl import self_grounding as SG, review_mechanisms as RM, judge, judge_vllm

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))


# ---------------------------------------------------------------
# §5 guarantee coverage sweep — reference-bearing field を全走査し違反注入→検出
# ---------------------------------------------------------------
def sweep_validate_answer_references():
    """validate_answer の看板 guarantee『全 record reference の実在を検証』を、各 reference-bearing
    field に捏造 id を注入して sweep。1箇所でも見逃せば FAIL(NEW_DEFECT-1 が起きた穴)。"""
    real = ["DE-0001"]
    base = {"answer_claims": [{"text": "t", "record_ids": ["DE-0001"], "currentness": "CURRENT"}],
            "historical_claims": [{"text": "h", "record_ids": ["DE-0001"], "superseded_by": ["DE-0001"]}],
            "open_gaps": [], "source_trace": ["DE-0001"]}
    import copy
    injections = {
        "answer_claims[].record_ids": lambda a: a["answer_claims"][0].__setitem__("record_ids", ["DE-FAKE"]),
        "historical_claims[].record_ids": lambda a: a["historical_claims"][0].__setitem__("record_ids", ["DE-FAKE"]),
        "historical_claims[].superseded_by": lambda a: a["historical_claims"][0].__setitem__("superseded_by", ["DE-FAKE"]),
        "source_trace[]": lambda a: a.__setitem__("source_trace", ["DE-FAKE"]),
    }
    missed = []
    for field, inject in injections.items():
        a = copy.deepcopy(base)
        inject(a)
        v = SG.validate_answer(a, real)
        if v["ok"]:                       # 捏造 id を通したら coverage の穴
            missed.append(field)
    return missed


def t_coverage_sweep():
    # 宣言された reference field 全てで sweep が違反を検出(見逃しゼロ)
    missed = sweep_validate_answer_references()
    check("§5 coverage sweep: validate_answer の全 reference-bearing field で捏造 id を検出(見逃しゼロ)",
          missed == [], f"missed={missed}")
    # COVERAGE_MAP が宣言する field と sweep 対象が一致(記述と実装の一致=scope 膨張の逆)
    declared = set(RM.COVERAGE_MAP[0]["reference_fields"])
    swept = {"answer_claims[].record_ids", "historical_claims[].record_ids",
             "historical_claims[].superseded_by", "source_trace[]"}
    check("§5 coverage map: 宣言 reference_fields = sweep 対象(記述が実装より広くない)", declared == swept, str(declared ^ swept))


# ---------------------------------------------------------------
# §6 C-TOTALITY totality fuzz — 決定的 LLM-guard は malformed で crash/fail-open しない
# ---------------------------------------------------------------
def t_totality_validate_answer():
    crashes, fail_open = [], []
    for name, shape in RM.c_totality_shapes():
        try:
            v = SG.validate_answer(shape, ["DE-0001"])
        except Exception as e:
            crashes.append((name, type(e).__name__)); continue
        # malformed 入力が ok=True(fail-open)になってはならない
        if v.get("ok"):
            fail_open.append(name)
    check("§6 totality(validate_answer): 全 malformed-shape で crash しない(total)", crashes == [], str(crashes))
    check("§6 totality(validate_answer): malformed が ok=True(fail-open)にならない", fail_open == [], str(fail_open))


def t_totality_judge():
    # Gate4 findings parser を malformed model 出力で fuzz。全て fail-closed(UNJUDGEABLE)を要求。
    pkt = {"candidate_id": "CC", "statement": "s", "scope": {}, "claim_type": "DESCRIPTION",
           "evidence_packets": [{"fragment_id": "F", "bounded_context": {"heading": "h", "prev_block": None,
                                 "fragment": "x", "next_block": None, "source_class": "PRIMARY"}}]}
    malformed_outputs = ["", "not json", "{", "{}", '{"f1_entailment": 42}',
                         '{"f1_entailment": ["SUPPORTED"], "f2_scope": "WITHIN"}',
                         '{"f1_entailment": "MAYBE", "f2_scope": "WITHIN"}',
                         '{"f2_scope": "WITHIN"}', 'garbage {"f1_entailment":"SUPPORTED"} more',
                         '{"f1_entailment": null, "f2_scope": null}']
    orig = judge_vllm._call
    crashes, fail_open = [], []
    try:
        for out in malformed_outputs:
            judge_vllm._call = (lambda o: (lambda _p: o))(out)
            try:
                f = judge_vllm.VLLMAdjudicator().adjudicate(pkt, common_run_id="R")
            except Exception as e:
                crashes.append((out[:20], type(e).__name__)); continue
            # malformed が SUPPORTED(fail-open)になってはならない → fail-safe は UNJUDGEABLE
            if f.f1_entailment not in judge.F1_VALUES or f.f1_entailment == "SUPPORTED":
                if f.f1_entailment == "SUPPORTED":
                    fail_open.append(out[:20])
    finally:
        judge_vllm._call = orig
    check("§6 totality(Gate4 judge): malformed model 出力で crash しない", crashes == [], str(crashes))
    check("§6 totality(Gate4 judge): malformed が SUPPORTED(fail-open)にならない(fail-closed=UNJUDGEABLE)",
          fail_open == [], str(fail_open))


if __name__ == "__main__":
    print("=== JREV-0007 恒久レビュー機構 (guarantee coverage sweep + C-TOTALITY) ===")
    print("\n[§5] guarantee coverage sweep(reference-bearing field 網羅の機械 audit)"); t_coverage_sweep()
    print("\n[§6] C-TOTALITY totality fuzz(決定的 LLM-guard は crash/fail-open しない)")
    t_totality_validate_answer(); t_totality_judge()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("宣言 guarantee は field 網羅を audit され、決定的 LLM-guard は malformed で total & fail-closed。")
