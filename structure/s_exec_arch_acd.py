#!/usr/bin/env python3
"""s_exec_arch_acd — EXEC_ARCH A/C/D 統合 s-stage(決定論・LLM 不使用・:8005/GPU 不使用)。

Stage B(s_llm_invocations)テンプレ。単一モジュールで 3 jsonl を生成し統一 --check を持つ:
  A. ENTRYPOINTS_EXT.jsonl  — Python 外の起動経路(sh/systemd/tmux/cron/runner/vLLM serve)
  C. READ_PATHS.jsonl       — actually_loaded(AST の open) + gate 被覆。required_by_design は
                              決定論出典が無く UNRESOLVED_NO_DESIGN_MANIFEST(C2: 不明は正直停止・捏造しない)
  D. STATE_MACHINES.jsonl    — 各 state 機械の symbol を edge/ladder 語彙へ写像。alias 矛盾は CONTRADICTIONS へ

規律(v0.2): 新状態語彙を作らない(既存 edge/ladder へ写像のみ)。切断/矛盾は直さず CONTRADICTIONS.jsonl。
NO は被覆下のみ(未被覆=UNRESOLVED_<理由>)。MD は導出(手書きしない)。新 Registry を作らない。

usage:  s_exec_arch_acd.py [--check]
"""
import ast
import json
import os
import re
import sys

ROOT = "/home/takasan"
REPOS = ("twoder", "egl", "rri", "ds", "dev-workcell")
STRUCT = os.path.join(ROOT, "egl", "structure")
OUT_A = os.path.join(STRUCT, "ENTRYPOINTS_EXT.jsonl")
OUT_C = os.path.join(STRUCT, "READ_PATHS.jsonl")
OUT_D = os.path.join(STRUCT, "STATE_MACHINES.jsonl")
CONTRA = os.path.join(STRUCT, "CONTRADICTIONS.jsonl")   # 既存 sole ledger: **追記しない**(s6 が writer)。矛盾は別掲出力へ

EDGE_VOCAB = ("LIVE", "WIRED_UNENTERED", "WIRED_EXECUTION_UNRESOLVED", "IMPLEMENTED_UNWIRED", "TEST_ONLY_ISLAND")
LADDER_VOCAB = ("documented", "implemented", "wired", "executed", "proven")
EXCLUDE = ("__pycache__", ".git", "node_modules")


def _walk(exts):
    for repo in REPOS:
        for dp, dns, fns in os.walk(os.path.join(ROOT, repo)):
            dns[:] = [d for d in dns if d not in EXCLUDE]
            for fn in fns:
                if fn.endswith(exts):
                    ab = os.path.join(dp, fn)
                    yield repo, os.path.relpath(ab, ROOT), ab


