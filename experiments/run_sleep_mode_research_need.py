#!/usr/bin/env python3
"""Sleep Mode RESEARCH_NEED を RRI に流す: Need Validation(§19-20)→ Research Design(§23-29)。
Optimizer/AEC は need emit で停止。RRI が need を validate し design を形成・gate 検証する。
§5 discipline: external SPECIFICATION 質問(vLLM docs で解ける)と local MEASUREMENT 質問(この機体でしか
測れない)を分離。RRI は research/acquisition を実行しない(ACQ-10: autonomous RD 未有効)→ design を出して停止。"""
import json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/rri")
from rri.need_validation import validate_research_need
from rri.rdec import validate_rdec
from rri.research_axis import validate_research_axis
from rri.rq_candidate import validate_rq_candidate
from rri.approved_rq_set import approved_rq_set_gate

EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
EGL = Path("/home/takasan/egl")

# Optimizer(DE-0080)+ AEC(AC-2/AC-4)が emit した need。RRI がこれを検証する。
FROZEN_NEED = {
    "origin": "Process Optimizer (DE-0080) + AEC AC-2/AC-4",
    "blocked_decision": "REDUCE_MODEL_SWITCH_OVERHEAD",
    "observed": "model-switch が wall-clock の 98% を支配(overhead_ratio 0.981, DE-0074/DE-0080)。"
                "vLLM Sleep Mode / concurrent-serve 等の native capability は EGL 未 admit(AEC AC-2 = UNRESOLVED)。",
    "optimizer_candidate": "parallelize independent validators(batching)= workflow 選択肢(research 不要)",
}

RRI_SYS = (
    "You are an RRI Research-Intent worker validating a system-originated RESEARCH_NEED before it may enter "
    "Research Design. CRITICALLY separate an EXTERNAL SPECIFICATION question (answerable from official docs: does a "
    "capability exist / what are its documented semantics?) from a LOCAL MEASUREMENT question (only answerable by "
    "observing THIS machine: actual wake/resume latency, TP=2/NVFP4 behavior). Do NOT convert local unknowns into "
    "generic web research. Also list NON-RESEARCH alternative causes/resolutions (implementation or policy) that "
    "must be considered so we do not research a bottleneck that is really an implementation choice. Return ONLY JSON "
    "{\"decision_to_support\":\"...\",\"research_requirement_summary\":\"...\",\"alternative_causes\":[non-research "
    "implementation/policy options],\"external_specification_rqs\":[\"...\"],\"local_measurement_rqs\":[\"...\"],"
    "\"observed_block_refs\":[\"...\"]}.")


def chat(system, user, seed=0, max_tokens=1200):
    body = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=body, headers={"Content-Type": "application/json"}), timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""


def js(t):
    i, j = t.find("{"), t.rfind("}")
    try:
        return json.loads(t[i:j + 1]) if 0 <= i < j else None
    except Exception:
        return None


