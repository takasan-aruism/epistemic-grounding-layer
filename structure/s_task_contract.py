#!/usr/bin/env python3
"""s_task_contract — Task Contract(EXEC_ARCH の一段抽象化 / DE-0525)。決定論・LLM 不使用。

A/C/D の C/D が解けなかった根因=「比較対象(正典)が未定義」。各タスクに契約を持たせ、C/D を契約から再導出する。
役割分担: 実装=機械＋**決定論で出せる契約項目の候補**(expected_outputs/allowed_writes/actually_loaded)。
判断項目(required_inputs の"読むべき" / 状態の canonical 意味)は**設計が後で authored**。空から慎重に育てる。

生成:
  TASK_CONTRACTS.jsonl   — 1 タスク 1 行。required_inputs は authored 前は UNRESOLVED_NO_CONTRACT
  CANONICAL_STATES.jsonl — 正規化辞書(authored)。空で始めてよい。auto-collapse 禁止(同綴り別意を消さない)
  READ_PATHS.jsonl(C)    — 契約駆動: required_inputs vs actually_loaded → MISSING/OK/UNRESOLVED_NO_CONTRACT
  STATE_MACHINES.jsonl(D)— 正規化駆動: 状態→canonical→cross-machine 衝突。未写像=UNRESOLVED_NO_CANONICAL

usage:  s_task_contract.py [--check]
"""
import ast
import json
import os
import sys

import s_exec_arch_acd as ACD   # A/D の走査機構を流用(同一 grounding)

ROOT = ACD.ROOT
STRUCT = ACD.STRUCT
OUT_CONTRACTS = os.path.join(STRUCT, "TASK_CONTRACTS.jsonl")
OUT_CANON = os.path.join(STRUCT, "CANONICAL_STATES.jsonl")
OUT_C = os.path.join(STRUCT, "READ_PATHS.jsonl")
OUT_D = os.path.join(STRUCT, "STATE_MACHINES.jsonl")

# タスク = structure の s-stage 群(決定論ツール)。契約の種はここから機械生成。
def _stage_modules():
    import re as _re
    out = []
    for fn in sorted(os.listdir(STRUCT)):
        if _re.match(r"s\d*_.*\.py$", fn) and fn != "s_task_contract.py":
            out.append(fn)
    return out


def _join_literal(node):
    """os.path.join(..., "literal") の末尾 str literal を返す(basename 相当)。"""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join" \
            and node.args and isinstance(node.args[-1], ast.Constant) and isinstance(node.args[-1].value, str):
        return node.args[-1].value
    return None


def _path_of(node, const):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return const.get(node.id)
    return _join_literal(node)


def _writes_and_reads(path):
    """AST: open(path,"w"/"a")=write / open(path[,"r"])=read。literal・OUT定数・os.path.join を解決(決定論候補)。"""
    src = open(path, encoding="utf-8", errors="replace").read()
    tree = ast.parse(src)
    const = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            v = None
            if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                v = n.value.value
            else:
                v = _join_literal(n.value)
            if v is not None:
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        const[t.id] = v
    writes, reads = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "open" and n.args:
            p = _path_of(n.args[0], const)
            mode = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else "r"
            if p and p.endswith((".jsonl", ".json", ".npy", ".txt", ".md")):
                (writes if ("w" in str(mode) or "a" in str(mode)) else reads).add(os.path.basename(p))
    return sorted(writes), sorted(reads)


def _sole_writer_of(fname):
    """既存 sole-writer 規律: CONTRADICTIONS=s6。それ以外の s-stage 出力は自己(direct open)。"""
    if fname == "CONTRADICTIONS.jsonl":
        return "s6_contradictions.py"
    return "self(open w)"


def build_contracts():
    recs = []
    for fn in _stage_modules():
        if fn in ("s_task_contract.py",):
            continue
        writes, reads = _writes_and_reads(os.path.join(STRUCT, fn))
        recs.append({
            "task_id": fn[:-3],
            "required_inputs": "UNRESOLVED_NO_CONTRACT",   # 判断=設計が authored(捏造しない)
            "expected_outputs": writes,                     # 決定論候補
            "allowed_writes": [{"path": w, "via": _sole_writer_of(w)} for w in writes],
            "actually_loaded": reads,                       # 決定論実測
            "normalization": "CANONICAL_STATES",
        })
    recs.sort(key=lambda r: r["task_id"])
    return recs


def load_canonical():
    """authored 辞書。空で始めてよい。auto-collapse しない(同綴り別 canonical 可)。"""
    if not os.path.isfile(OUT_CANON):
        return []
    return [json.loads(l) for l in open(OUT_CANON, encoding="utf-8") if l.strip() and not l.startswith("#")]


def _canon_map(canon):
    """raw_symbol -> [canonical,...](同綴り別意=複数 canonical を保持)。"""
    m = {}
    for r in canon:
        m.setdefault(r["raw_symbol"], []).append(r["canonical"])
    return m


# ── C 再導出(契約駆動) ──────────────────────────────────────────────────────
def build_C(contracts):
    recs = []
    for c in contracts:
        req = c["required_inputs"]
        loaded = set(c["actually_loaded"])
        if req == "UNRESOLVED_NO_CONTRACT":
            recs.append({"stage": c["task_id"], "path": "*", "required_by_contract": "UNRESOLVED_NO_CONTRACT",
                         "actually_loaded": sorted(loaded), "verdict": "UNRESOLVED_NO_CONTRACT"})
            continue
        for p in req:
            recs.append({"stage": c["task_id"], "path": p, "required_by_contract": True,
                         "actually_loaded": (os.path.basename(p) in loaded) or (p in loaded),
                         "verdict": "OK" if ((os.path.basename(p) in loaded) or (p in loaded)) else "MISSING"})
    recs.sort(key=lambda r: (r["stage"], str(r["path"])))
    return recs


