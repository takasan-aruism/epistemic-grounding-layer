#!/usr/bin/env python3
"""Stage 4: EDGE_INVENTORY — the core artifact. Deterministic (spec v0.2 §B).

An edge is a cross-component call site: (caller file, line) -> (callee file, symbol).
Each edge is classified by the v0.2 decision table, including two states that only
appeared in measurement:
  WIRED_UNENTERED  — the call site sits inside `if <param>:` whose default is falsy
  TEST_ONLY_ISLAND — the caller is reachable only from tests / acceptance harnesses
`NO` is never asserted where the signal space is not covered (v0.2 §C).
"""
import ast, json, collections
from pathlib import Path

S = Path("/home/takasan/egl/structure"); HOME = Path("/home/takasan")
man = {f"{r['repo']}/{r['relative_path']}": r for r in map(json.loads, open(S/"FILE_MANIFEST.jsonl"))}
sym = {r["key"]: r for r in map(json.loads, open(S/"SYMBOL_INDEX.jsonl"))}
reach = {r["key"]: r for r in map(json.loads, open(S/"REACHABILITY.jsonl"))}
comp_rows = [json.loads(l) for l in open(S/"COMPONENT_INVENTORY.jsonl")]
execed = {r["component_id"]: r["execution_signal_count"] for r in comp_rows}

# component of each file (recompute with the same rules as s3)
DIR_RULE = [("ds/ds/","DS"),("rri/rri/","RRI"),("dev-workcell/dw/","DW"),("egl/egl/","EGL"),
            ("egl/autonomy/","EGL_AUTONOMY"),("egl/experiments/","EGL_EXPERIMENT"),
            ("egl/docs/","ARCHIVE_DOCS"),("dev-workcell/experiments/","DW_EXPERIMENT"),
            ("twoder/experiments/","TWODER_EXPERIMENT"),("twoder/regression/","TEST"),
            ("twoder/audit/","AUDIT"),("twoder/tools/","TWODER_TOOLS")]
SPECIAL = {"twoder/webui.py":"UI","twoder/operator.py":"OPERATOR",
           "twoder/authority.py":"AUTHORITY","twoder/procedure_audit.py":"AUDIT"}
def comp_of(k):
    if k in SPECIAL: return SPECIAL[k]
    if man.get(k,{}).get("classification")=="test" or "/test" in "/"+k: return "TEST"
    for pre,n in DIR_RULE:
        if k.startswith(pre): return n
    return "TWODER" if k.startswith("twoder/") else "OTHER"

# module resolution
modmap = collections.defaultdict(list)
def modnames(repo, rel):
    p = rel[:-3].replace("/", ".")
    if p.endswith(".__init__"): p = p[:-9]
    out = {p}
    if repo != "dev-workcell": out.add(f"{repo}.{p}")
    return {x for x in out if x}
for k, r in man.items():
    if r["extension"] == ".py":
        for m in modnames(r["repo"], r["relative_path"]): modmap[m].append(k)

def falsy_default(node, name):
    """Is `name` a parameter of the enclosing function with a falsy default?"""
    a = node.args
    params = list(a.posonlyargs) + list(a.args)
    defs = list(a.defaults)
    pad = len(params) - len(defs)
    for i, p in enumerate(params):
        if p.arg == name and i >= pad:
            d = defs[i - pad]
            if isinstance(d, ast.Constant) and not d.value: return True
            if isinstance(d, (ast.Dict, ast.List, ast.Tuple)) and not getattr(d, "elts", getattr(d, "keys", [1])):
                return True
    for kw, kd in zip(a.kwonlyargs, a.kw_defaults):
        if kw.arg == name and isinstance(kd, ast.Constant) and not kd.value: return True
    return False

