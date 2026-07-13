#!/usr/bin/env python3
"""ITEM-2DER-EVO-0008 FIRST LIVE INTEGRATION — approved, scoped, single-use. Real :8005 Qwen worker/auditor
driven by operator.advance_dw_machine_ops; post-op conformance (0016) monitors each op; INTERVENTION (0017)
recorded ONLY on a HALT/anomaly. No GPU/serve change. Records to the REAL DW/DS/EGL stores (not isolated)."""
import sys, json, itertools
sys.path.insert(0, "/home/takasan")
for r in ("ds", "rri", "egl", "dev-workcell"):
    sys.path.insert(0, "/home/takasan/" + r)
from dw import workcell as W, adapters as AD
from twoder import operator as OP, authority as A, intervention as INTV, ids as IDS
from ds import phase0

meta = json.load(open("/tmp/live0008.json"))
TASK = "TASK-LIVE-0008-INTEG-002"
clk = ("2026-07-13T01:%02d:00" % i for i in itertools.count(10))
ts0 = "2026-07-13T01:05:00"

# 1) SCOPED single-use approval token bound to THIS task + op class (Taka go)
tok = A.grant_approval("USE_VLLM_INFERENCE", TASK, "DW_MACHINE_OP", "taka", ts0,
                       approved_scope=["DW_MACHINE_OP"])
print("APPROVAL", tok["approval_id"], "bound", tok["task_id"], tok["operation_class"], "single_use", tok["single_use"])

# 2) bounded task + plan (a tiny, safe coding goal). PLAN supplied by Manager (not the live loop).
KP = {"packet_type": "KNOWLEDGE_PACKET", "task_context": "live-0008 integration", "related_failure_patterns": []}
IP = {"narrow_goal": "add a pure function is_even(n) that returns n % 2 == 0",
      "in_scope": ["a single small function"], "acceptance_criteria": ["is_even(2) is True", "is_even(3) is False"],
      "forbidden_assumptions": ["no external deps", "no I/O"]}
if W.derive_state(TASK)[0] == "BLOCKED":              # fresh task
    W.create_task(TASK, "LIVE0008", IP["narrow_goal"], KP, next(clk), "manager-claude")
    W.record_plan(TASK, IP, next(clk), "manager-claude")
print("PRE_DW_STATE", W.derive_state(TASK)[0], "| PRE_STATE_ID", meta["pre_state_id"])

# 3) real-adapter bridge: QwenCoder/QwenAuditor (:8005) -> DW recorders. generator != auditor (separate seed/identity).
worker, auditor = AD.QwenCoder(seed=7), AD.QwenAuditor(seed=101)
def worker_fn(tid, view, nlo):
    run = worker.generate(IP)                         # REAL :8005 call (coder identity/seed)
    if nlo["operation"] == "REGENERATE":              # CODING_WORKER serves both GENERATE and REGENERATE
        run = {**run, "resolved_findings": [i.get("finding_id") for i in W.rework_items(tid)]}
        return W.record_regenerate(tid, run, next(clk))
    return W.record_generate(tid, run, next(clk))
def auditor_fn(tid, view, nlo):
    gen = (view["generate_runs"][-1].get("payload") or {}) if view.get("generate_runs") else {}
    ctx = {"implementation_packet": IP, "diff": gen.get("diff"), "test_result": gen.get("test_result"),
           "relevant_failure_patterns": KP["related_failure_patterns"]}
    run = auditor.audit(ctx)                           # REAL :8005 call
    return W.record_audit(tid, run, next(clk))
ACTORS = {"CODING_WORKER": worker_fn, "INDEPENDENT_AUDITOR": auditor_fn}   # no MANAGER -> DISPOSE/UPPER_REVIEW = barrier

# 4) LIVE run — approved + scoped + single-use consumed inside
res = OP.advance_dw_machine_ops(TASK, ACTORS, next(clk), live=True, approval=tok, operation_class="DW_MACHINE_OP", max_ops=4)
print("\nRAN", res["ran"], "| authority", res["authority"], "| approval_id", res.get("approval_id"))
print("STOPPED_AT", res["stopped_at"]["operation"], "(", res["stopped_at"].get("actor_role"), ")")
print("TRACE:")
for t in res["trace"]:
    print("  ", t["op"], t["pre"], "->", t["post"], "| dispatched", t["dispatched"], "| auto_served", t.get("auto_served"), "| reason", t.get("reason"))
print("CONFORMANCE (0016):")
for c in res["conformance"]:
    print("  ", c["op"], "verdict", c["verdict"], "| ok", c["ok"], "| anomalies", c.get("anomalies"))
print("HALTED_ON", res["halted_on"])

# 5) INTERVENTION (0017) ONLY on HALT/anomaly
halts = [c for c in res["conformance"] if c["verdict"] == "HALT"] + ([res["halted_on"]] if res["halted_on"] else [])
if halts:
    iv = INTV.record_intervention(
        trigger="conformance_mismatch", reason="live-0008 conformance HALT: %s" % halts[0].get("anomalies"),
        ts=next(clk), idempotency_key="%s|%s|HALT" % (TASK, halts[0]["op"]), detected_by="conformance",
        assessed_by="claude-senior", severity="MAJOR", action_class="SENIOR_REVIEW",
        trace_id=meta["trace"], references={"task_id": TASK, "conformance_verdict_ref": "HALT"}, evidence_refs=["DE-0221"])
    print("INTERVENTION recorded:", iv["intervention_id"])
else:
    print("INTERVENTION: none (no HALT/anomaly — nothing to record)")

# 6) POST-STATE id
post = phase0.record_dialogue_event([meta["utt"]], event_type="LIVE_EXEC_POSTSTATE",
        actor="2der-operator", run_meta={"task_id": TASK, "final_dw_state": W.derive_state(TASK)[0],
        "ops_advanced": [t["op"] for t in res["trace"] if t["dispatched"]],
        "conformance_verdicts": [c["verdict"] for c in res["conformance"]],
        "stopped_at": res["stopped_at"]["operation"], "approval_id": res.get("approval_id")})
print("POST_STATE_ID", post["dialogue_event_id"], "| FINAL_DW_STATE", W.derive_state(TASK)[0])
json.dump({"post_state_id": post["dialogue_event_id"], "final_state": W.derive_state(TASK)[0],
           "stopped_at": res["stopped_at"]["operation"], "ops": [t["op"] for t in res["trace"] if t["dispatched"]],
           "verdicts": [c["verdict"] for c in res["conformance"]], "approval_id": res.get("approval_id"),
           "intervention": (iv["intervention_id"] if halts else None)}, open("/tmp/live0008_result.json", "w"))