def main():
    out = {"frozen_need": FROZEN_NEED}
    print("### Sleep Mode RESEARCH_NEED -> RRI ###\n")
    # ── RRI forms the need decomposition (external-spec vs local-measurement + non-research alternatives) ──
    form = js(chat(RRI_SYS, f"RESEARCH_NEED:\n{json.dumps(FROZEN_NEED, ensure_ascii=False)}\n\nReturn the JSON.", seed=0)) or {}
    print(f"[RRI decomposition] external_spec_rqs={len(form.get('external_specification_rqs', []))} "
          f"local_measurement_rqs={len(form.get('local_measurement_rqs', []))}")
    print(f"  alternative_causes(non-research): {form.get('alternative_causes')}")
    out["rri_decomposition"] = form

    # ── §19-20 Need Validation (deterministic gate) ──
    nec = {"validated": True, "origin_decision": form.get("decision_to_support") or "REDUCE_MODEL_SWITCH_OVERHEAD",
           "observed_block_refs": form.get("observed_block_refs") or ["DE-0074", "DE-0080"],
           "alternative_causes": form.get("alternative_causes") or ["phase batching (implementation)", "accept swap cost (policy)"],
           "research_requirement_summary": form.get("research_requirement_summary") or "vLLM native model-transition capability existence + semantics"}
    need = {"need_id": "RNEED-SLEEPMODE-1", "origin_system": "ProcessOptimizer/AEC",
            "decision_to_support": nec["origin_decision"], "blocked_state": "OPERATING_MODE_UNDECIDED", "nec": nec}
    nv = validate_research_need(need)
    print(f"\n[§19-20 Need Validation] may_enter={nv.get('may_enter')} reason={nv.get('reason')}")
    out["need_validation"] = {"need": need, "result": nv}
    if not nv.get("may_enter"):
        out["status"] = "NEED_VALIDATION_FAILED"
        (EGL / "experiments" / "sleep_mode_rri_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print("need validation 未通過 → design に進めない"); return

    # ── §23-29 Research Design (form + deterministic gates) ──
    # research axis: the external-spec capability question supports the REDUCE_MODEL_SWITCH_OVERHEAD decision
    axis = {"axis_id": "AX-NATIVE-CAP", "supports_decisions": ["REDUCE_MODEL_SWITCH_OVERHEAD"], "required": True,
            "safe_behavior_if_unknown": "treat native capability as NOT_ESTABLISHED; keep sequential-swap; do not assume Sleep Mode",
            "rdec_ref": "RDEC-NATIVE-CAP"}
    av = validate_research_axis(axis, ["REDUCE_MODEL_SWITCH_OVERHEAD"])
    rdec = {"rdec_id": "RDEC-NATIVE-CAP", "decision": "REDUCE_MODEL_SWITCH_OVERHEAD", "axis": "AX-NATIVE-CAP",
            "why_required": "if a documented native weight-offload/concurrent-serve capability exists, it changes the operating-mode choice",
            "expected_decision_effect": "may change swap-based A/B mode vs a native-capability mode",
            "omission_risk": "design a swap workaround while a native capability already solves it",
            "stop_condition_ref": "STOP-NATIVE-CAP"}
    cv = validate_rdec(rdec, ["REDUCE_MODEL_SWITCH_OVERHEAD"])
    # RQ candidate = external-spec question only (local-measurement は別 route)
    ext_q = (form.get("external_specification_rqs") or ["Does vLLM document a native weight-offload / sleep / concurrent-serve capability and its constraints?"])[0]
    rqc = {"rq_candidate_id": "RQ-NATIVE-CAP-1", "question": ext_q, "derived_from_axes": ["AX-NATIVE-CAP"],
           "decision_relevance": "determines whether a native capability mode is available for REDUCE_MODEL_SWITCH_OVERHEAD",
           "priority": "REQUIRED", "rdec_refs": ["RDEC-NATIVE-CAP"]}
    qv = validate_rq_candidate(rqc, ["AX-NATIVE-CAP"])
    # approved RQ set (lineage: design + revision + traces to validated need)
    rq_set = {"approval_status": "APPROVED", "source_research_design_id": "RDES-SLEEPMODE-1",
              "source_revision_id": "RDRV-SLEEPMODE-1", "required_rqs": ["RQ-NATIVE-CAP-1"],
              "validated_need_ref": "RNEED-SLEEPMODE-1"}
    gv = approved_rq_set_gate(rq_set)
    gates = {"research_axis": av, "rdec": cv, "rq_candidate": qv, "approved_rq_set_gate": gv}
    print("\n[§23-29 Research Design gates]")
    for k, v in gates.items():
        print(f"  {k}: {v}")
    out["research_design"] = {"axis": axis, "rdec": rdec, "rq_candidate": rqc, "approved_rq_set": rq_set, "gates": gates}

    all_ok = av.get("ok") and cv.get("ok") and qv.get("ok") and gv.get("may_proceed")
    # ── routing: external-spec -> EGL acquisition (ACQ-10 gated, NOT executed); local -> measurement need ──
    out["routing"] = {
        "external_specification": {"route": "EGL acquisition (SearchPlan over vLLM official docs)",
                                   "rqs": form.get("external_specification_rqs"),
                                   "execution": "NOT executed — autonomous RD not enabled (ACQ-10); awaits authorization"},
        "local_measurement": {"route": "local MEASUREMENT need (this machine only, NOT web research)",
                              "rqs": form.get("local_measurement_rqs"),
                              "note": "§5: do not convert local wake-latency into generic web research"},
        "non_research_alternatives": nec["alternative_causes"]}
    out["status"] = "RESEARCH_DESIGN_FORMED_AWAITING_ACQUISITION_AUTHORIZATION" if all_ok else "DESIGN_GATE_FAILED"
    print(f"\n[routing] external-spec -> EGL acquisition (NOT executed, ACQ-10); local -> measurement need")
    print(f"[status] {out['status']}")
    (EGL / "experiments" / "sleep_mode_rri_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n-> sleep_mode_rri_run.json 保存。RRI は research/acquisition を実行しない(design まで)。")


if __name__ == "__main__":
    main()
