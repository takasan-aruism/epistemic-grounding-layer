"""Tests for SLICE-5 Taka correction-event backbone + state overlay + dashboard.
Hermetic: monkeypatch AUTONOMY_LEDGER to a temp path (no fake Taka events in the real log)."""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autonomy.amend as amend
import autonomy.current_state as cs
import autonomy.dashboard as dash
from autonomy.current_state import REPO

TMP = REPO / "_tmp_autonomy_ledger.jsonl"


def _use_tmp():
    if TMP.exists():
        TMP.unlink()
    amend.AUTONOMY_LEDGER = TMP
    cs.AUTONOMY_LEDGER = TMP


def _restore():
    amend.AUTONOMY_LEDGER = REPO / "AUTONOMY_LEDGER.jsonl"
    cs.AUTONOMY_LEDGER = REPO / "AUTONOMY_LEDGER.jsonl"
    try:
        TMP.unlink()
    except Exception:
        pass


def test_T1_event_schema():
    _use_tmp()
    try:
        ev = amend.append_taka_event("TAKA_HOLD", "validation_failure", "pause while I look", reason="r")
        for k in ("event_id", "ts", "owner", "action", "target_object", "content",
                  "previous_state_ref", "reason", "downstream_effect"):
            assert k in ev, f"missing {k}"
        assert ev["owner"] == "Taka" and ev["event_id"].startswith("AE-")
        assert ev["downstream_effect"]  # non-empty router effect
    finally:
        _restore()


def test_T2_unknown_action_rejected():
    _use_tmp()
    try:
        try:
            amend.append_taka_event("NOPE", "x", "y")
            assert False, "should have raised"
        except ValueError:
            pass
    finally:
        _restore()


def test_T3_overlay_hold_has_visible_effect():
    _use_tmp()
    try:
        st0 = cs.build_current_state()
        kinds = {w["kind"] for w in st0["candidate_executable_work"]}
        target = next(iter(kinds)) if kinds else "validation_failure"
        amend.append_taka_event("TAKA_HOLD", target, "hold pending review")
        st1 = cs.build_current_state()
        assert st1["taka_events"], "taka_events not loaded"
        assert st1["authority_pending"], "authority_pending not populated by HOLD"
        assert kinds, "real repo should have candidate work (validation failures) to exercise effect"
        assert any("HOLD" in e for e in st1["taka_overlay_effects"]), "HOLD produced no visible downstream effect"
        assert any(w.get("held_by") for w in st1["candidate_executable_work"]), "no work item marked held"
        assert st1["field_origins"]["taka_events"] == "TAKA-OWNED"
    finally:
        _restore()


def test_T4_supersession_latest_wins():
    _use_tmp()
    try:
        amend.append_taka_event("TAKA_HOLD", "spec_stale", "first")
        amend.append_taka_event("TAKA_REDIRECT", "spec_stale", "second")
        st = cs.build_current_state()
        actives = [a for a in st["authority_pending"] if a["target_object"] == "spec_stale"]
        assert len(actives) == 1 and actives[0]["action"] == "TAKA_REDIRECT", \
            "latest event per target must win (append-only supersession)"
    finally:
        _restore()


def test_T4b_supersession_clears_prior_effect():
    _use_tmp()
    try:
        st0 = cs.build_current_state()
        kinds = {w["kind"] for w in st0["candidate_executable_work"]}
        target = next(iter(kinds)) if kinds else "validation_failure"
        amend.append_taka_event("TAKA_HOLD", target, "hold")
        held_after_hold = any(w.get("held_by") for w in cs.build_current_state()["candidate_executable_work"])
        amend.append_taka_event("TAKA_REDIRECT", target, "redirect instead")  # surfaced-only, supersedes HOLD
        st2 = cs.build_current_state()
        held_after_redirect = any(w.get("held_by") for w in st2["candidate_executable_work"])
        assert held_after_hold and not held_after_redirect, \
            "superseding event must CLEAR the prior HOLD's realized effect (reversibility of effect)"
    finally:
        _restore()


def test_T5_dashboard_self_contained():
    _use_tmp()
    try:
        h = dash.render(cs.build_current_state())
        assert "autonomous loop" in h and "amend.py" in h
        assert "http://" not in h and "https://" not in h and "src=" not in h, "must be self-contained (no external refs)"
        assert h.startswith("<!doctype html>")
    finally:
        _restore()


def test_T6_amend_read_only_to_sor():
    _use_tmp()
    try:
        def sha(p):
            try:
                return hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                return None
        tgts = [REPO / "DESIGN_EVIDENCE_LEDGER.jsonl", REPO / "data" / "events.jsonl"]
        before = {str(p): sha(p) for p in tgts}
        amend.append_taka_event("TAKA_CONTEXT_ADDITION", "x", "note")
        after = {str(p): sha(p) for p in tgts}
        assert before == after, "amend must not touch SoR/DE ledger"
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