# ── D 再導出(正規化駆動) ────────────────────────────────────────────────────
def build_D(canon):
    D_raw, _ = ACD.build_D()   # {machine, state_symbol, source_file}(生)
    cmap = _canon_map(canon)
    recs = []
    canon_owner = {}   # canonical -> set(machine)  衝突検出用(auto-collapse でない=辞書経由のみ)
    for r in D_raw:
        cs = cmap.get(r["state_symbol"])
        canonical = cs[0] if (cs and len(cs) == 1) else \
            ("UNRESOLVED_NO_CANONICAL" if not cs else "AMBIGUOUS_MULTI_CANONICAL")
        recs.append({"machine": r["machine"], "state_symbol": r["state_symbol"],
                     "canonical": canonical, "source_file": r["source_file"]})
        if cs and len(cs) == 1:
            canon_owner.setdefault(canonical, set()).add(r["source_file"])
    conflicts = [{"type": "CROSS_MACHINE_STATE_CONFLICT", "canonical": c, "owners": sorted(o)}
                 for c, o in canon_owner.items() if len(o) > 1]
    recs.sort(key=lambda r: (r["machine"], r["state_symbol"]))
    return recs, conflicts


def build_all():
    contracts = build_contracts()
    canon = load_canonical()
    C = build_C(contracts)
    D, conflicts = build_D(canon)
    return contracts, canon, C, D, conflicts


def _ser(recs):
    return "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in recs)


# ── ゲート ──────────────────────────────────────────────────────────────────
def _schema_ok(contracts):
    bad = []
    for c in contracts:
        for k in ("task_id", "required_inputs", "expected_outputs", "allowed_writes", "normalization"):
            if k not in c:
                bad.append("%s missing %s" % (c.get("task_id"), k))
        for w in c["allowed_writes"]:
            if w["via"] == "s6_contradictions.py" and not os.path.isfile(os.path.join(STRUCT, "s6_contradictions.py")):
                bad.append("%s via s6 not real" % c["task_id"])
    return bad


def check():
    contracts, canon, C, D, conflicts = build_all()
    red = []
    for path, recs in ((OUT_CONTRACTS, contracts), (OUT_C, C), (OUT_D, D)):
        if not os.path.isfile(path) or open(path, encoding="utf-8").read() != _ser(recs):
            red.append("REGEN_MISMATCH: %s" % os.path.basename(path))
    red += _schema_ok(contracts)
    # §3-3 auto-collapse 禁止(陰性対照): 同綴り別 canonical を注入 → 機械が同一へ寄せない
    probe = _canon_map([{"raw_symbol": "DUP", "canonical": "A"}, {"raw_symbol": "DUP", "canonical": "B"}])
    if probe.get("DUP") != ["A", "B"]:
        red.append("AUTO_COLLAPSE_VIOLATION: same-spelling collapsed (should keep distinct canonicals)")
    # §3-4 C 検出力: required_inputs に未読資料 → MISSING
    tc = build_C([{"task_id": "probe", "required_inputs": ["nonexistent_input.jsonl"], "actually_loaded": []}])
    if not any(r["verdict"] == "MISSING" for r in tc):
        red.append("C_DETECTION_FAILED: unread required input not flagged MISSING")
    # §3-5 D 検出力: CREATED を両 machine で同 canonical へ写像 → 衝突再検出
    _, conf = build_D([{"raw_symbol": "CREATED", "canonical": "STATE_CREATED", "authored_by": "probe"}])
    if not any(c["canonical"] == "STATE_CREATED" for c in conf):
        red.append("D_DETECTION_FAILED: known CREATED cross-machine conflict not re-detected via canonical")
    if red:
        print("TASK_CONTRACT --check: RED")
        for m in red:
            print("  " + m)
        return 1
    n_unres_c = sum(1 for r in C if str(r["verdict"]).startswith("UNRESOLVED"))
    n_unres_d = sum(1 for r in D if str(r["canonical"]).startswith("UNRESOLVED"))
    print("TASK_CONTRACT --check: GREEN (byte-identical; schema ok; neg-controls auto-collapse/C/D load-bearing; "
          "%d contracts, C UNRESOLVED_NO_CONTRACT=%d, D UNRESOLVED_NO_CANONICAL=%d, live conflicts=%d)"
          % (len(contracts), n_unres_c, n_unres_d, len(conflicts)))
    return 0


def main(argv):
    if "--check" in argv:
        return check()
    contracts, canon, C, D, conflicts = build_all()
    open(OUT_CONTRACTS, "w", encoding="utf-8").write(_ser(contracts))
    if not os.path.isfile(OUT_CANON):
        open(OUT_CANON, "w", encoding="utf-8").write(
            "# CANONICAL_STATES(authored)。空で始める。auto-collapse 禁止=同綴り別意は別 canonical。\n")
    open(OUT_C, "w", encoding="utf-8").write(_ser(C))
    open(OUT_D, "w", encoding="utf-8").write(_ser(D))
    print("contracts=%d (all required_inputs=UNRESOLVED_NO_CONTRACT・種のみ) | canonical=%d(空=authored 待ち)"
          % (len(contracts), len(canon)))
    print("C rows=%d (UNRESOLVED_NO_CONTRACT=%d) | D rows=%d (UNRESOLVED_NO_CANONICAL=%d) | live conflicts=%d"
          % (len(C), sum(1 for r in C if str(r['verdict']).startswith('UNRESOLVED')),
             len(D), sum(1 for r in D if str(r['canonical']).startswith('UNRESOLVED')), len(conflicts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
