"""SLICE-3: deterministic next-work router (2DER autonomous loop v0).

Selects the next work item from CURRENT_STATE using the frozen §6 ordering — existing
status/failure semantics only, NO new composite score. Respects Taka overlay (held/rejected
items are already filtered/flagged by the state builder). Returns the pick + a rationale.
"""
# §6 priority order (plan docs/autonomous_loop_v0_audit_and_plan.md). Lower = first.
PRIORITY = {
    "seal_mismatch": 1,          # broken integrity invariant
    "instrument_invalid": 2,     # construct audit gate_pass=false
    "validation_failure": 3,     # failed validation (M1 fail / coverage not ok)
    "approved_adapter": 4,       # DESIGN-VALID small adapter not implemented
    "spec_stale": 5,             # stale state/spec
    "wiring": 6,                 # unresolved technical wiring
}


def select_next_work(state):
    """Return (work_item, rationale) or (None, reason). Deterministic; held items skipped."""
    work = [w for w in state.get("candidate_executable_work", []) if not w.get("held_by")]
    if not work:
        held = [w for w in state.get("candidate_executable_work", []) if w.get("held_by")]
        return None, (f"no actionable work ({len(held)} held by Taka)" if held else "no candidate work")
    # sort by (mechanical priority field, then §6 kind order, then ref string) — fully deterministic
    def key(w):
        return (w.get("priority", 99), PRIORITY.get(w.get("kind"), 99), str(w.get("ref")))
    work.sort(key=key)
    top = work[0]
    rationale = (f"selected kind='{top.get('kind')}' (priority P{top.get('priority')}, "
                 f"§6 rank {PRIORITY.get(top.get('kind'), 99)}) as the highest-priority non-held work "
                 f"of {len(work)} candidates")
    return top, rationale