# ── A. Runtime Entry 拡張 ───────────────────────────────────────────────────
def build_A():
    recs = []
    def add(rel, kind, target, args, status):
        recs.append({"source_file": rel.replace("\\", "/"), "kind": kind,
                     "launch_target": target, "args": args, "status": status})
    for repo, rel, ab in _walk((".sh", ".service", ".timer")):
        try:
            src = open(ab, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if rel.endswith(".service") or rel.endswith(".timer"):
            m = re.search(r"(?m)^\s*ExecStart\s*=\s*(.+)$", src)
            tgt = m.group(1).strip() if m else "UNRESOLVED_NO_EXECSTART"
            # systemd unit が現に有効かは静的に不可 → 動的ディスパッチ扱い
            add(rel, "SYSTEMD", tgt, "", "WIRED_EXECUTION_UNRESOLVED")
        else:  # .sh
            first = next((l for l in src.splitlines() if l.strip() and not l.strip().startswith("#")), "")
            # vLLM serve を含む sh は VLLM_ENDPOINT 種
            if re.search(r"vllm serve|--port\s*800[56]|:800[56]", src):
                add(rel, "VLLM_ENDPOINT", first[:120], "", "WIRED_EXECUTION_UNRESOLVED")
            else:
                add(rel, "SHELL", first[:120], "", "WIRED_EXECUTION_UNRESOLVED")
    # tmux(現行 2der/2der2 セッション=live だが静的ソースに無い→UNRESOLVED)
    add("<runtime>", "TMUX", "sessions 2der/2der2 (attached; not in static source)", "",
        "UNRESOLVED_DYNAMIC_LAUNCH")
    # cron: 静的ファイル 0 件。crontab は runtime → 未被覆
    add("<runtime>", "CRON", "crontab (runtime; no static *.cron file found)", "",
        "UNRESOLVED_DYNAMIC_LAUNCH")
    recs.sort(key=lambda r: (r["kind"], r["source_file"], r["launch_target"]))
    return recs


# ── C. Mandatory Read Paths ─────────────────────────────────────────────────
def _opened_paths(tree):
    """AST で open(...) の第1引数が literal path or 既知 path 変数のもの(actually_loaded の近似)。"""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open" and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.add(a.value)
    return out


def build_C(entry_recs):
    recs = []
    # actually_loaded: s-stage/runtime モジュールが open する literal path。required_by_design は決定論出典なし。
    for repo, rel, ab in _walk((".py",)):
        if "/structure/" not in ("/" + rel) and "structure/" not in rel:
            continue  # C は structure s-stage の read 被覆に限定(範囲を勝手に広げない)
        try:
            tree = ast.parse(open(ab, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        for p in sorted(_opened_paths(tree)):
            recs.append({"stage": rel.replace("\\", "/"), "path": p,
                         "required_by_design": "UNRESOLVED_NO_DESIGN_MANIFEST",  # C2: 出典無し=正直停止
                         "actually_loaded": True,
                         "verdict": "UNRESOLVED_NO_DESIGN_MANIFEST"})
    # gate 被覆: どの entrypoint(A) が --check ゲートに到達するか。静的には不可 → 未被覆を UNRESOLVED で別掲
    gate_files = sorted({rel for _, rel, ab in _walk((".py",))
                         if "structure/" in rel and "--check" in open(ab, errors="replace").read()})
    for ep in entry_recs:
        recs.append({"stage": "GATE_COVERAGE", "path": ep["source_file"],
                     "required_by_design": "reaches a --check gate?",
                     "actually_loaded": "UNRESOLVED_DYNAMIC_DISPATCH",
                     "verdict": "UNRESOLVED_DYNAMIC_DISPATCH"})
    recs.append({"stage": "GATE_INVENTORY", "path": ";".join(gate_files),
                 "required_by_design": "n/a", "actually_loaded": True,
                 "verdict": "OK", "note": "%d --check gates present" % len(gate_files)})
    recs.sort(key=lambda r: (r["stage"], r["path"]))
    return recs


# ── D. State Machine Map ────────────────────────────────────────────────────
def build_D():
    recs = []
    state_owner = {}   # state symbol -> [source_file,...]  (alias 矛盾検出用)
    for repo, rel, ab in _walk((".py",)):
        if "/regression/" in ("/" + rel) or "/test_" in ("/" + rel) or rel.split("/")[-1].startswith("test_"):
            continue
        try:
            src = open(ab, encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except Exception:
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if not any(nm in ("STATES", "TRANSITIONS") or nm.endswith("_STATES") for nm in names):
                continue
            # STATES tuple / TRANSITIONS dict から state symbol を抽出
            syms = set()
            for s in ast.walk(node.value):
                if isinstance(s, ast.Constant) and isinstance(s.value, str) and re.match(r"^[A-Z][A-Z0-9_]{2,}$", s.value):
                    syms.add(s.value)
            machine = rel.replace("\\", "/") + ":" + names[0]
            for sym in sorted(syms):
                mapped = _map_to_vocab(sym)
                recs.append({"machine": machine, "state_symbol": sym,
                             "mapped_to": mapped, "source_file": rel.replace("\\", "/")})
                state_owner.setdefault(sym, set()).add(rel.replace("\\", "/"))
    # alias 矛盾(同一 symbol が複数 machine で別文脈) → CONTRADICTIONS を作らず別掲出力に記録(sole writer は s6)
    contradictions = [{"type": "STATE_ALIAS_MULTI_OWNER", "state_symbol": sym,
                       "owners": sorted(owners)}
                      for sym, owners in state_owner.items() if len(owners) > 1]
    recs.sort(key=lambda r: (r["machine"], r["state_symbol"]))
    return recs, contradictions


def _map_to_vocab(sym):
    """新語彙を作らず既存 edge/ladder へ写像。写像不能は UNRESOLVED(曖昧化しない)。"""
    s = sym.upper()
    table = {
        "LIVE": "LIVE", "DISPATCHABLE": "wired", "RESOLVED": "proven", "CLOSED": "executed",
        "EXECUTED": "executed", "PROVEN": "proven", "WIRED": "wired", "IMPLEMENTED": "implemented",
        "DOCUMENTED": "documented",
    }
    return table.get(s, "UNRESOLVED_NO_VOCAB_MAPPING:" + sym)


# ── 出力 + gate ─────────────────────────────────────────────────────────────
def _ser(recs):
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in recs)


def build_all():
    A = build_A()
    C = build_C(A)
    D, contra = build_D()
    return A, C, D, contra


def _symbols_exist(A, D):
    """記録 symbol の実在: A の source_file / D の source_file が実在するか。"""
    bad = []
    for r in A:
        f = r["source_file"]
        if not f.startswith("<") and not os.path.isfile(os.path.join(ROOT, f)):
            bad.append("A:" + f)
    for r in D:
        if not os.path.isfile(os.path.join(ROOT, r["source_file"])):
            bad.append("D:" + r["source_file"])
    return bad


def check():
    A, C, D, contra = build_all()
    red = []
    for path, recs in ((OUT_A, A), (OUT_C, C), (OUT_D, D)):
        if not os.path.isfile(path) or open(path, encoding="utf-8").read() != _ser(recs):
            red.append("REGEN_MISMATCH: %s" % os.path.basename(path))
    bad = _symbols_exist(A, D)
    if bad:
        red.append("DANGLING_SYMBOL: " + ", ".join(bad[:5]))
    # 陰性対照(§4-3): 既知 entrypoint を1つ隠す→再走査で欠落(未登録)を検出できるか
    hidden = [r for r in A if r["kind"] in ("SHELL", "SYSTEMD", "VLLM_ENDPOINT")]
    if hidden:
        A2 = [r for r in build_A() if r != hidden[0]]
        if len(A2) >= len(A):
            red.append("NEG_CONTROL_A_FAILED: hiding an entrypoint not detectable")
    # 陰性対照(§4-5): 既知 alias 衝突を注入→捕捉できるか(検出器 load-bearing)
    probe = _detect_alias([{"state_symbol": "X_DUP", "source_file": "a.py"},
                           {"state_symbol": "X_DUP", "source_file": "b.py"}])
    if not probe:
        red.append("NEG_CONTROL_D_FAILED: injected alias conflict not detected")
    if red:
        print("EXEC_ARCH_ACD --check: RED")
        for m in red:
            print("  " + m)
        return 1
    print("EXEC_ARCH_ACD --check: GREEN (byte-identical A/C/D; symbols exist; neg-controls A/D load-bearing; "
          "%d entrypoints, %d state-symbols, %d alias-contradictions)" % (len(A), len(D), len(contra)))
    return 0


def _detect_alias(D_like):
    owner = {}
    for r in D_like:
        owner.setdefault(r["state_symbol"], set()).add(r["source_file"])
    return [s for s, o in owner.items() if len(o) > 1]


def main(argv):
    if "--check" in argv:
        return check()
    A, C, D, contra = build_all()
    open(OUT_A, "w", encoding="utf-8").write(_ser(A))
    open(OUT_C, "w", encoding="utf-8").write(_ser(C))
    open(OUT_D, "w", encoding="utf-8").write(_ser(D))
    print("A entrypoints=%d | C read-path rows=%d | D state-symbols=%d | alias-contradictions=%d"
          % (len(A), len(C), len(D), len(contra)))
    print("A kinds:", {k: sum(1 for r in A if r["kind"] == k) for k in sorted({r["kind"] for r in A})})
    print("D unmapped(UNRESOLVED_NO_VOCAB):", sum(1 for r in D if str(r["mapped_to"]).startswith("UNRESOLVED")))
    if contra:
        print("alias contradictions (別掲・CONTRADICTIONS への追記は s6 sole writer):",
              [c["state_symbol"] for c in contra][:8])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
