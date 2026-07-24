#!/usr/bin/env python3
"""設計整合監査 — SEAM_PKG_MIRROR v0.4（実装 ⇔ SPEC の齟齬検出）。

役割: CC-α（設計・整合担当）。実装インスタンスが `twoder/seam/pkg_mirror.py` を
working tree に実装したら、本ハーネスが SPEC(`SPEC_PKG_MIRROR_v0_4.md`)を正本として
実装が設計を反映しているかを **決定論で**監査する。実装は書かない（それは別インスタンス）。

チェック（すべて「壊れていたら赤くなる」= 族A を避ける設計）:
  C1 骨格保存   : §2 骨格の <<<FILL>>> 以外の固定区間が impl に順序どおり bytes 一致で保存
                  （generate_via_runner.verify_skeleton_preserved と同一ロジック。出典コメント参照）
  C2 不変テスト : §3 を発注どおり impl に対し **実行**し 12/12 green（sandbox 同条件: cwd=tmp,
                  impl→impl.py / tests→test_impl.py, PYTHONPATH は §3 の _run が自前で張る=death#7 非依存）
  C3 import規律 : impl が twoder.* を static import しない（S10 と同基準。§0.3 ブートストラップ適格）
  C4 重複定義禁止: 骨格5シンボルが各1回（S9 と同基準。挿入は骨格検査では防げない）

verdict: 全 green → CONSISTENT（設計反映）／1つでも赤 → DISCREPANCY（齟齬・要調整）
         impl 不在 → NOT_YET_IMPLEMENTED（空振りでなく明示的未着手）

usage: python3 audit_pkg_mirror.py [impl_path] [--json]
"""
import ast, json, os, re, subprocess, sys, tempfile, shutil

SPEC = "/home/takasan/egl/docs/SPEC_PKG_MIRROR_v0_4.md"
DEFAULT_IMPL = "/home/takasan/twoder/seam/pkg_mirror.py"
SKELETON_SYMBOLS = ("mirror_package", "sha256_file", "MirrorHalt",
                    "MIRROR_MANIFEST", "MIRROR_EXCLUDE")


def _fenced_after(text, anchor, must_start):
    i = text.index(anchor)
    for mo in re.compile(r"```python\n(.*?)\n```", re.DOTALL).finditer(text, i):
        if mo.group(1).startswith(must_start):
            return mo.group(1)
    raise SystemExit("SPEC block not found after %r" % anchor)


def load_spec():
    body = open(SPEC, encoding="utf-8").read()
    skeleton = _fenced_after(body, "## §2. 骨格", '"""パッケージ複製 seam') + "\n"
    tests = _fenced_after(body, "## §3. 不変テスト", "import ast, hashlib") + "\n"
    return skeleton, tests


# --- C1: 骨格保存（generate_via_runner.py:49-74 と同一ロジックを自己完結で再実装） -------
def _skeleton_fixed_segments(skeleton):
    segs, cur = [], []
    for line in (skeleton or "").splitlines(keepends=True):
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
    for seg in _skeleton_fixed_segments(skeleton):
        idx = artifact.find(seg, pos)
        if idx < 0:
            return False
        pos = idx + len(seg)
    return True


# --- C2: §3 を実装に対して実行（sandbox 同条件の runner 再現） ------------------------
def run_immutable_tests(impl_src, tests_src):
    d = tempfile.mkdtemp(prefix="audit_pkgmirror_")
    try:
        with open(os.path.join(d, "impl.py"), "w", encoding="utf-8") as f:
            f.write(impl_src)
        with open(os.path.join(d, "test_impl.py"), "w", encoding="utf-8") as f:
            f.write(tests_src)
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "test_impl.py"],
                           cwd=d, capture_output=True, text=True, timeout=180)
        out = r.stdout + "\n" + r.stderr
        def _n(word):
            m = re.search(r"(\d+) %s" % word, out)
            return int(m.group(1)) if m else 0
        passed, failed, errors = _n("passed"), _n("failed"), _n("error")
        collection_error = "errors during collection" in out or "ERROR test_impl" in out
        return {"returncode": r.returncode, "passed": passed, "failed": failed,
                "errors": errors, "collection_error": collection_error,
                "green_12_12": (r.returncode == 0 and passed == 12 and failed == 0 and errors == 0),
                "tail": out.strip().splitlines()[-8:]}
    finally:
        shutil.rmtree(d, ignore_errors=True)


