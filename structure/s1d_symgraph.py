#!/usr/bin/env python3
"""Stage 1d: symbol-level call graph + reachability. Deterministic, no LLM.
Spec §4.3 / closes UNRESOLVED U1.

Module-level reachability (s1_reach.py) proves only that a file is IMPORTED on the
live path. This stage asks the stricter question: is a given FUNCTION actually
called from an entrypoint?

Resolution is deliberately conservative:
  - every unresolved call is COUNTED and reported (no silent drops)
  - ambiguous method names resolve to ALL candidates (over-approximation),
    so `reached` stays an UPPER BOUND, never an under-count
Never imports target modules (twoder/operator.py shadows stdlib `operator`, DE-0486 §5b).
"""
import ast, json
from collections import defaultdict, deque
from pathlib import Path

HOME = Path("/home/takasan")
STRUCT = HOME / "egl/structure"
MANIFEST = STRUCT / "FILE_MANIFEST.jsonl"

ENTRY_FILES = ["twoder/webui.py", "twoder/submit.py", "twoder/operator.py",
               "dev-workcell/dw/dispatch.py"]

# ---------- load python files ----------
files = {}
for line in open(MANIFEST):
    r = json.loads(line)
    if r["extension"] == ".py" and r["classification"] in ("source", "test"):
        files[f"{r['repo']}/{r['relative_path']}"] = r

def module_names(repo, rel):
    p = rel[:-3].replace("/", ".")
    if p.endswith(".__init__"):
        p = p[:-9]
    out = {p}
    if repo != "dev-workcell":
        out.add(f"{repo}.{p}")
    return {x for x in out if x}

modmap = defaultdict(list)          # dotted module -> [file keys]
for k, r in files.items():
    for m in module_names(r["repo"], r["relative_path"]):
        modmap[m].append(k)

# ---------- per-file AST pass ----------
defs = {}                            # (file, qualname) -> meta
defs_by_name = defaultdict(list)     # bare name -> [(file, qual)]
alias_mod = {}                       # file -> {alias: dotted module}
alias_sym = {}                       # file -> {localname: (dotted module, symbol)}
raw_calls = defaultdict(list)        # (file, qual) -> [callee expr strings]
trees = {}

for k, r in files.items():
    try:
        src = Path(r["absolute_path"]).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except Exception:
        continue
    trees[k] = tree
    alias_mod[k], alias_sym[k] = {}, {}

    class Walker(ast.NodeVisitor):
        def __init__(self):
            self.stack = ["<module>"]
        def qual(self):
            return ".".join(self.stack[1:]) or "<module>"
        def _def(self, node, kind):
            self.stack.append(node.name)
            q = self.qual()
            defs[(k, q)] = {"file": k, "qual": q, "kind": kind, "name": node.name,
                            "lineno": node.lineno,
                            "end_lineno": getattr(node, "end_lineno", node.lineno),
                            "is_public": not node.name.startswith("_")}
            defs_by_name[node.name].append((k, q))
            self.generic_visit(node)
            self.stack.pop()
        def visit_FunctionDef(self, n): self._def(n, "function")
        def visit_AsyncFunctionDef(self, n): self._def(n, "function")
        def visit_ClassDef(self, n): self._def(n, "class")
        def visit_Import(self, n):
            for a in n.names:
                alias_mod[k][a.asname or a.name.split(".")[0]] = a.name
            self.generic_visit(n)
        def visit_ImportFrom(self, n):
            mod = n.module or ""
            for a in n.names:
                alias_sym[k][a.asname or a.name] = (mod, a.name)
                alias_mod[k].setdefault(a.asname or a.name, f"{mod}.{a.name}")
            self.generic_visit(n)
        def visit_Call(self, n):
            try:
                expr = ast.unparse(n.func)
            except Exception:
                expr = None
            if expr:
                raw_calls[(k, self.qual())].append(expr)
            self.generic_visit(n)
    Walker().visit(tree)

# ---------- callee resolution ----------
STATS = {"total": 0, "resolved_import": 0, "resolved_local": 0,
         "resolved_by_name_unique": 0, "resolved_by_name_multi": 0,
         "unresolved_builtin_or_dynamic": 0}

