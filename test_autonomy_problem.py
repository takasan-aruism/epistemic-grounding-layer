"""Tests for autonomy/problem.py — 2DER as continuous actor. Hermetic: monkeypatch stage mechanisms
+ ingest, temp PROBLEM_LOG. Checks: full-path stages logged, INVESTIGATOR_TASK complete, RESULT return
(2DER selects next-op, not Claude), continuous state fold, read-only."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autonomy.problem as P
from autonomy.current_state import REPO

TLOG = os.path.join(REPO, "_tmp_problem_log.jsonl")


def _use_tmp():
    if os.path.exists(TLOG):
        os.remove(TLOG)
    P.PLOG = TLOG
    P.ingest_problem = lambda raw, so=None, cr=None: {"problem_id": "PB-00001", "owner": "Taka", "raw_input": raw,
                                                      "stated_objective": so,
                                                      "inferred_working_objective": {"text": "guess", "authority": "NON_AUTHORITATIVE_WORKER_GUESS"}}
    P._stage_history = lambda f: {"mechanism": "self_grounding (LIVE)", "record_ids": ["DE-0074"],
                                  "claims": [{"text": "measured 174.5s", "src": ["DE-0074"]}], "open_gaps": ["g"], "grounded_m1": True}
    P._stage_detection = lambda f: {"mechanism": "AFE (EXHIBIT)", "missing_dimensions": [{"missing_dimension": "coexistence"}],
                                    "skeptic_checks": ["is it container overhead?"], "survived_candidates": [], "dropped": "x"}
    P._stage_reconstruction = lambda f: {"mechanism": "scheduler (CLOSED-NEGATIVE)", "alternative_frame": "decouple residency",
                                         "changed_subject_level_distinction": True, "attempts": []}


def _restore():
    P.PLOG = os.path.join(REPO, "PROBLEM_LOG.jsonl")
    try:
        os.remove(TLOG)
    except Exception:
        pass


def test_run_problem_full_path_and_task():
    _use_tmp()
    try:
        task = P.run_problem("swap 3分", stated_objective=None)
        for k in P.INVESTIGATOR_TASK_FIELDS:
            assert k in task, f"task missing {k}"
        # every full-path stage was logged (not just the handoff)
        types = [json.loads(l)["event_type"] for l in open(TLOG)]
        for st in ("INGESTED", "STAGE_HISTORY", "STAGE_DETECTION", "STAGE_RECONSTRUCTION", "NEXT_OP", "INVESTIGATOR_TASK_ISSUED"):
            assert st in types, f"stage {st} not persisted"
        assert task["detection_outputs"]["missing_dimensions"], "detection output not in task"
        assert task["reconstruction_outputs"]["alternative_frame"], "reconstruction output not in task"
        assert "UNVALIDATED" in task["reconstruction_correctness"], "recon must be flagged unvalidated"
    finally:
        _restore()


def test_result_return_2der_selects_next_op():
    _use_tmp()
    try:
        task = P.run_problem("swap 3分")
        result = {"task_id": task["task_id"], "parent_problem_id": "PB-00001", "findings": "x",
                  "actual_path": "read serve scripts", "evidence_refs": ["DE-0143"], "actions_taken": [],
                  "result": "PARTIAL", "remaining_uncertainty": "y",
                  "suggested_next_actions": ["test the fp8-kv workaround"], "authority_issue": "needs :8005 downtime"}
        out = P.return_result(result)
        assert out["next_operation"].startswith("STOP_FOR_TAKA"), "authority_issue must route to STOP_FOR_TAKA"
        # note: 2DER retains next-op selection
        note = [json.loads(l) for l in open(TLOG) if '"NEXT_OP_AFTER_RESULT"' in l][-1]["payload"]["note"]
        assert "suggestion" in note and "next-op" in note
    finally:
        _restore()


def test_result_missing_field_rejected():
    _use_tmp()
    try:
        try:
            P.return_result({"task_id": "IT-1"}); assert False
        except ValueError:
            pass
    finally:
        _restore()


def test_continuous_state_resumable():
    _use_tmp()
    try:
        task = P.run_problem("swap 3分")
        P.return_result({"task_id": task["task_id"], "parent_problem_id": "PB-00001", "findings": "f",
                         "actual_path": "p", "evidence_refs": [], "actions_taken": [], "result": "PARTIAL",
                         "remaining_uncertainty": "u", "suggested_next_actions": ["next"]})
        # a FRESH read (simulating a new session with NO memory) reconstructs full state from the log
        st = P.problem_state("PB-00001")
        assert st["problem"] == "swap 3分" and st["claude_results"], "state not resumable from log"
        assert st["detection_outputs"] and st["reconstruction_outputs"], "stage outputs not in state"
        assert st["current_next_operation"], "next-op not held by 2DER state"
        assert len(st["process_trace"]) >= 6, "process trace incomplete"
    finally:
        _restore()


def test_read_only_to_sor():
    _use_tmp()
    try:
        def sha(p):
            try:
                return hashlib.sha256(open(p, "rb").read()).hexdigest()
            except Exception:
                return None
        t = [os.path.join(REPO, "DESIGN_EVIDENCE_LEDGER.jsonl"), os.path.join(REPO, "data", "events.jsonl")]
        before = {p: sha(p) for p in t}
        P.run_problem("x")
        after = {p: sha(p) for p in t}
        assert before == after, "problem.py wrote SoR/DE ledger"
    finally:
        _restore()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"PASS {fn.__name__}")
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
    sys.exit(0 if passed == len(fns) else 1)
