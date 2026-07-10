"""SLICE-5 backbone: Taka correction-event appender (2DER autonomous loop v0).

Contract: docs/autonomous_loop_v0_audit_and_plan.md §10. Taka corrections MUST be
machine-readable events, NOT rendered-text edits. Append-only AUTONOMY_LEDGER.jsonl
(program-governance, separate from the knowledge SoR). Reversible: a later event on the
same target supersedes an earlier one; history is preserved.

Event: {event_id, ts, owner:"Taka", action, target_object, content, previous_state_ref, reason?, downstream_effect}
"""
import sys, os, json, argparse, datetime, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AUTONOMY_LEDGER = REPO / "AUTONOMY_LEDGER.jsonl"

ACTIONS = {"TAKA_CORRECTION", "TAKA_PRIORITY_OVERRIDE", "TAKA_HOLD", "TAKA_REJECT",
           "TAKA_REDIRECT", "TAKA_AUTHORITY_RECLASSIFICATION", "TAKA_CONTEXT_ADDITION"}

# router effect per action. HONEST about what the v0 overlay ACTUALLY realizes vs what is
# only surfaced for Taka in the decision queue (C≠H: do not overstate the realized effect).
_DOWNSTREAM = {
    "TAKA_PRIORITY_OVERRIDE": "APPLIED: sets priority on matching candidate_executable_work",
    "TAKA_HOLD": "APPLIED: matching work item marked held (router skips)",
    "TAKA_REJECT": "APPLIED: matching work item dropped",
    "TAKA_REDIRECT": "SURFACED-ONLY: shown in authority_pending; task replacement NOT auto-applied in v0",
    "TAKA_AUTHORITY_RECLASSIFICATION": "SURFACED-ONLY: shown in authority_pending; class change NOT auto-applied in v0",
    "TAKA_CORRECTION": "RECORDED: kept in taka_events; no automatic state change (surfaced for review)",
    "TAKA_CONTEXT_ADDITION": "RECORDED: kept in taka_events; no automatic state change (surfaced for review)",
}


def _high_water():
    n = 0
    try:
        for line in AUTONOMY_LEDGER.read_text().splitlines():
            m = re.match(r'.*"event_id":\s*"AE-(\d+)"', line)
            if m:
                n = max(n, int(m.group(1)))
    except Exception:
        pass
    return n


def append_taka_event(action, target_object, content, reason=None, previous_state_ref=None):
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}; allowed={sorted(ACTIONS)}")
    ev = {
        "event_id": f"AE-{_high_water() + 1:05d}",
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "owner": "Taka",
        "action": action,
        "target_object": target_object,
        "content": content,
        "previous_state_ref": previous_state_ref,
        "reason": reason,
        "downstream_effect": _DOWNSTREAM[action],
    }
    with open(AUTONOMY_LEDGER, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def main():
    ap = argparse.ArgumentParser(description="Append a Taka correction/adjudication event (owner=Taka).")
    ap.add_argument("action", choices=sorted(ACTIONS))
    ap.add_argument("target_object", help="e.g. a DE id, a candidate_work kind, a branch name, a spec section")
    ap.add_argument("content", help="the correction/decision content (free text or a value)")
    ap.add_argument("--reason", default=None)
    ap.add_argument("--previous-state-ref", default=None)
    a = ap.parse_args()
    ev = append_taka_event(a.action, a.target_object, a.content, a.reason, a.previous_state_ref)
    print(json.dumps(ev, ensure_ascii=False))
    print(f"-> {AUTONOMY_LEDGER} | {ev['event_id']} {ev['action']} target={ev['target_object']} "
          f"effect={ev['downstream_effect']}")


if __name__ == "__main__":
    main()
