#!/usr/bin/env python3
"""ODF narrowing — 独立 audit が露出させた minimality/trust-root 問題で ODF-02 候補を狭め、
実 dw/workcell.py（本物の gate）を dogfood して実装候補へ昇格する。

設計タスク用の load-bearing test = **決定的 minimality check**（F5 相当）。
GENERATE(narrow, Qwen3.6) → deterministic test → AUDIT(独立 Qwen3.6, 別 identity) → REGENERATE →
re-AUDIT → UPPER_REVIEW(Claude Manager) → gate → RESULT_PACKET（proposed_claims のみ=DW は確定しない）。
"""
import json
import os
import sys
import tempfile
import urllib.request
import urllib.error
import socket
from pathlib import Path

sys.path.insert(0, "/home/takasan/dev-workcell")
from dw import workcell as W  # noqa: E402

_ENDPOINT = "http://localhost:8005/v1/chat/completions"
_MODEL = "Qwen3.6-35B-A3B"

# 狭める元（ODF-02 の DW 候補）と、独立 audit が出した直す対象
ODF02_CANDIDATE = ("DW-consumed assignment-context record with 3 fields (model->task-type capability boundaries; "
                   "surrounding-environment metadata; escalation criteria). DM auto-assigns or escalates.")
FINDINGS_TO_FIX = ["scope_expansion", "responsibility_leakage", "unsound_trust_root",
                   "IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION", "not_minimal (3-field schema)"]

FORBIDDEN_SCOPE = ["environment", "inventory", "effectiveness", "gpu", "residency", "monitor", "surrounding"]


