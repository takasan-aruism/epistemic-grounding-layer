#!/usr/bin/env python3
"""Stage 1c: reachability from live entrypoints — the `wired` column. Deterministic.
Spec §4.3. Answers: which T1 source files are actually on the live path.
"""
import json, re
from collections import deque, defaultdict
from pathlib import Path

STRUCT = Path("/home/takasan/egl/structure")
rows = [json.loads(l) for l in open(STRUCT / "SYMBOL_INDEX.jsonl")]
by = {r["key"]: r for r in rows}

ENTRYPOINTS = ["twoder/webui.py", "twoder/submit.py", "twoder/operator.py",
               "dev-workcell/dw/dispatch.py"]

# module -> files  (rebuild forward edges)
modmap = defaultdict(list)
for r in rows:
    for m in r.get("module_names", []) or []:
        modmap[m].append(r["key"])

fwd = defaultdict(set)
for r in rows:
    for imp in r.get("imports", []):
        mod, sym = imp["module"] or "", imp.get("symbol")
        for cand in (f"{mod}.{sym}" if sym else None, mod):
            if cand and cand in modmap:
                fwd[r["key"]].update(modmap[cand])
                break

def bfs(seeds):
    seen, depth, q = set(), {}, deque()
    for s in seeds:
        if s in by:
            seen.add(s); depth[s] = 0; q.append(s)
    parent = {}
    while q:
        cur = q.popleft()
        for nxt in sorted(fwd.get(cur, ())):
            if nxt not in seen:
                seen.add(nxt); depth[nxt] = depth[cur] + 1
                parent[nxt] = cur; q.append(nxt)
    return seen, depth, parent

reach, depth, parent = bfs(ENTRYPOINTS)

def path_to(k):
    out, cur, guard = [k], k, 0
    while cur in parent and guard < 30:
        cur = parent[cur]; out.append(cur); guard += 1
    return list(reversed(out))

ARCHIVE = re.compile(r"/(SUBMIT_|docs/report/|experiments/|adjexp/|problems/)|\.zip")
out = []
for r in rows:
    if r["language"] != "python":
        continue
    k = r["key"]
    is_test = r["classification"] == "test"
    is_archive_copy = bool(ARCHIVE.search("/" + k))
    wired = k in reach
    has_cli = bool(r.get("cli_entrypoints"))
    if wired:
        cat = "LIVE_REACHABLE"
    elif is_test:
        cat = "TEST_ONLY"
    elif is_archive_copy:
        cat = "ARCHIVE_OR_EXPERIMENT"
    elif has_cli:
        cat = "STANDALONE_ENTRYPOINT"
    elif r["imported_by_count"] > 0:
        cat = "SUPPORT_OFF_LIVE_PATH"
    else:
        cat = "ORPHAN"
    out.append({
        "key": k, "repo": r["repo"], "trust_tier": r["trust_tier"],
        "classification": r["classification"], "loc": r.get("loc", 0),
        "wired": wired, "reach_depth": depth.get(k),
        "reach_path": path_to(k) if wired else [],
        "imported_by_count": r["imported_by_count"],
        "cli_entrypoints": r.get("cli_entrypoints", []),
        "reach_category": cat,
        "derived_from": "import-graph BFS from " + ",".join(ENTRYPOINTS),
        "regenerable": True,
    })
(STRUCT / "REACHABILITY.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")

import collections
c = collections.Counter(r["reach_category"] for r in out)
print(f"python files analysed: {len(out)}")
for k, v in c.most_common():
    loc = sum(r["loc"] for r in out if r["reach_category"] == k)
    print(f"  {v:4d} files  {loc:7d} LOC  {k}")
print("\nLIVE by repo:", dict(collections.Counter(r["repo"] for r in out if r["wired"])))
print("max depth:", max((r["reach_depth"] or 0) for r in out))
