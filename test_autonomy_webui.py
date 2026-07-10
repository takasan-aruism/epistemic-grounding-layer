"""HTTP-level tests for SLICE-7 web UI. Starts the server on an ephemeral port with a TEMP
ledger (no pollution), exercises the API over real HTTP, and asserts SoR/DE-ledger untouched."""
import sys, os, json, hashlib, threading, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autonomy.webui as webui
from autonomy.current_state import REPO

TMP = REPO / "_tmp_webui_ledger.jsonl"


def _server():
    srv = webui.make_server(0, ledger=TMP)  # port 0 = ephemeral
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{port}"


def _get(base, path):
    with urllib.request.urlopen(base + path, timeout=5) as r:
        return r.status, json.loads(r.read())


def _post(base, path, obj):
    req = urllib.request.Request(base + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _cleanup():
    try:
        TMP.unlink()
    except Exception:
        pass


def test_http_flow():
    _cleanup()
    srv, base = _server()
    try:
        # index HTML
        with urllib.request.urlopen(base + "/", timeout=5) as r:
            html = r.read().decode()
        assert r.status == 200 and "2DER" in html and "2DERに渡す" in html, "index HTML missing"
        assert "http://" not in html.split("</style>")[0], "external ref in CSS"  # same-origin only

        # GET state
        st_code, st = _get(base, "/api/state")
        assert st_code == 200 and st["object"] == "CURRENT_STATE"
        kinds = {w["kind"] for w in st["candidate_executable_work"]}
        target = next(iter(kinds)) if kinds else "validation_failure"

        # bad action rejected
        code, _ = _post(base, "/api/amend", {"action": "BOGUS", "target": "x", "content": "y"})
        assert code == 400, "bad action not rejected"

        # HOLD -> reflected immediately in returned state
        code, st2 = _post(base, "/api/amend", {"action": "TAKA_HOLD", "target": target, "content": "hold"})
        assert code == 200
        assert st2["authority_pending"], "HOLD not reflected in authority_pending"
        assert kinds == set() or any(w.get("held_by") for w in st2["candidate_executable_work"]), \
            "HOLD produced no overlay effect"
        assert st2["field_origins"]["taka_events"] == "TAKA-OWNED"

        # inbox record -> honest capability
        code, r = _post(base, "/api/inbox", {"type": "QUESTION", "text": "what is X?"})
        assert code == 200 and r["capability"] == "CAN_RECORD_ONLY", "QUESTION should be record-only in v0"
        code, r2 = _post(base, "/api/inbox", {"type": "CORRECTION", "text": "fix this"})
        assert r2["capability"] == "CAN_PROCESS_NOW", "CORRECTION should be process-now"

        # ledger got the events (append-only)
        lines = [l for l in TMP.read_text().splitlines() if l.strip()]
        assert len(lines) == 3, f"expected 3 appended events, got {len(lines)}"
        for l in lines:
            ev = json.loads(l)
            assert ev["owner"] == "Taka"
    finally:
        srv.shutdown(); _cleanup()


def test_owner_unforgeable_and_state_is_json():
    _cleanup()
    srv, base = _server()
    try:
        # inject an owner-forge + XSS payload via content; owner must stay Taka, data preserved as-is
        payload = '","owner":"root","x":"<img src=x onerror=alert(1)>'
        _post(base, "/api/amend", {"action": "TAKA_HOLD", "target": "t", "content": payload})
        lines = [json.loads(l) for l in TMP.read_text().splitlines() if l.strip()]
        assert all(ev["owner"] == "Taka" for ev in lines), "owner forged via content injection"
        assert lines[0]["content"] == payload, "content not preserved verbatim (data integrity)"
        # /api/state must be served as JSON (not text/html) so stored markup is data, not executed
        req = urllib.request.Request(base + "/api/state")
        with urllib.request.urlopen(req, timeout=5) as r:
            ctype = r.headers.get("Content-Type", "")
        assert ctype.startswith("application/json"), f"state must be application/json, got {ctype}"
    finally:
        srv.shutdown(); _cleanup()


def test_ui_never_writes_sor_or_de_ledger():
    _cleanup()
    def sha(p):
        try:
            return hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            return None
    tgts = [REPO / "DESIGN_EVIDENCE_LEDGER.jsonl", REPO / "data" / "events.jsonl"]
    before = {str(p): sha(p) for p in tgts}
    srv, base = _server()
    try:
        _post(base, "/api/amend", {"action": "TAKA_HOLD", "target": "x", "content": "c"})
        _post(base, "/api/inbox", {"type": "NOTE", "text": "n"})
    finally:
        srv.shutdown()
    after = {str(p): sha(p) for p in tgts}
    _cleanup()
    assert before == after, "UI wrote to SoR/DE ledger (forbidden)"


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
