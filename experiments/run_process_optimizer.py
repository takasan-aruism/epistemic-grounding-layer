#!/usr/bin/env python3
"""§16 Process Optimizer walking slice + §17 A-vs-virtual-B。
deterministic aggregate → trigger fire 時のみ Qwen3.6(Optimizer)→ ≤1 candidate(pre-seed 禁止)→
別 actor が property preservation review(§12 gate)→ native capability(§13)→ research 要れば RESEARCH_NEED。
self-formed vs human-taught を記録。process policy は auto-apply しない(§19 AC-19)。"""
import json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import process_optimizer as PO
sys.path.insert(0, "/home/takasan/egl/experiments")
import process_aggregate as PA

EGL = Path("/home/takasan/egl")
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
# §16: これらを答えとして与えない。self-formed かどうかを測る。
FORBIDDEN_PRESEED = ["raw findings cause avoidable rework", "independent slices are serialized",
                     "batching", "parallelization", "model switching dominates", "vLLM Sleep Mode",
                     "current-stack native capability was not inspected"]


def chat(system, user, seed=0, max_tokens=1100):
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


OPT_SYS = (
    "You are the 2DER Process Optimizer. You observe a DETERMINISTIC process aggregate (computed from primitive "
    "event logs; you are NOT the cost calculator) and form AT MOST ONE dominant process-simplification candidate. "
    "You do NOT conduct research, define RQs, acquire sources, admit knowledge, adjudicate your own proposal, or "
    "apply changes. Answer: (1) which observed cost appears structurally avoidable? (2) is the costly ordering "
    "required by task dependency? (3) can steps be removed, reordered, batched, parallelized, cached, or delegated "
    "differently? (4) does a known current runtime/tool/service directly control the dominant blocked property? "
    "(5) for the proposed change, which required process properties are preserved/weakened/unknown? (6) what "
    "evidence is required before adoption? Return ONLY JSON {\"candidate\":{\"dominant_cost\":\"...\","
    "\"structurally_avoidable\":true|false,\"dependency_required\":true|false,\"proposed_change\":\"...\","
    "\"native_capability\":{\"component\":\"...\",\"blocked_property\":\"...\",\"coverage_status\":\"ESTABLISHED|NOT_ESTABLISHED\"},"
    "\"research_required\":true|false,\"evidence_required_before_adoption\":\"...\"}}. If no structurally avoidable "
    "dominant cost exists, return {\"candidate\":null}.")

REV_SYS = (
    "You are an INDEPENDENT property-preservation reviewer (you did NOT author the optimization candidate). Given a "
    "proposed process change and the required process properties, for EACH property return a verdict PRESERVED / "
    "WEAKENED / UNKNOWN with an argument, and mechanism_ref when PRESERVED. Return ONLY JSON "
    "{\"property_verdicts\":[{\"property_id\":\"P1\",\"verdict\":\"...\",\"argument\":\"...\",\"mechanism_ref\":\"...\"}]}.")


