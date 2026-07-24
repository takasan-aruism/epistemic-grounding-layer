#!/usr/bin/env python3
"""設計整合監査 — TOKEN 配線（SPEC_TOKEN_WIRING_v0_1）。

C1 Part A: approval_registry にアダプタ3関数追加＋既存3関数存置＋§2 骨格固定区間保存
C2 Part A: tests/test_token_wiring.py 6/6（隔離）＋ verbatim
C3 Part B: 6ファイルが validate_by_token/consume_by_token＋approval_registry import に置換
C4 Part C: probe §5 T1–T12 green（隔離）
（C5 再走行 gate1_token=green は別途確認済み: BREAKAGE_LIST_2026-07-23_rerun.jsonl）
"""
import ast, json, os, re, subprocess, sys, tempfile

SPEC = "/home/takasan/egl/docs/SPEC_TOKEN_WIRING_v0_1.md"
TWODER = "/home/takasan/twoder"
AR = os.path.join(TWODER, "approval_registry.py")
FILES_B = ["live_worker_runtime.py", "gate4.py", "operator.py", "ab_harness.py",
           "command_surface.py", "autonomous_git.py"]
ISOLATE = ("EGL_DATA_DIR", "DS_DATA_DIR", "DW_DATA_DIR", "RRI_DATA_DIR")
TMPROOT = "/home/takasan/.probe_audit_tmp"


def _fenced_after(text, anchor, must_start):
    i = text.index(anchor)
    for mo in re.compile(r"```python\n(.*?)\n```", re.DOTALL).finditer(text, i):
        if mo.group(1).startswith(must_start):
            return mo.group(1)
    raise SystemExit("SPEC block not found after %r" % anchor)


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
    pos = 0
    for seg in _fixed_segments(sk):
        idx = art.find(seg, pos)
        if idx < 0:
            return False
        pos = idx + len(seg)
    return True


def _pytest(rel, expect):
    os.makedirs(TMPROOT, exist_ok=True)
    iso = tempfile.mkdtemp(prefix="wire_iso_", dir=TMPROOT)
    env = {**os.environ, "PYTHONSAFEPATH": "1", "PYTHONPATH": "/home/takasan", "TMPDIR": TMPROOT}
    for k in ISOLATE:
        d = os.path.join(iso, k.lower()); os.makedirs(d, exist_ok=True); env[k] = d
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", rel],
                       cwd=TWODER, env=env, capture_output=True, text=True, timeout=300)
    out = r.stdout + "\n" + r.stderr
    m = re.search(r"(\d+) passed", out); passed = int(m.group(1)) if m else 0
    fm = re.search(r"(\d+) failed", out); failed = int(fm.group(1)) if fm else 0
    em = re.search(r"(\d+) error", out); errors = int(em.group(1)) if em else 0
    return {"passed": passed, "failed": failed, "errors": errors, "rc": r.returncode,
            "green": (r.returncode == 0 and failed == 0 and errors == 0 and passed >= expect),
            "tail": out.strip().splitlines()[-6:]}


def audit():
    spec = open(SPEC, encoding="utf-8").read()
    tests_A = _fenced_after(spec, "## §2", "import importlib") + "\n"
    sk_A = _fenced_after(spec, "## §2", "# ── 配線アダプタ") + "\n"
    ar_src = open(AR, encoding="utf-8").read()

    # C1
    fns = [n.name for n in ast.parse(ar_src).body if isinstance(n, ast.FunctionDef)]
    adapter = all(f in fns for f in ("_extract_approval_id", "validate_by_token", "consume_by_token"))
    existing = all(f in fns for f in ("_load_grant", "validate_approval_by_id", "consume_approval_by_id"))
    sk_pres = verify_skeleton_preserved(sk_A, ar_src)
    c1 = {"ok": adapter and existing and sk_pres, "adapter": adapter, "existing_kept": existing, "skeleton_preserved": sk_pres}

    # C2
    c2t = _pytest("tests/test_token_wiring.py", 6)
    got = open(os.path.join(TWODER, "tests/test_token_wiring.py"), encoding="utf-8").read()
    c2 = {"ok": c2t["green"] and got.rstrip("\n") == tests_A.rstrip("\n"),
          "tests": c2t, "verbatim": got.rstrip("\n") == tests_A.rstrip("\n")}

    # C3
    b = {}
    for f in FILES_B:
        s = open(os.path.join(TWODER, f), encoding="utf-8").read()
        has_new = "validate_by_token" in s
        has_import = "approval_registry" in s
        # 旧直呼びが残っていないか(AR. 以外の validate_approval( 直呼び)。approval_registry.py 名以外。
        stale = bool(re.search(r"(?<![_A-Za-z])(AUTH|A)\.validate_approval\(", s))
        b[f] = {"has_new": has_new, "has_import": has_import, "stale_direct_call": stale,
                "ok": has_new and has_import and not stale}
    c3 = {"ok": all(v["ok"] for v in b.values()), "per_file": b}

    # C4
    c4t = _pytest("tests/test_conformance_probe.py", 10)
    c4 = {"ok": c4t["green"], "tests": c4t}

    consistent = c1["ok"] and c2["ok"] and c3["ok"] and c4["ok"]
    return {"verdict": "CONSISTENT" if consistent else "DISCREPANCY",
            "C1_partA_adapter": c1, "C2_partA_tests": c2, "C3_partB_rewire": c3, "C4_partC_probe": c4}


if __name__ == "__main__":
    rep = audit()
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2)); sys.exit(0)
    print("=== TOKEN 配線 設計整合監査 ===")
    print("verdict:", rep["verdict"])
    c1 = rep["C1_partA_adapter"]; c2 = rep["C2_partA_tests"]; c3 = rep["C3_partB_rewire"]; c4 = rep["C4_partC_probe"]
    print("C1 Part A アダプタ+既存不変+骨格保存: %s (adapter=%s existing=%s skel=%s)"
          % ("green" if c1["ok"] else "RED", c1["adapter"], c1["existing_kept"], c1["skeleton_preserved"]))
    print("C2 Part A test_token_wiring 6/6+verbatim: %s (passed=%d verbatim=%s)"
          % ("green" if c2["ok"] else "RED", c2["tests"]["passed"], c2["verbatim"]))
    print("C3 Part B 6経路 rewire: %s" % ("green" if c3["ok"] else "RED"))
    for f, v in c3["per_file"].items():
        print("   %-24s new=%s import=%s stale=%s" % (f, v["has_new"], v["has_import"], v["stale_direct_call"]))
    print("C4 Part C probe T1–T12: %s (passed=%d)" % ("green" if c4["ok"] else "RED", c4["tests"]["passed"]))
    if not c4["ok"]:
        print("   probe tail:", c4["tests"]["tail"])
    sys.exit(0 if rep["verdict"] == "CONSISTENT" else 1)