def resolve(file_key, expr):
    """expr -> list of (file, qual). Over-approximating; never guesses silently."""
    STATS["total"] += 1
    parts = expr.split(".")
    head, tail = parts[0], parts[1:]

    # from X import f  ->  f()
    if not tail and head in alias_sym.get(file_key, {}):
        mod, sym = alias_sym[file_key][head]
        for tgt in modmap.get(mod, []):
            if (tgt, sym) in defs:
                STATS["resolved_import"] += 1
                return [(tgt, sym)]
        for tgt in modmap.get(f"{mod}.{sym}", []):
            if (tgt, "<module>") in defs or tgt in files:
                STATS["resolved_import"] += 1
                return [(tgt, "<module>")]

    # import M / from P import M  ->  M.f()   (also M.C.f)
    if tail and head in alias_mod.get(file_key, {}):
        mod = alias_mod[file_key][head]
        for depth in range(len(tail), 0, -1):
            cand_mod = ".".join([mod] + tail[:depth - 1]) if depth > 1 else mod
            sym = ".".join(tail[depth - 1:])
            for tgt in modmap.get(cand_mod, []):
                if (tgt, sym) in defs:
                    STATS["resolved_import"] += 1
                    return [(tgt, sym)]
                if (tgt, sym.split(".")[0]) in defs:
                    STATS["resolved_import"] += 1
                    return [(tgt, sym.split(".")[0])]

    # local definition in same file
    if not tail and (file_key, head) in defs:
        STATS["resolved_local"] += 1
        return [(file_key, head)]

    # method / attribute call: resolve by bare name across the whole codebase
    name = tail[-1] if tail else head
    cands = defs_by_name.get(name, [])
    if cands:
        if len(cands) == 1:
            STATS["resolved_by_name_unique"] += 1
        else:
            STATS["resolved_by_name_multi"] += 1
        return cands
    STATS["unresolved_builtin_or_dynamic"] += 1
    return []

edges = defaultdict(set)
for (fk, caller), exprs in raw_calls.items():
    for e in exprs:
        for tgt in resolve(fk, e):
            edges[(fk, caller)].add(tgt)

# a def is also "entered" when its enclosing scope runs (module-level defs of a
# reached module are NOT auto-reached; only <module> is, plus explicit calls)
# ---------- seeds ----------
seeds = set()
for ek in ENTRY_FILES:
    if ek in files:
        seeds.add((ek, "<module>"))
        for (fk, q), m in defs.items():
            if fk == ek and "." not in q and m["is_public"]:
                seeds.add((fk, q))          # entrypoint public surface (HTTP handlers etc.)

seen, depth, parent = set(), {}, {}
q = deque()
for s in seeds:
    if s in defs or s[1] == "<module>":
        seen.add(s); depth[s] = 0; q.append(s)
while q:
    cur = q.popleft()
    for nxt in sorted(edges.get(cur, ())):
        if nxt not in seen:
            seen.add(nxt); depth[nxt] = depth[cur] + 1; parent[nxt] = cur; q.append(nxt)

# ---------- output ----------
rows = []
for (fk, qual), m in sorted(defs.items()):
    reached = (fk, qual) in seen
    rows.append({
        "key": fk, "symbol": qual, "kind": m["kind"],
        "lineno": m["lineno"], "end_lineno": m["end_lineno"],
        "is_public": m["is_public"],
        "symbol_reached": reached,
        "reach_depth": depth.get((fk, qual)),
        "called_by": sorted(f"{a}::{b}" for (a, b) in
                            [c for c, tg in edges.items() if (fk, qual) in tg])[:20],
        "calls_out": sorted(f"{a}::{b}" for a, b in edges.get((fk, qual), ()))[:40],
        "derived_from": "ast call-graph BFS from " + ",".join(ENTRY_FILES),
        "resolution_note": "over-approximating: ambiguous method names resolve to all "
                           "same-named defs, so reached is an UPPER BOUND",
        "regenerable": True,
    })
(STRUCT / "SYMBOL_REACHABILITY.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

# ---------- report ----------
import collections
print(f"defs indexed       : {len(defs)}")
print(f"call sites         : {sum(len(v) for v in raw_calls.values())}")
print("resolution:")
for k, v in STATS.items():
    if k != "total":
        print(f"  {v:6d}  {100*v/max(STATS['total'],1):5.1f}%  {k}")
print(f"  {STATS['total']:6d}  100.0%  TOTAL")
reached = [r for r in rows if r["symbol_reached"]]
print(f"\nsymbols reached    : {len(reached)} / {len(rows)}  ({100*len(reached)/len(rows):.1f}%)")
rf = {r["key"] for r in reached}
print(f"files with >=1 reached symbol : {len(rf)}")
mod_live = {json.loads(l)["key"] for l in open(STRUCT / "REACHABILITY.jsonl")
            if json.loads(l)["wired"]}
print(f"module-level LIVE             : {len(mod_live)}")
print(f"  both                        : {len(rf & mod_live)}")
print(f"  module-LIVE but no reached symbol : {len(mod_live - rf)}")
print(f"  symbol-reached but NOT module-LIVE: {len(rf - mod_live)}")
