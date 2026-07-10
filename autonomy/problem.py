"""2DER as CONTINUOUS PROGRAM ACTOR. TAKA → 2DER FULL PATH → INVESTIGATOR_TASK → CLAUDE →
RESULT → 2DER → STATE/TRACE UPDATE → NEXT OP.

- run_problem(): runs the fullest callable path HISTORY→DETECTION→RECONSTRUCTION→check→next-op on a
  general problem, persisting EVERY stage to an append-only PROBLEM_LOG.jsonl (the process-trace
  adapter — reuses the existing event-log pattern, NOT a new DB), and emits an INVESTIGATOR_TASK.
- return_result(): ingests a machine-readable Claude RESULT OBJECT; 2DER (not Claude) selects the
  next operation; Claude finding≠evidence, suggestion≠next-op, verdict≠disposition.
- problem_state(): folds PROBLEM_LOG for a problem_id → continuous state, resumable WITHOUT any
  Claude session memory.
Read-only to SoR/DE ledger; writes only PROBLEMS.jsonl / PROBLEM_LOG.jsonl. Requires vLLM :8005.
CLOSED-NEGATIVE mechanisms are run as-is and never relabeled positive; their output correctness is UNVALIDATED.
"""
import sys, os, json, datetime, re
import concurrent.futures as cf
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "experiments"))
from autonomy.ingest import ingest_problem  # reuse Taka-problem record + non-authoritative inferred objective

PLOG = os.path.join(REPO, "PROBLEM_LOG.jsonl")

INVESTIGATOR_TASK_FIELDS = ["task_id", "parent_problem_id", "2der_state_ref", "process_trace_ref",
                            "objective", "current_reality", "relevant_history", "detection_outputs",
                            "reconstruction_outputs", "selected_next_operation", "open_gaps",
                            "artifact_refs", "allowed_actions", "stop_conditions", "original_problem"]
RESULT_OBJECT_FIELDS = ["task_id", "parent_problem_id", "findings", "actual_path", "evidence_refs",
                        "actions_taken", "result", "remaining_uncertainty", "suggested_next_actions"]


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _hw(prefix, key):
    n = 0
    try:
        for line in open(PLOG):
            m = re.search(rf'"{key}":\s*"{prefix}-(\d+)"', line)
            if m:
                n = max(n, int(m.group(1)))
    except Exception:
        pass
    return n


