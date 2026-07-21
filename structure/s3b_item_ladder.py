#!/usr/bin/env python3
"""Stage 3b: per-ITEM 5-state ladder. Feeds TR-2 (任意の ITEM -> コードと実行記録).
Deterministic. Binds ROADMAP_REGISTRY ITEMs to files, then computes the ladder per item.
"""
import json, collections
from pathlib import Path
S = Path("/home/takasan/egl/structure"); HOME = Path("/home/takasan")
man = {f"{r['repo']}/{r['relative_path']}": r for r in map(json.loads, open(S/"FILE_MANIFEST.jsonl"))}
sym = {r["key"]: r for r in map(json.loads, open(S/"SYMBOL_INDEX.jsonl"))}
reach = {r["key"]: r for r in map(json.loads, open(S/"REACHABILITY.jsonl"))}
cons = {r["key"]: r for r in map(json.loads, open(S/"FILE_EXTRACTION_CONSENSUS.jsonl"))}

items = {}
for d in map(json.loads, (l for l in open(HOME/"twoder/audit/ROADMAP_REGISTRY.jsonl") if l.strip())):
    if d.get("kind") == "ITEM" and d.get("item_id"):
        e = items.setdefault(d["item_id"], {"title": None, "status": None, "de": set()})
        if d.get("title"): e["title"] = d["title"]
        e["status"] = d.get("status")
        for f in ("evidence_de", "evidence_de_ids", "related_de_ids", "prereg_de"):
            v = d.get(f)
            if isinstance(v, str): e["de"].add(v)
            elif isinstance(v, list): e["de"].update(x for x in v if isinstance(x, str))

PREF = ("ITEM-2DER-IMPL-PLATFORM-", "ITEM-2DER-TEMPORAL-", "ITEM-2DER-PARALLEL-OPS-",
        "ITEM-2DER-OFFRAMP-", "ITEM-2DER-EVO-", "ITEM-2DER-AC-")
# runtime trace keys, for the `executed` column at item granularity
trace_keys = collections.Counter()
import glob
for f in glob.glob(str(HOME/"twoder/runs/*.json")):
    try: d = json.load(open(f))
    except Exception: continue
    if isinstance(d, dict): trace_keys.update(d.keys())

rows = []
for iid, e in sorted(items.items()):
    files = []
    for p in PREF:
        if iid.startswith(p):
            snake = iid[len(p):].lower().replace("-", "_")
            for cand in (f"twoder/{snake}.py", f"dev-workcell/dw/{snake}.py"):
                if cand in man: files.append(cand)
    files = sorted(set(files))
    implemented = bool(files) and any(sym.get(k, {}).get("defines") for k in files)
    wired = any(reach.get(k, {}).get("wired") for k in files)
    importers = sorted({i for k in files for i in sym.get(k, {}).get("imported_by", [])})
    live_importers = [i for i in importers if reach.get(i, {}).get("wired")]
    gaps = [dict(g, file=k) for k in files for g in cons.get(k, {}).get("capability_gap", [])]
    rows.append({
        "item_id": iid, "title": e["title"], "roadmap_status": e["status"],
        "bound_files": files, "importers": importers, "live_importers": live_importers,
        "ladder": {
            "documented": "YES",
            "implemented": "YES" if implemented else ("NO_FILE_BOUND" if not files else "NO"),
            "wired": "YES" if wired else ("UNRESOLVED_NO_FILE_BOUND" if not files else "NO"),
            "executed": "UNRESOLVED_NOT_COMPUTED_AT_ITEM_GRANULARITY",
            "proven": "NO",
        },
        "capability_gaps": [{"file": g["file"], "label": g["label"][:160],
                             "lines": [g["line_start"], g["line_end"]], "votes": g["votes"]}
                            for g in gaps[:4]],
        "trust_tier": "T3_DERIVED", "regenerable": True,
        "derived_from": "ROADMAP_REGISTRY + FILE_MANIFEST + REACHABILITY + consensus",
    })
(S/"ITEM_LADDER.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

n = len(rows)
bound = [r for r in rows if r["bound_files"]]
print(f"ITEMs: {n}   file-bound: {len(bound)}   unbound: {n-len(bound)}")
st = collections.Counter(r["roadmap_status"] for r in rows)
print("roadmap status:", dict(st))
print("\n=== DONE と申告されているが配線されていない ITEM ===")
bad = [r for r in rows if r["roadmap_status"] == "DONE" and r["bound_files"]
       and r["ladder"]["wired"] == "NO"]
for r in bad:
    print(f"  {r['item_id']}")
    print(f"     files={r['bound_files']} importers={r['importers'][:3]}")
print(f"  計 {len(bad)} 件")
print("\n=== DONE / 配線あり / live importer あり ===")
good = [r for r in rows if r["roadmap_status"] == "DONE" and r["ladder"]["wired"] == "YES"]
print(f"  計 {len(good)} 件")
print("\n=== DONE だがファイル束縛が解決できない (命名規約外) ===")
ub = [r for r in rows if r["roadmap_status"] == "DONE" and not r["bound_files"]]
print(f"  計 {len(ub)} 件 (TR-2 の未解決分)")
for r in ub[:8]: print("   ", r["item_id"], "|", (r["title"] or "")[:60])