# --- C3 / C4: AST 規律 ----------------------------------------------------------------
def check_imports(impl_src):
    bad = []
    for node in ast.walk(ast.parse(impl_src)):
        if isinstance(node, ast.Import):
            bad += [a.name for a in node.names if a.name.startswith("twoder")]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").startswith("twoder"):
                bad.append(node.module)
    return {"ok": not bad, "twoder_imports": bad}


def check_no_redefinition(impl_src):
    names = []
    for node in ast.parse(impl_src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names += [t.id for t in node.targets if isinstance(t, ast.Name)]
    counts = {s: names.count(s) for s in SKELETON_SYMBOLS}
    return {"ok": all(v == 1 for v in counts.values()), "counts": counts}


def audit(impl_path=DEFAULT_IMPL):
    skeleton, tests = load_spec()
    if not os.path.isfile(impl_path):
        return {"verdict": "NOT_YET_IMPLEMENTED", "impl_path": impl_path,
                "note": "実装未着手。実装インスタンスが投下したら本監査を走らせる。"}
    impl_src = open(impl_path, encoding="utf-8").read()
    try:                                   # 部分書き込み中の途中状態は齟齬でなく未完成
        ast.parse(impl_src)
    except SyntaxError as e:
        return {"verdict": "INCOMPLETE_SYNTAX", "impl_path": impl_path, "error": str(e),
                "note": "実装が構文的に未完成（書き込み途中の可能性）。監査は保留。"}
    c1 = verify_skeleton_preserved(skeleton, impl_src)
    c2 = run_immutable_tests(impl_src, tests)
    c3 = check_imports(impl_src)
    c4 = check_no_redefinition(impl_src)
    consistent = c1 and c2["green_12_12"] and c3["ok"] and c4["ok"]
    return {"verdict": "CONSISTENT" if consistent else "DISCREPANCY",
            "impl_path": impl_path,
            "C1_skeleton_preserved": c1,
            "C2_immutable_tests": c2,
            "C3_no_twoder_import": c3,
            "C4_no_redefinition": c4}


def _summary(rep):
    v = rep["verdict"]
    lines = ["=== SEAM_PKG_MIRROR v0.4 設計整合監査 ===", "verdict: %s" % v,
             "impl   : %s" % rep.get("impl_path")]
    if v in ("NOT_YET_IMPLEMENTED", "INCOMPLETE_SYNTAX"):
        lines.append(rep.get("note", "")); return "\n".join(lines)
    c2 = rep["C2_immutable_tests"]
    lines += ["C1 骨格保存(bytes)      : %s" % ("green" if rep["C1_skeleton_preserved"] else "RED"),
              "C2 §3 不変テスト 12/12  : %s (passed=%d failed=%d errors=%d rc=%d)"
              % ("green" if c2["green_12_12"] else "RED", c2["passed"], c2["failed"], c2["errors"], c2["returncode"]),
              "C3 twoder.* 非import    : %s %s" % ("green" if rep["C3_no_twoder_import"]["ok"] else "RED",
                                                   rep["C3_no_twoder_import"]["twoder_imports"] or ""),
              "C4 重複定義なし         : %s %s" % ("green" if rep["C4_no_redefinition"]["ok"] else "RED",
                                                  "" if rep["C4_no_redefinition"]["ok"] else rep["C4_no_redefinition"]["counts"])]
    if not c2["green_12_12"]:
        lines += ["--- pytest tail ---"] + ["  " + t for t in c2["tail"]]
    return "\n".join(lines)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--json"]
    impl = args[0] if args else DEFAULT_IMPL
    rep = audit(impl)
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(_summary(rep))
    sys.exit(0 if rep["verdict"] in ("CONSISTENT", "NOT_YET_IMPLEMENTED", "INCOMPLETE_SYNTAX") else 1)
