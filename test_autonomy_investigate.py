"""Tests for SLICE-3/4 router + investigator. Hermetic: monkeypatch the Qwen worker call and
point INVESTIGATIONS at a temp file (no live model, no pollution, no SoR writes)."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autonomy.router as router
import autonomy.investigate as inv
from autonomy.current_state import REPO

TMP = REPO / "_tmp_investigations.jsonl"


def test_router_deterministic_and_skips_held():
    st = {"candidate_executable_work": [
        {"priority": 3, "kind": "validation_failure", "ref": "b"},
        {"priority": 1, "kind": "seal_mismatch", "ref": "a"},
        {"priority": 3, "kind": "validation_failure", "ref": "a", "held_by": "AE-1"},
    ]}
    pick, why = router.select_next_work(st)
    assert pick["kind"] == "seal_mismatch", "router must pick lowest priority number first"
    assert "seal_mismatch" in why
    # all held -> None
    st2 = {"candidate_executable_work": [{"priority": 1, "kind": "seal_mismatch", "ref": "a", "held_by": "x"}]}
    pick2, why2 = router.select_next_work(st2)
    assert pick2 is None and "held" in why2


def test_router_tiebreak_deterministic_under_shuffle():
    # equal priority -> §6 kind-rank then ref-string tiebreak; must be stable regardless of input order
    items = [{"priority": 3, "kind": "validation_failure", "ref": "z"},
             {"priority": 3, "kind": "spec_stale", "ref": "a"},
             {"priority": 3, "kind": "validation_failure", "ref": "a"}]
    picks = set()
    for order in ([0, 1, 2], [2, 1, 0], [1, 0, 2], [2, 0, 1]):
        st = {"candidate_executable_work": [items[i] for i in order]}
        p, _ = router.select_next_work(st)
        picks.add((p["kind"], str(p["ref"])))
    assert len(picks) == 1, f"router pick not order-invariant: {picks}"
    assert picks == {("validation_failure", "a")}, f"tiebreak wrong: {picks}"  # rank3 < spec_stale rank5; ref 'a'<'z'


def test_dedup_skips_already_investigated():
    st = {"candidate_executable_work": [{"priority": 3, "kind": "validation_failure", "ref": "R"}],
          "investigations": [{"inv_id": "INV-00001", "work_ref": {"kind": "validation_failure", "ref": "R"},
                              "taka_steer": None}]}
    out, why = inv.run_one_cycle(st)
    assert out is None and "already investigated" in why, "must not re-investigate un-steered work"
    # once Taka steers it, it becomes eligible again
    st["investigations"][0]["taka_steer"] = {"action": "TAKA_CORRECTION", "content": "APPROVED"}
    orig = inv.run_investigation
    inv.run_investigation = lambda w: {"classification": "E_MISSING_EVIDENCE", "findings": "x",
                                       "proposed_next_action": "y", "reversible": True, "confidence": "LOW"}
    orig_led = inv.INVESTIGATIONS; inv.INVESTIGATIONS = TMP
    try:
        if TMP.exists():
            TMP.unlink()
        out2, _ = inv.run_one_cycle(st)
        assert out2 is not None, "steered work should be investigable again"
    finally:
        inv.run_investigation = orig; inv.INVESTIGATIONS = orig_led
        try:
            TMP.unlink()
        except Exception:
            pass


def test_investigate_schema_and_class_clamped(monkeypatch=None):
    orig_chat, orig_led = inv._vllm_chat, inv.INVESTIGATIONS
    inv.INVESTIGATIONS = TMP
    try:
        if TMP.exists():
            TMP.unlink()
        # mock worker: returns a finding with an INVALID classification -> must clamp to G_UNKNOWN
        inv._vllm_chat = lambda prompt, max_tokens=900: json.dumps({
            "findings": "x", "expected": "y", "actual": "z",
            "classification": "TOTALLY_MADE_UP", "proposed_next_action": "look", "reversible": True, "confidence": "LOW"})
        work = {"priority": 3, "kind": "validation_failure", "ref": {"artifact": "experiments/hbb_egl_bridge_replay_result.json"}}
        finding = inv.run_investigation(work)
        assert finding["classification"] == "G_UNKNOWN", "invalid class must clamp to G_UNKNOWN"
        rec = inv.record_investigation(work, finding)
        for k in ("inv_id", "ts", "investigator", "senior_verified", "taka_status", "work_ref", "finding"):
            assert k in rec
        assert rec["senior_verified"] is False and rec["taka_status"] == "PROPOSED", "must be un-verified/proposed (honest)"
        assert rec["investigator"] == "qwen-first-pass"
        assert rec["inv_id"].startswith("INV-")
        # loadable
        got = inv.load_investigations()
        assert len(got) == 1 and got[0]["inv_id"] == rec["inv_id"]
    finally:
        inv._vllm_chat, inv.INVESTIGATIONS = orig_chat, orig_led
        try:
            TMP.unlink()
        except Exception:
            pass


def test_investigate_read_only_to_sor():
    orig_chat, orig_led = inv._vllm_chat, inv.INVESTIGATIONS
    inv.INVESTIGATIONS = TMP
    try:
        def sha(p):
            try:
                return hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                return None
        tgts = [REPO / "DESIGN_EVIDENCE_LEDGER.jsonl", REPO / "data" / "events.jsonl"]
        before = {str(p): sha(p) for p in tgts}
        inv._vllm_chat = lambda prompt, max_tokens=900: json.dumps({
            "findings": "x", "expected": "y", "actual": "z", "classification": "E_MISSING_EVIDENCE",
            "proposed_next_action": "look", "reversible": True, "confidence": "LOW"})
        work = {"priority": 3, "kind": "validation_failure", "ref": {"artifact": "experiments/hbb_egl_bridge_replay_result.json"}}
        inv.record_investigation(work, inv.run_investigation(work))
        after = {str(p): sha(p) for p in tgts}
        assert before == after, "investigator must not write SoR/DE ledger"
    finally:
        inv._vllm_chat, inv.INVESTIGATIONS = orig_chat, orig_led
        try:
            TMP.unlink()
        except Exception:
            pass


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