def _chat(system, user, seed=0, max_tokens=900):
    body = json.dumps({"model": _MODEL, "temperature": 0, "seed": seed, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(_ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""


def _json(t):
    i, j = t.find("{"), t.rfind("}")
    try:
        return json.loads(t[i:j + 1]) if 0 <= i < j else None
    except Exception:
        return None


def minimality_test(design):
    """設計タスクの load-bearing test（決定的）。狭さ・trust-root・presence≠sufficiency・scope を検査。"""
    fails = []
    if not isinstance(design, dict):
        return {"passed": False, "cases": 1, "failures": ["design not an object"]}
    fields = design.get("load_bearing_fields", [])
    if not isinstance(fields, list) or len(fields) == 0 or len(fields) > 2:
        fails.append(f"load-bearing fields must be 1..2 (minimal); got {fields}")
    if "declar" not in str(design.get("trust_root", "")).lower():
        fails.append("trust_root must be an explicit human DECLARATION (not grounded)")
    if design.get("presence_not_sufficiency") is not True:
        fails.append("must explicitly state presence-of-context != assignment sufficiency")
    if not str(design.get("escalation_rule", "")).strip():
        fails.append("must state one explicit escalation rule")
    for f in (fields if isinstance(fields, list) else []):
        if any(t in str(f).lower() for t in FORBIDDEN_SCOPE):
            fails.append(f"load-bearing field re-expands scope: {f!r}")
    return {"passed": not fails, "cases": 4 + (len(fields) if isinstance(fields, list) else 0), "failures": fails}


_WORKER_SYS = (
    "You NARROW an over-scoped design to the MINIMAL change that resolves ONLY the observed problem: a DW manager "
    "having to ad-hoc ask a human 'is this model enough?' at worker assignment. Fix the audit findings. Constraints: "
    "at most 2 load-bearing fields; the trust root is an explicit human DECLARATION (never a grounded claim); state "
    "explicitly that context-presence is NOT an assignment-sufficiency guarantee; exactly one escalation rule; do NOT "
    "make environment / inventory / effectiveness / GPU / monitoring a load-bearing field. Return ONLY JSON "
    "{\"load_bearing_fields\":[...],\"trust_root\":\"...\",\"presence_not_sufficiency\":true,\"escalation_rule\":\"...\","
    "\"scope_excluded\":[...],\"rationale\":\"...\"}."
)


class NarrowWorker(W.__class__ if False else object):
    identity = "qwen3.6@8005#odf-narrow-worker"
    def __init__(self):
        self._n = 0
        self._fb = None
    def set_feedback(self, fb):
        self._fb = fb
    def generate(self):
        self._n += 1
        u = (f"OVER-SCOPED CANDIDATE:\n{ODF02_CANDIDATE}\nAUDIT FINDINGS TO FIX:\n{FINDINGS_TO_FIX}\n")
        if self._fb:
            u += f"\nPrior narrowed version still failed. Fix ALL of:\n{json.dumps(self._fb, ensure_ascii=False)[:900]}\n"
        design = _json(_chat(_WORKER_SYS, u + "\nReturn the JSON.", seed=11 + self._n)) or {}
        tr = minimality_test(design)
        return {"identity": self.identity, "run_id": f"{self.identity}-run{self._n}", "diff": json.dumps(design, ensure_ascii=False),
                "test_result": tr, "problems": tr.get("failures", []), "_design": design}


_AUD_SYS = (
    "You are an independent design auditor (separate context). Given a NARROWED design, attack it for remaining "
    "scope_expansion, responsibility_leakage (DW judging adequacy instead of applying a declared rule), unsound or "
    "forgeable trust_root, or IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION. Only report SUBSTANTIVE remaining issues. "
    "Return ONLY JSON {\"findings\":[{\"category\":\"...\",\"evidence\":\"...\"}]}."
)


def audit(design_json, seed=307):
    o = _json(_chat(_AUD_SYS, f"NARROWED_DESIGN:\n{design_json}\n\nReturn the JSON.", seed=seed)) or {"findings": []}
    return {"identity": "qwen3.6@8005#odf-narrow-auditor", "run_id": f"aud-{seed}",
            "findings": [{"finding_id": f"F{i}", "category": (f.get("category", "other") or "other").lower().replace(" ", "_")[:40] if isinstance(f.get("category"), str) else "other",
                          "severity": "MAJOR", "evidence": f.get("evidence", ""), "status": "OPEN"}
                         for i, f in enumerate(o.get("findings", []))]}


def _norm_cat(findings):
    ok = W.FINDING_CATEGORIES
    for f in findings:
        if f["category"] not in ok:
            f["category"] = "scope_expansion" if "scope" in f["category"] else "other"
    return findings


def main():
    d = tempfile.mkdtemp()
    os.environ["DW_DATA_DIR"] = d
    import importlib
    importlib.reload(W)
    TASK = "TASK-ODF-NARROW-01"
    mgr = "claude-manager"
    t = [0]
    def ts():
        t[0] += 1
        return f"2026-07-07T00:00:{t[0]:02d}Z"
    print("### ODF narrowing through real DW workcell (dogfood) ###\n")
    W.create_task(TASK, "ODF", "narrow the assignment-context candidate to minimal + fix trust-root", {}, ts(), mgr)
    W.record_plan(TASK, {"narrow_goal": "≤2 load-bearing fields, declared trust-root, presence≠sufficiency, one escalation rule",
                         "forbidden_assumptions": ["no environment/inventory/effectiveness load-bearing field"]}, ts(), mgr)
    worker = NarrowWorker()
    wr = worker.generate()
    final = wr["_design"]
    W.record_generate(TASK, {k: v for k, v in wr.items() if k != "_design"}, ts())
    print(f"[GENERATE] test passed={wr['test_result']['passed']} fields={final.get('load_bearing_fields')}")
    for f in wr["test_result"].get("failures", []):
        print(f"   test-fail: {f}")
    ar = audit(wr["diff"]); ar["findings"] = _norm_cat(ar["findings"])
    W.record_audit(TASK, ar, ts())
    print(f"[AUDIT] findings={[f['category'] for f in ar['findings']]}")
    rework = 0
    while True:
        state, _ = W.derive_state(TASK)
        if state != "AUDIT_FAILED" or rework >= W.REWORK_ESCALATION_THRESHOLD:
            break
        worker.set_feedback({"test_failures": wr["test_result"].get("failures"), "audit": [f["evidence"] for f in ar["findings"]]})
        wr = worker.generate()
        final = wr["_design"]
        W.record_regenerate(TASK, {k: v for k, v in wr.items() if k != "_design"}, ts())
        print(f"[REGENERATE #{rework+1}] test passed={wr['test_result']['passed']} fields={final.get('load_bearing_fields')}")
        for f in wr["test_result"].get("failures", []):
            print(f"   test-fail: {f}")
        ar = audit(wr["diff"], seed=307 + rework + 1); ar["findings"] = _norm_cat(ar["findings"])
        W.record_audit(TASK, ar, ts())
        print(f"[re-AUDIT] findings={[f['category'] for f in ar['findings']]}")
        rework += 1
    state, view = W.derive_state(TASK)
    print(f"\n[state] {state}")
    result = {"final_design": final, "state": state}
    if state == "READY_FOR_UPPER_REVIEW":
        W.record_upper_review(TASK, {"verdict": "minimality test passed + independent audit clean"}, ts(), mgr)
        try:
            pkt = W.propose_complete(TASK,
                                     observed_results=[{"observed": "narrowed design passed deterministic minimality test + independent audit"}],
                                     proposed_claims=[{"proposed": "minimal assignment-escalation-rule design (declared trust-root, presence!=sufficiency), narrowed from ODF-02, is an implementation candidate on the tested minimality criteria",
                                                       "scope": "tested minimality criteria only — NOT a proof of operational adequacy", "record_ids": []}],
                                     new_gap_candidates=[], ts=ts(), manager_identity=mgr)
            result["result_packet"] = pkt
            print(f"[COMPLETE] RESULT_PACKET → implementation candidate（proposed_claims のみ）")
        except W.WorkflowViolation as e:
            print(f"[COMPLETE REJECTED] {e}")
            result["rejected"] = str(e)
    else:
        print(f"[NO COMPLETE] state={state}（minimality/audit 未収束 → 実装候補に昇格しない）")
    print(f"\n[final minimal design]\n{json.dumps(final, ensure_ascii=False, indent=2)}")
    Path("/home/takasan/egl/experiments/odf_narrow_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
