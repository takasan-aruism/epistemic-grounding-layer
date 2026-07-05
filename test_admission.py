#!/usr/bin/env python3
"""JREV-0006 data-integrity 修正の counter-factual(DE-0039/0040/0041)。ネットワーク非依存。
- DE-0040: judge entailment ≠ claim admission。VERIFIED は policy-eligible(PRIMARY)support path を要する。
- DE-0039: bootstrap_eligible は teacher_signal だけでなく code 導出(UNRESOLVED/非適格/taint を排除)。
- DE-0041: entailment_status を分離記録(VERIFIED は judge-entailment+admission であって外的真理でない)。
"""
import os, sys, tempfile
os.environ.setdefault("EGL_DATA_DIR", tempfile.mkdtemp(prefix="egl_adm_"))
from egl import core, acquisition as ACQ, source_policy as SP, pipeline as P, judge, curator

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))

def reset():
    for f in ["events.jsonl", "state.sqlite", ".idlock"]:
        p = core.DATA / f
        if p.exists():
            p.unlink()


def _mint(required, locator):
    """acquisition→extraction→curate(judge=SUPPORTED)で Claim を1本作り返す。"""
    r = core.run_start("rd", "ACQUISITION", task_id="TASK-1")
    leg = ACQ.mk_leg_intent(r, plan_id="PLAN-1", task_id="TASK-1", required_source_kind=required,
                            target_locator=locator, adapter_class="ACQ_HTTP_STATIC",
                            source_policy_id=SP.SOFTWARE_TECHNICAL_V1["source_policy_id"],
                            source_policy_version=1, search_method="DOC_FETCH", query=["x"], scope_locator=locator)
    a = ACQ.acquire(r, leg, injected={"transport_status": "SUCCESS", "content_status": "OBSERVED",
                                      "http_status": 200, "content_type": "text/html",
                                      "raw_bytes": "vLLM is a fast library.", "adapter_version": "1.0"})
    ACQ.mk_search_result_snapshot(r, leg, a, result_count=1)
    obs = ACQ.emit_observation_if_eligible(r, a)
    re_ = core.run_start("extractor", "EXTRACTION", task_id="TASK-1")
    ext = ACQ.extract_fragment(re_, obs["observation_id"], blocks=["vLLM is a fast library."],
                               block_index=0, excerpt="vLLM is a fast library.")
    core.run_end(re_, [])
    rc = core.run_start("rd", "EXTRACTION", task_id="TASK-1")
    rel = P.mk_relation(rc, ext["fragment_id"], None, "SUPPORTS", {"scope": {"entity": "vllm"}})
    C = P.mk_candidate(rc, {"object_kind": "CandidateClaim", "claim_type": "FACT", "predicate": "p",
        "polarity": "POSITIVE", "task_id": "TASK-1", "statement": "vLLM is a fast library",
        "scope": {"entity": "vllm"}, "evidence_relations": [rel], "resolves_gap": None,
        "representation_residual": {"known_omissions": [], "scope_uncertainty": "LOW"}})
    core.run_end(rc, [])
    adj = judge.ClaudeAdjudicator({C: {"f1": "SUPPORTED", "f2": "WITHIN", "fragment_sufficient": True, "rationale": "x"}})
    curator.curate(C, adj, log=lambda *_: None)
    con = core.build_view()
    return next((c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == C), None)


def t_de0040_admission():
    reset()
    # PRIMARY(OFFICIAL_DOCS→DECLARATION)+ SUPPORTED → VERIFIED
    prim = _mint("OFFICIAL_DOCS", "https://docs.vllm.ai/x")
    check("DE-0040: PRIMARY(policy-eligible)+ SUPPORTED → VERIFIED", prim and prim["status"] == "VERIFIED", prim["status"] if prim else None)
    check("DE-0040: admission_basis に policy-eligible path が記録", bool(prim and prim.get("admission_basis", {}).get("policy_match")))
    reset()
    # SECONDARY(UNKNOWN な random blog)+ SUPPORTED → REPORTED(entail されても admission されない)
    sec = _mint("OFFICIAL_DOCS", "https://random-blog.example/foo")
    check("DE-0040 counter-factual: SECONDARY source は judge SUPPORTED でも VERIFIED でなく REPORTED",
          sec and sec["status"] == "REPORTED", sec["status"] if sec else None)
    check("DE-0040: SECONDARY の admission_basis は policy_match=False", not (sec and sec.get("admission_basis", {}).get("policy_match")))


def t_de0039_bootstrap():
    reset()
    prim = _mint("OFFICIAL_DOCS", "https://docs.vllm.ai/x")     # PRIMARY + DECLARED
    check("DE-0039: PRIMARY+DECLARED+SUPPORTED → bootstrap_eligible True", prim and prim.get("bootstrap_eligible") is True)
    reset()
    repo = _mint("OFFICIAL_REPOSITORY", "https://github.com/vllm-project/vllm/blob/main/x.py")  # PRIMARY + IMPLEMENTATION_ARTIFACT → UNRESOLVED
    check("DE-0039 counter-factual: PRIMARY だが UNRESOLVED(repo)→ VERIFIED でも bootstrap_eligible False",
          repo and repo["status"] == "VERIFIED" and repo.get("validation_mode") == "UNRESOLVED" and repo.get("bootstrap_eligible") is False,
          f"status={repo['status']} vmode={repo.get('validation_mode')} boot={repo.get('bootstrap_eligible')}" if repo else None)
    reset()
    sec = _mint("OFFICIAL_DOCS", "https://random-blog.example/foo")   # SECONDARY / UNRESOLVED
    check("DE-0039 counter-factual: SECONDARY/UNRESOLVED → bootstrap_eligible False", sec and sec.get("bootstrap_eligible") is False)


def t_de0041_entailment_status():
    reset()
    prim = _mint("OFFICIAL_DOCS", "https://docs.vllm.ai/x")
    check("DE-0041: entailment_status を分離記録(judge-entailment を status と別に保持)",
          prim and prim.get("entailment_status") == "SUPPORTED")
    check("DE-0041: VERIFIED は entailment+admission であって外的真理でない(bootstrap_eligible と別軸)",
          prim and prim["status"] == "VERIFIED" and "bootstrap_eligible" in prim and "validation_mode" in prim)


if __name__ == "__main__":
    print("=== JREV-0006 data-integrity 修正テスト (DE-0039/0040/0041) ===")
    print("\n[DE-0040] factual admission は policy-eligible support path を要する"); t_de0040_admission()
    print("\n[DE-0039] bootstrap_eligible は code 導出(自律化原料を fail-closed で守る)"); t_de0039_bootstrap()
    print("\n[DE-0041] entailment / admission / validation_mode の分離"); t_de0041_entailment_status()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS)-len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("judge entailment ≠ claim admission ≠ bootstrap eligibility。低信頼 source は自律化原料を汚さない。")