def main():
    agg = PA.aggregate()
    (EGL / "experiments" / "process_aggregate.json").write_text(json.dumps(agg, ensure_ascii=False, indent=2))
    out = {"aggregate": agg}
    print(f"[aggregate] tasks={agg['n_tasks']} overhead_ratio={agg['model_switch_overhead_ratio']} "
          f"triggers={[f['id'] for f in agg['triggers_fired']]}")
    if not agg["triggers_fired"]:
        out["result"] = "no trigger fired -> Optimizer NOT invoked"
        (EGL / "experiments" / "process_optimizer_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print(out["result"]); return

    # §16: aggregate の数値のみ渡す(解釈を pre-seed しない)。per_task は簡約。
    seed_view = {k: agg[k] for k in ("n_tasks", "completed", "total_run_seconds", "total_switch_seconds",
                                     "total_model_switches", "model_switch_overhead_ratio", "tasks_with_rework",
                                     "total_rework", "total_findings", "disposition_totals",
                                     "independence_relation", "executed")}
    cand_raw = chat(OPT_SYS, f"PROCESS_AGGREGATE:\n{json.dumps(seed_view, ensure_ascii=False)}\n\nReturn the JSON.",
                    seed=0, max_tokens=1100)
    cand = (js(cand_raw) or {}).get("candidate")
    out["candidate"] = cand
    print(f"[optimizer candidate] {json.dumps(cand, ensure_ascii=False)[:300] if cand else 'null'}")

    if cand:
        # §13 native capability(self-report 禁止、ESTABLISHED は EGL ref 要)
        nc = PO.validate_native_capability(cand.get("native_capability") or {})
        out["native_capability_check"] = nc
        # research 要れば RESEARCH_NEED を emit して stop(Optimizer は research しない)
        if cand.get("research_required") or nc["research_need"]:
            out["research_need_emitted"] = {
                "packet_type": "RESEARCH_NEED", "origin": "Process Optimizer",
                "blocked_property": (cand.get("native_capability") or {}).get("blocked_property"),
                "component": (cand.get("native_capability") or {}).get("component"),
                "route": "RRI Need Validation -> Research Design -> EGL acquisition",
                "note": "Optimizer stops here; does NOT research/acquire/admit."}
            print(f"[RESEARCH_NEED emitted] {out['research_need_emitted']['blocked_property']} (Optimizer stops)")
        # §12 property preservation review by SEPARATE actor (different context/seed)
        props = (PO.current_property_set() or {}).get("properties", [])
        rev_raw = chat(REV_SYS, f"PROPOSED_CHANGE:\n{cand.get('proposed_change')}\nREQUIRED_PROPERTIES:\n"
                       f"{json.dumps(props, ensure_ascii=False)}\n\nReturn the JSON.", seed=909, max_tokens=1100)
        review = js(rev_raw) or {"property_verdicts": []}
        gate = PO.validate_preservation_review(review, (PO.current_property_set() or {}).get("process_property_set_version"))
        out["preservation_review"] = review
        out["preservation_gate"] = gate
        print(f"[preservation gate] auto_adoptable={gate['auto_adoptable']} problems={gate['problems'][:2]}")

    # §16 self-formation 測定: candidate に forbidden-preseed の各軸が自力で現れたか
    blob = json.dumps(out.get("candidate") or {}, ensure_ascii=False).lower()
    self_formed = {ax: (any(w in blob for w in ax.lower().split() if len(w) > 4)) for ax in FORBIDDEN_PRESEED}
    out["self_formed_axes"] = self_formed
    out["human_taught_available_but_not_injected"] = ["H-OPS-01", "H-OPS-02"]

    # §17 A vs virtual-B counterfactual (deterministic, COUNTERFACTUAL_ESTIMATE)
    n = agg["n_tasks"]; actual_swaps = agg["total_model_switches"]
    avg = None
    secs = [t["switch_seconds"] / t["model_switches"] for t in agg["per_task"] if t["model_switches"] and t["switch_seconds"]]
    avg = round(sum(secs) / len(secs), 1) if secs else None
    reworked = agg["tasks_with_rework"]
    # virtual B: 1 swap->coder (batch generate all N) + 1 swap->qwen (batch audit all N) = 2;
    # rework subset: +2 per rework round (assume 1 shared rework round if any reworked) 近似
    virtual_b_swaps = 2 + (2 if reworked else 0)
    out["a_vs_virtual_b"] = {
        "status": "COUNTERFACTUAL_ESTIMATE (NOT measured B performance)",
        "dependency_graph": agg["independence_relation"],
        "batch_eligible_slices": n, "actual_A_swaps": actual_swaps, "virtual_B_min_swaps": virtual_b_swaps,
        "measured_swap_latency_basis_s": avg,
        "estimated_switch_time_delta_s": round((actual_swaps - virtual_b_swaps) * avg, 1) if avg else None,
        "assumptions": ["all slices independent (batch-eligible)", "1 shared rework round approximated",
                        "swap latency ~constant (measured basis)"],
        "non_guarantees": ["B not executed", "batch buffer/partial-work risk not modeled",
                           "rework distribution across items ignored", "do NOT auto-adopt B from this estimate"]}
    print(f"[A vs virtual-B] actual_A_swaps={actual_swaps} virtual_B_min_swaps={virtual_b_swaps} "
          f"est_delta={out['a_vs_virtual_b']['estimated_switch_time_delta_s']}s (COUNTERFACTUAL)")

    (EGL / "experiments" / "process_optimizer_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n-> process_optimizer_run.json 保存。process policy は auto-apply しない(§19 AC-19)。")


if __name__ == "__main__":
    main()
