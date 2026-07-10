"""Tests for SLICE-8 general problem-ingest path. Hermetic: monkeypatch worker + retrieval, temp files."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autonomy.ingest as ing
from autonomy.current_state import REPO

TP = REPO / "_tmp_problems.jsonl"
TH = REPO / "_tmp_handoffs.jsonl"


def _use_tmp():
    for p in (TP, TH):
        if p.exists():
            p.unlink()
    ing.PROBLEMS, ing.HANDOFFS = TP, TH
    ing._worker_infer_objective = lambda raw: "inferred: " + raw[:20]
    ing.answer_question = lambda q: ({"answer_claims": [{"text": "swap は MEASURED ~174.5s/回 (co-serve IMPOSSIBLE)", "record_ids": ["DE-0074"]}],
                                      "open_gaps": ["3分の内訳が未プロファイル"]}, ["DE-0074", "DE-0073"], "raw")
    ing.validate_answer = lambda ans, ids: {"metrics": {"m1_grounding_integrity_pass": True}}


def _restore():
    ing.PROBLEMS, ing.HANDOFFS = REPO / "PROBLEMS.jsonl", REPO / "HANDOFFS.jsonl"
    for p in (TP, TH):
        try:
            p.unlink()
        except Exception:
            pass


def test_ingest_problem_objective_split():
    _use_tmp()
    try:
        p = ing.ingest_problem("swap 3分なんとか", stated_objective=None)
        assert p["problem_id"].startswith("PB-") and p["owner"] == "Taka"
        assert p["stated_objective"] is None, "stated must stay None unless Taka provides"
        io = p["inferred_working_objective"]
        assert io and io["authority"] == "NON_AUTHORITATIVE_WORKER_GUESS", "inferred must be non-authoritative"
    finally:
        _restore()


def test_handoff_has_live_history_and_honest_missing():
    _use_tmp()
    try:
        h = ing.assemble_handoff(ing.ingest_problem("swap 3分", stated_objective=None))
        assert h["relevant_history"]["status"].startswith("LIVE")
        assert "DE-0074" in h["relevant_history"]["record_ids"]
        assert h["relevant_history"]["claims"], "history claims must be present"
        # honest MISSING (not faked)
        for stage in ("triage", "detection", "candidate_frames_realization_paths"):
            assert h[stage]["status"] == "MISSING", f"{stage} must be honestly MISSING, not faked"
            assert h[stage]["reason"], "MISSING must carry a reason"
        assert "route to Claude" in h["next_operation"]
        assert "NOT the raw prompt" in h["investigator_task"]["must_start_from"]
    finally:
        _restore()


def test_ingest_read_only_to_sor():
    _use_tmp()
    try:
        def sha(p):
            try:
                return hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                return None
        tgts = [REPO / "DESIGN_EVIDENCE_LEDGER.jsonl", REPO / "data" / "events.jsonl"]
        before = {str(p): sha(p) for p in tgts}
        ing.assemble_handoff(ing.ingest_problem("x", None))
        after = {str(p): sha(p) for p in tgts}
        assert before == after, "ingest must not write SoR/DE ledger"
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