edges = []
ALL_CALLS = []
for k, r in man.items():
    if r["extension"] != ".py": continue
    try: tree = ast.parse(Path(r["absolute_path"]).read_text(encoding="utf-8", errors="replace"))
    except Exception: continue
    alias_mod, alias_sym = {}, {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a2 in n.names: alias_mod[a2.asname or a2.name.split(".")[0]] = a2.name
        elif isinstance(n, ast.ImportFrom):
            for a2 in n.names:
                alias_sym[a2.asname or a2.name] = (n.module or "", a2.name)
                alias_mod.setdefault(a2.asname or a2.name, f"{n.module or ''}.{a2.name}")
    # walk with function + if-guard context
    def walk(node, fnstack, guards):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fnstack = fnstack + [node]
        if isinstance(node, ast.If):
            g = None
            if isinstance(node.test, ast.Name): g = node.test.id
            for ch in node.body:
                walk(ch, fnstack, guards + ([g] if g else []))
            for ch in node.orelse: walk(ch, fnstack, guards)
            return
        if isinstance(node, ast.Call):
            f = node.func
            expr = None
            try: expr = ast.unparse(f)
            except Exception: pass
            if expr:
                parts = expr.split("."); head, tail = parts[0], parts[1:]
                tgt = None
                if tail and head in alias_mod:
                    for c in modmap.get(alias_mod[head], []): tgt = c; break
                elif not tail and head in alias_sym:
                    mod, s2 = alias_sym[head]
                    for c in modmap.get(mod, []) or modmap.get(f"{mod}.{s2}", []): tgt = c; break
                if tgt and tgt != k:
                    gated = [g for g in guards
                             if fnstack and falsy_default(fnstack[-1], g)]
                    ALL_CALLS.append({"caller_file": k, "callee_file": tgt,
                                      "gated": bool(gated), "line": node.lineno})
                if tgt and comp_of(tgt) != comp_of(k):
                    gated = [g for g in guards
                             if fnstack and falsy_default(fnstack[-1], g)]
                    edges.append({"caller_file": k, "callee_file": tgt,
                                  "producer": comp_of(k), "consumer": comp_of(tgt),
                                  "callee_symbol": ".".join(tail) or head,
                                  "line": node.lineno,
                                  "enclosing_fn": fnstack[-1].name if fnstack else "<module>",
                                  "guards": guards, "falsy_default_guards": gated})
        for ch in ast.iter_child_nodes(node): walk(ch, fnstack, guards)
    walk(tree, [], [])

# ---- GATE PROPAGATION (spec v0.2 §B) --------------------------------------
# A file is ENTERED_ONLY_UNDER_FALSY_GUARD when every incoming call from a LIVE-reachable
# file sits inside an `if <param>:` whose default is falsy. Such a file cannot be entered
# on the default path, so its own outgoing edges inherit WIRED_UNENTERED.
incoming = collections.defaultdict(list)
for c in ALL_CALLS:
    incoming[c["callee_file"]].append(c)
GATED_FILES = {}
changed = True
while changed:                      # transitive: gated caller propagates downstream
    changed = False
    for f, cs in incoming.items():
        live_in = [c for c in cs if reach.get(c["caller_file"], {}).get("wired")]
        if not live_in:
            continue
        if all(c["gated"] or GATED_FILES.get(c["caller_file"]) for c in live_in):
            if not GATED_FILES.get(f):
                GATED_FILES[f] = sorted({c["caller_file"] for c in live_in})[:4]
                changed = True

# aggregate to unique (producer, consumer, caller_file, callee_file, symbol)
agg = {}
for e in edges:
    key = (e["producer"], e["consumer"], e["caller_file"], e["callee_file"], e["callee_symbol"])
    a = agg.setdefault(key, dict(e, call_sites=[], gated_sites=[]))
    a["call_sites"].append(e["line"])
    if e["falsy_default_guards"]: a["gated_sites"].append({"line": e["line"], "guard": e["falsy_default_guards"]})

TESTY = ("TEST",)
def classify(a):
    cf = a["caller_file"]
    caller_wired = reach.get(cf, {}).get("wired", False)
    importers = sym.get(cf, {}).get("imported_by", [])
    only_test = bool(importers) and all(comp_of(i) in TESTY or
                                        i.endswith("acceptance_harness.py") for i in importers)
    ex = execed.get(a["consumer"], 0)
    if caller_wired and a["gated_sites"] and len(a["gated_sites"]) == len(set(a["call_sites"])):
        return "WIRED_UNENTERED"
    if GATED_FILES.get(cf):
        return "WIRED_UNENTERED"
    if caller_wired:
        return "LIVE" if ex > 0 else "WIRED_EXECUTION_UNRESOLVED"
    if a["producer"] == "TEST" or only_test or cf.endswith("acceptance_harness.py"):
        return "TEST_ONLY_ISLAND"
    if importers:
        return "IMPLEMENTED_UNWIRED"
    return "IMPLEMENTED_UNWIRED"

rows = []
for key, a in sorted(agg.items()):
    a["status"] = classify(a)
    a["caller_wired"] = reach.get(a["caller_file"], {}).get("wired", False)
    a["caller_entered_only_under_falsy_guard"] = GATED_FILES.get(a["caller_file"])
    a["consumer_execution_signals"] = execed.get(a["consumer"], 0)
    a["evidence"] = [f"{a['caller_file']}:{l}" for l in sorted(set(a["call_sites"]))[:6]]
    a["trust_tier"] = "T3_DERIVED"; a["regenerable"] = True
    a["derived_from"] = "AST cross-component call sites + REACHABILITY + EXECUTION_EVIDENCE (spec v0.2 §B)"
    for f in ("falsy_default_guards", "guards", "line"): a.pop(f, None)
    rows.append(a)
(S/"EDGE_INVENTORY.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows)+"\n")

print(f"cross-component call edges: {len(rows)}  (raw call sites {len(edges)})")
c = collections.Counter(r["status"] for r in rows)
for k, v in c.most_common(): print(f"  {v:5d}  {k}")
print(f"\ngate-propagated files (entered only under falsy guard): {len(GATED_FILES)}")
for f, src in sorted(GATED_FILES.items())[:12]: print(f"   {f}   <- gated by {src}")
print("\n=== WIRED_UNENTERED (呼出点はあるが falsy 既定の分岐の内側) ===")
for r in rows:
    if r["status"] == "WIRED_UNENTERED":
        print(f"  {r['producer']}->{r['consumer']}  {r['evidence'][0]}  "
              f"{r['callee_symbol']}")
print("\n=== 系統間の辺（4責任系 + UI/OPERATOR のみ）===")
CORE = {"DS","RRI","EGL","DW","TWODER","UI","OPERATOR","AUTHORITY","AUDIT"}
m = collections.Counter((r["producer"], r["consumer"], r["status"]) for r in rows
                        if r["producer"] in CORE and r["consumer"] in CORE)
for (p, cns, st), v in sorted(m.items()):
    print(f"  {p:10s} -> {cns:10s} {st:28s} {v}")
