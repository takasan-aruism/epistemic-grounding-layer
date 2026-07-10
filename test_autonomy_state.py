"""Tests for SLICE-1 CURRENT_STATE builder. Hermetic where possible; read-only invariant checked
against the real repo by byte-hashing the ledger/events before and after a build."""
import sys, os, json, hashlib, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autonomy.current_state import build_current_state, REPO, load_de_ledger, verify_seals

VALID_ORIGINS = {"MECHANICAL", "CLAUDE-DERIVED", "TAKA-OWNED", "WORKER-UNVERIFIED"}


def _sha(p):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception:
        return None


def test_T1_latest_de_matches_tail():
    led = load_de_ledger()
    st = build_current_state()
    assert st["latest_de"] == led[-1]["design_evidence_id"]
    assert st["n_de_entries"] == len(led)


def test_T2_known_seal_verifies_ok():
    seals = {s["file"]: s for s in verify_seals()}
    key = "experiments/hbb_egl_bridge_prereg_seal_v0.2.json"
    assert key in seals, "expected known seal present"
    s = seals[key]
    assert s["status"] == "OK", f"known-good seal did not verify OK: {s}"
    assert any("hbb_egl_bridge_prereg_v0.2.md" in p for p in s["verified"])


def test_T3_every_field_has_origin():
    st = build_current_state()
    skip = {"object", "schema_version", "as_of", "field_origins"}
    for k in st:
        if k in skip:
            continue
        assert k in st["field_origins"], f"field {k} missing origin"
        assert st["field_origins"][k] in VALID_ORIGINS, f"bad origin for {k}"


def test_T4_determinism_modulo_as_of():
    a = build_current_state(); b = build_current_state()
    a.pop("as_of"); b.pop("as_of")
    assert a == b, "builder is not deterministic (modulo as_of)"


def test_T5_totality_returns_dict():
    st = build_current_state()
    assert isinstance(st, dict) and st["object"] == "CURRENT_STATE"


def test_T6_read_only_to_sor_and_ledger():
    targets = [REPO / "DESIGN_EVIDENCE_LEDGER.jsonl", REPO / "data" / "events.jsonl"]
    before = {str(p): _sha(p) for p in targets}
    build_current_state()
    after = {str(p): _sha(p) for p in targets}
    assert before == after, "builder mutated SoR/ledger (read-only invariant violated)"


def test_T5b_totality_non_dict_ledger_line(tmp_path=None):
    import tempfile, autonomy.current_state as cs
    orig = cs.LEDGER
    try:
        p = REPO / "_tmp_bad_ledger.jsonl"
        p.write_text('42\n[1,2]\n"str"\n{"design_evidence_id":"DE-9999"}\n')
        cs.LEDGER = p
        led = cs.load_de_ledger()
        assert led == [{"design_evidence_id": "DE-9999"}], "non-dict lines must be dropped"
    finally:
        cs.LEDGER = orig
        try:
            (REPO / "_tmp_bad_ledger.jsonl").unlink()
        except Exception:
            pass


def test_T7_closed_branches_is_claude_derived():
    st = build_current_state()
    assert st["field_origins"]["closed_branches"] == "CLAUDE-DERIVED", \
        "heuristic field must NOT be tagged MECHANICAL (origin honesty)"


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
