#!/usr/bin/env python3
"""設計整合監査 — CONFORMANCE_PROBE v0.4（実装 ⇔ SPEC の齟齬検出）。

役割: CC-α。実装インスタンスが `twoder/probe/conformance_probe.py`＋`tests/` を実装したら、
SPEC(`SPEC_CONFORMANCE_PROBE_v0_4.md`)を正本に設計反映を決定論監査する。実装は書かない。

チェック（すべて「壊れていたら赤」= 族A 回避）:
  C1 骨格保存   : §4 骨格の FILL 以外の固定区間が impl に順序どおり bytes 一致で保存
  C2 不変テスト : §5 を実配置で pytest 実行し全 green（実装 tests/ を PYTHONSAFEPATH で走らせる）
  C3 発注物 verbatim: §5 テスト・conftest が worker により改変されず bytes 一致（worker は書かない=規律）
  C4 spy 規律   : impl が spy/fake/mock を import せず、bind_real の SPY 検出ロジックを温存

usage: python3 audit_conformance_probe.py [--json]
"""
import ast, json, os, re, subprocess, sys

SPEC = "/home/takasan/egl/docs/SPEC_CONFORMANCE_PROBE_v0_4.md"
IMPL = "/home/takasan/twoder/probe/conformance_probe.py"
TWODER = "/home/takasan/twoder"
TEST_REL = "tests/test_conformance_probe.py"
CONFTEST_REL = "tests/conftest.py"


def _fenced_after(text, anchor, must_start):
    i = text.index(anchor)
    for mo in re.compile(r"```python\n(.*?)\n```", re.DOTALL).finditer(text, i):
        if mo.group(1).startswith(must_start):
            return mo.group(1)
    raise SystemExit("SPEC block not found after %r" % anchor)


def load_spec():
    b = open(SPEC, encoding="utf-8").read()
    sk = _fenced_after(b, "## §4. 骨格", '"""CONFORMANCE PROBE') + "\n"
    tests = _fenced_after(b, "## §5", "import json, os") + "\n"
    conftest = _fenced_after(b, "### conftest", '"""CONFORMANCE PROBE 発注側') + "\n"
    return sk, tests, conftest


def _fixed_segments(skeleton):
    segs, cur = [], []
    for line in skeleton.splitlines(keepends=True):
        if "<<<FILL" in line:
            if cur:
                segs.append("".join(cur)); cur = []
        else:
            cur.append(line)
    if cur:
        segs.append("".join(cur))
    return [s for s in segs if s]


def verify_skeleton_preserved(skeleton, artifact):
    if not isinstance(artifact, str):
        return False
    pos = 0
    for seg in _fixed_segments(skeleton):
        idx = artifact.find(seg, pos)
        if idx < 0:
            return False
        pos = idx + len(seg)
    return True


def run_tests():
    env = {**os.environ, "PYTHONSAFEPATH": "1", "PYTHONPATH": "/home/takasan"}
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", TEST_REL],
                       cwd=TWODER, env=env, capture_output=True, text=True, timeout=300)
    out = r.stdout + "\n" + r.stderr
    def _n(w):
        m = re.search(r"(\d+) %s" % w, out)
        return int(m.group(1)) if m else 0
    passed, failed, errors = _n("passed"), _n("failed"), _n("error")
    return {"returncode": r.returncode, "passed": passed, "failed": failed, "errors": errors,
            "collection_error": "errors during collection" in out,
            "all_green": (r.returncode == 0 and failed == 0 and errors == 0 and passed >= 10),
            "tail": out.strip().splitlines()[-8:]}


def _verbatim(spec_src, path):
    if not os.path.isfile(path):
        return {"ok": False, "reason": "MISSING:%s" % path}
    got = open(path, encoding="utf-8").read()
    ok = got.rstrip("\n") == spec_src.rstrip("\n")
    return {"ok": ok, "reason": "" if ok else "BYTES_DIFFER"}