def _log(problem_id, event_type, payload):
    ev = {"event_id": f"PE-{_hw('PE', 'event_id') + 1:05d}", "ts": _now(),
          "problem_id": problem_id, "event_type": event_type, "payload": payload}
    with open(PLOG, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


# ---- stage runners: the ACTUAL owned mechanisms (same calls as dogfood_fullpath) ----
def _stage_history(frame):
    from egl.self_grounding import answer_question, validate_answer
    ans, rids, raw = answer_question(frame)
    ok = isinstance(ans, dict)
    claims = (ans or {}).get("answer_claims") or [] if ok else []
    gaps = (ans or {}).get("open_gaps") or [] if ok else []
    val = validate_answer(ans, set(rids)) if ok else None
    return {"mechanism": "self_grounding.answer_question (LIVE)", "record_ids": rids,
            "claims": [{"text": c.get("text"), "src": c.get("record_ids")} for c in claims if isinstance(c, dict)],
            "open_gaps": gaps, "grounded_m1": (val or {}).get("metrics", {}).get("m1_grounding_integrity_pass")}


def _stage_detection(frame):
    import run_afe_walking as afe
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        signals = list(ex.map(lambda o: afe.run_operator(o, frame), afe.ADMITTED))
    cands = afe.aggregate(signals)
    fec = afe.orchestrate(frame, cands)
    skeptic = afe.arm_ABE("B", frame)
    n_sig = sum(1 for s in signals if s.get("verdict") == "SIGNAL")
    return {"mechanism": "AFE run_operator/aggregate/orchestrate + skepticism (EXHIBIT; content WEAK/NEG evidence; UNVALIDATED)",
            "missing_dimensions": fec, "skeptic_checks": skeptic,
            "survived_candidates": [{"structure": c["structure"], "support": c["support_count"]} for c in cands][:8],
            "dropped": f"{len(signals) - n_sig}/{len(signals)} operators NO_SIGNAL"}


def _stage_reconstruction(frame):
    import run_scheduler_exhibit as sch
    rebuild, rtrace = sch.rs_run(frame, seed=0, V=3, cap=1)   # one real attempt (view→sig→compare→rebuild→check)
    return {"mechanism": "scheduler rs_run view→signature→compare→rebuild (EXHIBIT; CLOSED-NEGATIVE at HBB bar; UNVALIDATED)",
            "alternative_frame": rebuild, "changed_subject_level_distinction": rtrace.get("resolved"),
            "attempts": rtrace.get("attempts")}


def _select_next_operation(hist, det, recon):
    """2DER-side selection (NOT Claude). Deterministic template from the stage outputs."""
    return ("INVESTIGATE: 2DER の reconstruction が出した alternative frame と detection の missing-dimensions / "
            "skeptic-question を、actual runtime + relevant_history の constraint に照らして reversible に検証し、"
            "machine-readable RESULT を返す。提供済み history/measured 値は再導出しない。correctness は未検証扱い。")


def _build_investigator_task(prob, hist, det, recon, next_op):
    pid = prob["problem_id"]
    return {
        "task_id": f"IT-{_hw('IT', 'task_id') + 1:05d}",
        "parent_problem_id": pid,
        "2der_state_ref": pid,                       # resolvable via problem_state(pid)
        "process_trace_ref": f"PROBLEM_LOG.jsonl:{pid}",
        "objective": prob.get("stated_objective") or (prob.get("inferred_working_objective") or {}).get("text"),
        "current_reality": {"repo": "CURRENT_STATE.json (build_state.py)",
                            "runtime": "investigator が nvidia-smi/docker/serve script を現物で読む必要(2DER 未取得)"},
        "relevant_history": {"record_ids": hist.get("record_ids", []), "claims": hist.get("claims", []),
                            "grounded_m1": hist.get("grounded_m1"), "status": hist.get("status", "OK")},
        "detection_outputs": det,
        "reconstruction_outputs": recon,
        "selected_next_operation": next_op,          # 2DER selected, not Claude
        "open_gaps": hist.get("open_gaps", []),
        "artifact_refs": ["~/models_trtllm/serve_*.sh", "nvidia-smi / docker ps", "DE: " + ", ".join(hist.get("record_ids", []))],
        "allowed_actions": ["read-only investigation", "reversible local technical actions", "web search"],
        "stop_conditions": ["live service interruption (e.g. :8005 stop) → STOP_FOR_TAKA",
                            "objective/value/irreversible/program-scope decision → STOP_FOR_TAKA"],
        "original_problem": prob["raw_input"],
        "reconstruction_correctness": "UNVALIDATED (EXHIBIT run; CLOSED-NEGATIVE at HBB bar) — investigator must judge, not assume.",
    }


def _safe_stage(pid, name, fn, frame):
    """Run a stage; on failure (e.g. :8005 outage) log a STAGE_*_ERROR event and continue with a
    flagged UNAVAILABLE payload so the loop stays resumable/observable from the log (not an uncaught crash)."""
    try:
        out = fn(frame); _log(pid, f"STAGE_{name}", out); return out
    except Exception as e:
        out = {"mechanism": name, "status": "UNAVAILABLE", "error": f"{type(e).__name__}: {e}"}
        _log(pid, f"STAGE_{name}_ERROR", out); return out


def run_problem(raw_input, stated_objective=None, context_refs=None):
    prob = ingest_problem(raw_input, stated_objective, context_refs)
    pid = prob["problem_id"]
    _log(pid, "INGESTED", prob)
    frame = raw_input + (" " + stated_objective if stated_objective else "")
    hist = _safe_stage(pid, "HISTORY", _stage_history, frame)
    det = _safe_stage(pid, "DETECTION", _stage_detection, frame)
    recon = _safe_stage(pid, "RECONSTRUCTION", _stage_reconstruction, frame)
    next_op = _select_next_operation(hist, det, recon)
    _log(pid, "NEXT_OP", {"selected": next_op, "by": "2DER"})
    task = _build_investigator_task(prob, hist, det, recon, next_op)
    for k in INVESTIGATOR_TASK_FIELDS:
        assert k in task, f"INVESTIGATOR_TASK missing {k}"
    _log(pid, "INVESTIGATOR_TASK_ISSUED", task)
    return task


def return_result(result_object):
    """PHASE 3: ingest a Claude RESULT OBJECT. 2DER selects next-op. Claude finding≠evidence."""
    missing = [k for k in RESULT_OBJECT_FIELDS if k not in result_object]
    if missing:
        raise ValueError(f"RESULT OBJECT missing fields: {missing}")
    pid = result_object["parent_problem_id"]
    _log(pid, "CLAUDE_RESULT", result_object)
    # 2DER-side next-op selection from the result (Claude's suggested_next_actions are PROPOSALS only)
    if result_object.get("authority_issue"):
        next_op = f"STOP_FOR_TAKA: {result_object['authority_issue']}"
    elif result_object.get("suggested_next_actions"):
        next_op = ("2DER adopts (as candidate, not committed): " + str(result_object["suggested_next_actions"][0])
                   + " — Claude suggestion≠next-op; 2DER retains selection.")
    else:
        next_op = "no next action proposed; hold."
    _log(pid, "NEXT_OP_AFTER_RESULT", {"selected": next_op, "by": "2DER",
                                       "note": "Claude finding≠validated evidence; suggestion≠next-op; verdict≠program disposition."})
    return {"next_operation": next_op, "problem_state": problem_state(pid)}


def problem_state(problem_id):
    """Fold PROBLEM_LOG for one problem → continuous state (resumable w/o Claude session memory)."""
    evs = []
    try:
        for line in open(PLOG):
            line = line.strip()
            if line:
                o = json.loads(line)
                if o.get("problem_id") == problem_id:
                    evs.append(o)
    except Exception:
        pass
    by = {}
    for e in evs:
        by.setdefault(e["event_type"], []).append(e["payload"])
    prob = (by.get("INGESTED") or [{}])[-1]
    tasks = by.get("INVESTIGATOR_TASK_ISSUED", [])
    results = by.get("CLAUDE_RESULT", [])
    return {
        "problem_id": problem_id,
        "problem": prob.get("raw_input"),
        "stated_objective": prob.get("stated_objective"),
        "working_objective_inferred": (prob.get("inferred_working_objective") or {}).get("text"),
        "current_reality": (by.get("STAGE_HISTORY") or [{}])[-1].get("record_ids") if by.get("STAGE_HISTORY") else None,
        "history_refs": (by.get("STAGE_HISTORY") or [{}])[-1].get("record_ids") if by.get("STAGE_HISTORY") else [],
        "process_trace": [{"event_type": e["event_type"], "ts": e["ts"], "event_id": e["event_id"]} for e in evs],
        "detection_outputs": (by.get("STAGE_DETECTION") or [None])[-1],
        "reconstruction_outputs": (by.get("STAGE_RECONSTRUCTION") or [None])[-1],
        "attempted_paths": [r.get("actual_path") for r in results],
        "failed_paths": [r.get("actual_path") for r in results if r.get("result") in ("FAILED", "BLOCKED")],
        "open_gaps": (by.get("STAGE_HISTORY") or [{}])[-1].get("open_gaps") if by.get("STAGE_HISTORY") else [],
        "current_next_operation": (by.get("NEXT_OP_AFTER_RESULT") or by.get("NEXT_OP") or [{}])[-1].get("selected"),
        "claude_tasks": [t.get("task_id") for t in tasks],
        "claude_results": [{"task_id": r.get("task_id"), "result": r.get("result")} for r in results],
        "taka_corrections": by.get("TAKA_CORRECTION", []),
        "authority_pending": [e for e in evs if str((e.get("payload") or {}).get("selected", "")).startswith("STOP_FOR_TAKA")],
        "n_events": len(evs),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_input"); ap.add_argument("--objective", default=None)
    a = ap.parse_args()
    t = run_problem(a.raw_input, a.objective)
    print(json.dumps(t, ensure_ascii=False, indent=2))
