"""Tests for SLICE-6 client-usable surface (state_report.py + amend.sh shell↔python round-trip)."""
import sys, os, json, hashlib, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autonomy.current_state as cs
import autonomy.state_report as sr
from autonomy.current_state import REPO

AMEND_SH = str(REPO / "autonomy" / "amend.sh")
TMP = REPO / "_tmp_client_ledger.jsonl"


def _run_amend(action, target, content, reason=None):
    args = ["bash", AMEND_SH, action, target, content] + ([reason] if reason else [])
    env = dict(os.environ, AUTONOMY_LEDGER=str(TMP))
    return subprocess.run(args, capture_output=True, text=True, env=env)


def _cleanup():
    try:
        TMP.unlink()
    except Exception:
        pass


def test_T1_state_report_markdown():
    md = sr.render_md(cs.build_current_state())
    assert md.startswith("# 2DER autonomous loop") and "latest DE" in md and "decision queue" in md.lower()
    a = sr.render_md(cs.build_current_state()); b = sr.render_md(cs.build_current_state())
    # deterministic modulo as_of line
    strip = lambda s: "\n".join(l for l in s.splitlines() if "as_of" not in l)
    assert strip(a) == strip(b), "state report not deterministic modulo as_of"


def test_T2_shell_to_python_roundtrip_overlay():
    _cleanup()
    try:
        st0 = cs.build_current_state()
        kinds = {w["kind"] for w in st0["candidate_executable_work"]}
        target = next(iter(kinds)) if kinds else "validation_failure"
        r = _run_amend("TAKA_HOLD", target, "hold from client shell")
        assert r.returncode == 0, f"amend.sh failed: {r.stderr}"
        orig = cs.AUTONOMY_LEDGER
        cs.AUTONOMY_LEDGER = TMP
        try:
            st1 = cs.build_current_state()
            assert st1["taka_events"], "shell event not loaded by python"
            assert st1["authority_pending"], "shell HOLD did not populate authority_pending"
            assert kinds and any(w.get("held_by") for w in st1["candidate_executable_work"]), \
                "shell HOLD produced no overlay effect (shell↔python incompatible)"
        finally:
            cs.AUTONOMY_LEDGER = orig
    finally:
        _cleanup()


def test_T3_unknown_action_rejected():
    _cleanup()
    try:
        r = _run_amend("NOPE", "t", "c")
        assert r.returncode != 0, "amend.sh accepted unknown action"
    finally:
        _cleanup()


def test_T4_amend_emits_valid_json_event():
    _cleanup()
    try:
        _run_amend("TAKA_CONTEXT_ADDITION", "spec_stale", "note with \"quotes\" and \\slash", "why")
        lines = [l for l in TMP.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        ev = json.loads(lines[0])  # must parse
        for k in ("event_id", "ts", "owner", "action", "target_object", "content",
                  "previous_state_ref", "reason", "downstream_effect"):
            assert k in ev, f"missing {k}"
        assert ev["owner"] == "Taka" and ev["event_id"].startswith("AE-")
        assert 'quotes' in ev["content"] and '\\slash' in ev["content"], "escaping lost content"
    finally:
        _cleanup()


def test_T4b_control_chars_stay_valid_json(tmp=None):
    # DEFECT A regression: a TAB/newline in content must NOT break JSON / silently drop the event.
    _cleanup()
    try:
        r = _run_amend("TAKA_CONTEXT_ADDITION", "spec_stale", "tab\there\nand newline")
        assert r.returncode == 0
        line = TMP.read_text().splitlines()[0]
        ev = json.loads(line)  # must parse (strict) — controls are stripped (lossy), not escaped
        # load_taka_events must still return the event (not silently dropped like the pre-fix bug)
        orig = cs.AUTONOMY_LEDGER; cs.AUTONOMY_LEDGER = TMP
        try:
            assert len(cs.load_taka_events()) == 1, "control-char event silently dropped by python loader"
        finally:
            cs.AUTONOMY_LEDGER = orig
    finally:
        _cleanup()


def test_T6b_high_water_past_octal_boundary():
    # DEFECT B regression: zero-padded ids AE-00008/00009 must not be misparsed as octal.
    _cleanup()
    try:
        TMP.write_text('{"event_id": "AE-00009", "action": "TAKA_HOLD", "target_object": "x", "owner": "Taka"}\n')
        r = _run_amend("TAKA_HOLD", "y", "next after 9")
        assert r.returncode == 0, f"amend.sh failed on AE-00009 high-water: {r.stderr}"
        ids = [json.loads(l)["event_id"] for l in TMP.read_text().splitlines() if l.strip()]
        assert ids[-1] == "AE-00010", f"expected AE-00010 after AE-00009, got {ids[-1]} (octal/base bug)"
    finally:
        _cleanup()


def test_T5_amend_read_only_to_sor():
    _cleanup()
    try:
        def sha(p):
            try:
                return hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                return None
        tgts = [REPO / "DESIGN_EVIDENCE_LEDGER.jsonl", REPO / "data" / "events.jsonl"]
        before = {str(p): sha(p) for p in tgts}
        _run_amend("TAKA_HOLD", "x", "c")
        after = {str(p): sha(p) for p in tgts}
        assert before == after, "amend.sh touched SoR/DE ledger"
    finally:
        _cleanup()


def test_T6_append_only_monotonic_ids():
    _cleanup()
    try:
        _run_amend("TAKA_HOLD", "a", "1")
        _run_amend("TAKA_HOLD", "b", "2")
        lines = [json.loads(l) for l in TMP.read_text().splitlines() if l.strip()]
        assert len(lines) == 2, "append-only violated"
        ids = [int(e["event_id"].split("-")[1]) for e in lines]
        assert ids == sorted(ids) and ids[0] < ids[1], f"AE ids not monotonic: {ids}"
    finally:
        _cleanup()


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
