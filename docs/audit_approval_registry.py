#!/usr/bin/env python3
"""設計整合監査 — TOKEN-GATE-01 / approval_registry.py（実装 ⇔ SPEC の齟齬検出）。

正本: SPEC_TOKEN_GATE_01.md。C1 骨格保存 / C2 §3 7本 pytest（authority 台帳を汚染しない
よう DS/EGL/DW/RRI を throwaway 隔離＋TMPDIR で disk 回避）/ C3 テスト verbatim / C4 spy 規律。
"""
import ast, json, os, re, subprocess, sys, tempfile

SPEC = "/home/takasan/egl/docs/SPEC_TOKEN_GATE_01.md"
IMPL = "/home/takasan/twoder/approval_registry.py"
TWODER = "/home/takasan/twoder"
TEST_REL = "tests/test_approval_registry.py"
ISOLATE = ("EGL_DATA_DIR", "DS_DATA_DIR", "DW_DATA_DIR", "RRI_DATA_DIR")


def _fenced_after(text, anchor, must_start):
    i = text.index(anchor)
    for mo in re.compile(r"```python\n(.*?)\n```", re.DOTALL).finditer(text, i):
        if mo.group(1).startswith(must_start):
            return mo.group(1)
    raise SystemExit("SPEC block not found after %r" % anchor)


def load_spec():
    b = open(SPEC, encoding="utf-8").read()
    sk = _fenced_after(b, "## §2", '"""TOKEN-GATE-01') + "\n"
    tests = _fenced_after(b, "## §3", "import importlib") + "\n"
    return sk, tests


def _fixed_segments(sk):
    segs, cur = [], []
    for line in sk.splitlines(keepends=True):
        if "<<<FILL" in line:
            if cur:
                segs.append("".join(cur)); cur = []
        else:
            cur.append(line)
    if cur:
        segs.append("".join(cur))
    return [s for s in segs if s]


def verify_skeleton_preserved(sk, art):
    if not isinstance(art, str):
        return False
    pos = 0
    for seg in _fixed_segments(sk):
        idx = art.find(seg, pos)
        if idx < 0:
            return False
        pos = idx + len(seg)
    return True


def run_tests():
    tmproot = "/home/takasan/.probe_audit_tmp"
    os.makedirs(tmproot, exist_ok=True)
    iso = tempfile.mkdtemp(prefix="tokengate_iso_", dir=tmproot)
    env = {**os.environ, "PYTHONSAFEPATH": "1", "PYTHONPATH": "/home/takasan", "TMPDIR": tmproot}
    for k in ISOLATE:                       # 実 DS/EGL 台帳を汚染しない throwaway
        d = os.path.join(iso, k.lower()); os.makedirs(d, exist_ok=True); env[k] = d
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", TEST_REL],
                       cwd=TWODER, env=env, capture_output=True, text=True, timeout=180)
    out = r.stdout + "\n" + r.stderr
    def _n(w):
        m = re.search(r"(\d+) %s" % w, out); return int(m.group(1)) if m else 0
    passed, failed, errors = _n("passed"), _n("failed"), _n("error")
    return {"returncode": r.returncode, "passed": passed, "failed": failed, "errors": errors,
            "all_green": (r.returncode == 0 and failed == 0 and errors == 0 and passed == 7),
            "tail": out.strip().splitlines()[-8:]}


def _verbatim(spec_src, path):
    if not os.path.isfile(path):
        return {"ok": False, "reason": "MISSING"}
    ok = open(path, encoding="utf-8").read().rstrip("\n") == spec_src.rstrip("\n")
    return {"ok": ok, "reason": "" if ok else "BYTES_DIFFER"}


def check_spy(impl_src):
    imps = []
    for n in ast.walk(ast.parse(impl_src)):
        if isinstance(n, ast.Import):
            imps += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            imps.append(n.module or "")
    bad = [m for m in imps if any(w in (m or "").lower() for w in ("spy", "fake", "mock"))]
    binds_auth = 'authority' in impl_src and '_AUTH' in impl_src
    return {"ok": not bad and binds_auth, "spy_imports": bad, "authority_bound": binds_auth}


def audit():
    sk, tests = load_spec()
    if not os.path.isfile(IMPL):
        return {"verdict": "NOT_YET_IMPLEMENTED", "impl": IMPL}
    src = open(IMPL, encoding="utf-8").read()
    try:
        ast.parse(src)
    except SyntaxError as e:
        return {"verdict": "INCOMPLETE_SYNTAX", "impl": IMPL, "error": str(e)}
    c1 = verify_skeleton_preserved(sk, src)
    c2 = run_tests()
    c3 = _verbatim(tests, os.path.join(TWODER, TEST_REL))
    c4 = check_spy(src)
    consistent = c1 and c2["all_green"] and c3["ok"] and c4["ok"]
    return {"verdict": "CONSISTENT" if consistent else "DISCREPANCY", "impl": IMPL,
            "C1_skeleton_preserved": c1, "C2_immutable_tests": c2,
            "C3_tests_verbatim": c3, "C4_spy_discipline": c4}


def _summary(r):
    v = r["verdict"]; L = ["=== TOKEN-GATE-01 / approval_registry 設計整合監査 ===", "verdict: %s" % v]
    if v in ("NOT_YET_IMPLEMENTED", "INCOMPLETE_SYNTAX"):
        return "\n".join(L + [r.get("error", "")])
    c2 = r["C2_immutable_tests"]
    L += ["C1 骨格保存      : %s" % ("green" if r["C1_skeleton_preserved"] else "RED"),
          "C2 §3 7/7 green  : %s (passed=%d failed=%d errors=%d rc=%d)"
          % ("green" if c2["all_green"] else "RED", c2["passed"], c2["failed"], c2["errors"], c2["returncode"]),
          "C3 テスト verbatim: %s %s" % ("green" if r["C3_tests_verbatim"]["ok"] else "RED", r["C3_tests_verbatim"]["reason"]),
          "C4 spy 規律      : %s %s" % ("green" if r["C4_spy_discipline"]["ok"] else "RED",
                                       "" if r["C4_spy_discipline"]["ok"] else r["C4_spy_discipline"])]
    if not c2["all_green"]:
        L += ["--- pytest tail ---"] + ["  " + t for t in c2["tail"]]
    return "\n".join(L)


if __name__ == "__main__":
    rep = audit()
    print(json.dumps(rep, ensure_ascii=False, indent=2) if "--json" in sys.argv else _summary(rep))
    sys.exit(0 if rep["verdict"] in ("CONSISTENT", "NOT_YET_IMPLEMENTED", "INCOMPLETE_SYNTAX") else 1)