def check_spy(impl_src):
    imports = []
    for node in ast.walk(ast.parse(impl_src)):
        if isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    bad = [m for m in imports if any(w in (m or "").lower() for w in ("spy", "fake", "mock"))]
    spy_guard = 'SPY_BOUND_WHERE_REAL_REQUIRED' in impl_src   # bind_real のガード温存
    return {"ok": not bad and spy_guard, "spy_imports": bad, "spy_guard_present": spy_guard}


def _observations(impl_src):
    obs = []
    m = re.search(r'PROBE_SPEC\s*=\s*"([^"]+)"', impl_src)
    if m and m.group(1) != "SPEC_CONFORMANCE_PROBE_v0_4":
        obs.append("PROBE_SPEC=%s（骨格由来。起草側の版未更新＝CC-α のミス。実装は忠実保存）" % m.group(1))
    return obs


def audit():
    sk, tests, conftest = load_spec()
    if not os.path.isfile(IMPL):
        return {"verdict": "NOT_YET_IMPLEMENTED", "impl": IMPL}
    impl_src = open(IMPL, encoding="utf-8").read()
    try:
        ast.parse(impl_src)
    except SyntaxError as e:
        return {"verdict": "INCOMPLETE_SYNTAX", "impl": IMPL, "error": str(e)}
    c1 = verify_skeleton_preserved(sk, impl_src)
    c2 = run_tests()
    c3a = _verbatim(tests, os.path.join(TWODER, TEST_REL))
    c3b = _verbatim(conftest, os.path.join(TWODER, CONFTEST_REL))
    c4 = check_spy(impl_src)
    consistent = c1 and c2["all_green"] and c3a["ok"] and c3b["ok"] and c4["ok"]
    return {"verdict": "CONSISTENT" if consistent else "DISCREPANCY", "impl": IMPL,
            "C1_skeleton_preserved": c1, "C2_immutable_tests": c2,
            "C3a_tests_verbatim": c3a, "C3b_conftest_verbatim": c3b,
            "C4_spy_discipline": c4, "observations": _observations(impl_src)}


def _summary(r):
    v = r["verdict"]
    L = ["=== CONFORMANCE_PROBE v0.4 設計整合監査 ===", "verdict: %s" % v, "impl: %s" % r.get("impl")]
    if v in ("NOT_YET_IMPLEMENTED", "INCOMPLETE_SYNTAX"):
        return "\n".join(L + [r.get("error", "")])
    c2 = r["C2_immutable_tests"]
    L += ["C1 骨格保存(bytes)     : %s" % ("green" if r["C1_skeleton_preserved"] else "RED"),
          "C2 §5 不変テスト green : %s (passed=%d failed=%d errors=%d rc=%d)"
          % ("green" if c2["all_green"] else "RED", c2["passed"], c2["failed"], c2["errors"], c2["returncode"]),
          "C3a テスト verbatim    : %s %s" % ("green" if r["C3a_tests_verbatim"]["ok"] else "RED", r["C3a_tests_verbatim"]["reason"]),
          "C3b conftest verbatim  : %s %s" % ("green" if r["C3b_conftest_verbatim"]["ok"] else "RED", r["C3b_conftest_verbatim"]["reason"]),
          "C4 spy 規律           : %s %s" % ("green" if r["C4_spy_discipline"]["ok"] else "RED",
                                            "" if r["C4_spy_discipline"]["ok"] else r["C4_spy_discipline"])]
    if not c2["all_green"]:
        L += ["--- pytest tail ---"] + ["  " + t for t in c2["tail"]]
    if r.get("observations"):
        L += ["観測外:"] + ["  - " + o for o in r["observations"]]
    return "\n".join(L)


if __name__ == "__main__":
    rep = audit()
    print(json.dumps(rep, ensure_ascii=False, indent=2) if "--json" in sys.argv else _summary(rep))
    sys.exit(0 if rep["verdict"] in ("CONSISTENT", "NOT_YET_IMPLEMENTED", "INCOMPLETE_SYNTAX") else 1)
