#!/usr/bin/env python3
"""real Gate4(VLLMAdjudicator)の hermetic テスト。ネットワーク非依存(_call を monkeypatch)。
焦点: 出力破損/未達/到達不能を fail-safe(UNJUDGEABLE/UNRESOLVED → EVIDENCE_INSUFFICIENT)へ倒す
=実モデルが壊れても *勝手に SUPPORTED にしない*(fail-closed)。実モデル敵対ラウンドは demo_gate4_vllm.py。
"""
import os, sys, tempfile, urllib.error
os.environ.setdefault("EGL_DATA_DIR", tempfile.mkdtemp(prefix="egl_j_"))
from egl import judge, judge_vllm

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))

PKT = {"candidate_id": "CC-1", "statement": "X", "scope": {}, "claim_type": "DESCRIPTION",
       "evidence_packets": [{"fragment_id": "F", "bounded_context": {"heading": "h", "prev_block": None,
                             "fragment": "X is stated", "next_block": None, "source_class": "PRIMARY"}}]}


def with_call(fn, test):
    orig = judge_vllm._call
    judge_vllm._call = fn
    try:
        test()
    finally:
        judge_vllm._call = orig


def t_extract_json():
    check("extract: 素の JSON", judge_vllm._extract_json('{"a":1}') == {"a": 1})
    check("extract: prose 埋め込み JSON を抽出",
          judge_vllm._extract_json('sure:\n{"f1_entailment":"SUPPORTED"}\ndone')["f1_entailment"] == "SUPPORTED")
    check("extract: 壊れた JSON → None", judge_vllm._extract_json("not json at all") is None)
    check("extract: 空 → None", judge_vllm._extract_json("") is None)


def t_valid_finding():
    def fake(_): return '{"f1_entailment":"SUPPORTED","f2_scope":"WITHIN","fragment_sufficient":true,"rationale":"ok"}'
    def test():
        f = judge_vllm.VLLMAdjudicator().adjudicate(PKT, common_run_id="R-1")
        check("valid: f1=SUPPORTED f2=WITHIN が Finding へ", f.f1_entailment == "SUPPORTED" and f.f2_scope == "WITHIN")
        check("valid: adjudicator に model@prompt version が刻まれる", "vllm" in f.adjudicator)
        check("valid: teacher_signal(CB-5)", f.teacher_signal is True)
    with_call(fake, test)


def t_failsafe_bad_enum():
    def fake(_): return '{"f1_entailment":"MAYBE","f2_scope":"SORTA","fragment_sufficient":true}'
    def test():
        f = judge_vllm.VLLMAdjudicator().adjudicate(PKT, common_run_id="R-1")
        check("fail-safe: 不正 enum → UNJUDGEABLE/UNRESOLVED(勝手に SUPPORTED にしない)",
              f.f1_entailment == "UNJUDGEABLE" and f.f2_scope == "UNRESOLVED" and f.fragment_sufficient is False)
    with_call(fake, test)


def t_failsafe_empty():
    def fake(_): return ""      # reasoning が予算を食い content 空(実測した故障)
    def test():
        f = judge_vllm.VLLMAdjudicator().adjudicate(PKT, common_run_id="R-1")
        check("fail-safe: 空 content → UNJUDGEABLE(broken でも fail-closed)", f.f1_entailment == "UNJUDGEABLE")
    with_call(fake, test)


def t_failsafe_unreachable():
    def fake(_): raise urllib.error.URLError("connection refused")
    def test():
        f = judge_vllm.VLLMAdjudicator().adjudicate(PKT, common_run_id="R-1")
        check("fail-safe: vLLM 到達不能 → UNJUDGEABLE(例外を握って fail-closed)",
              f.f1_entailment == "UNJUDGEABLE" and "unreachable" in f.rationale)
    with_call(fake, test)


def t_decide_maps_to_insufficient():
    # fail-safe finding は decide() で EVIDENCE_INSUFFICIENT(受理しない)へ
    from egl import gates
    fs = judge.Finding("CC-1", "UNJUDGEABLE", "UNRESOLVED", "R-1", "fail-safe", fragment_sufficient=False)
    out, _ = gates.decide(fs, {"dup_conflict_candidate_ids": []}, "SUPPORTING")
    check("decide: fail-safe finding → EVIDENCE_INSUFFICIENT(勝手に ACCEPT しない)", out == "EVIDENCE_INSUFFICIENT")


if __name__ == "__main__":
    print("=== real Gate4 (VLLMAdjudicator) hermetic テスト ===")
    print("\n[extract] JSON 抽出"); t_extract_json()
    print("\n[valid] 正常 finding"); t_valid_finding()
    print("\n[fail-safe] 出力破損/未達/到達不能は fail-closed")
    t_failsafe_bad_enum(); t_failsafe_empty(); t_failsafe_unreachable(); t_decide_maps_to_insufficient()

    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("実モデルが壊れても fail-closed(勝手に SUPPORTED にしない)。敵対ラウンドは demo_gate4_vllm.py。")
