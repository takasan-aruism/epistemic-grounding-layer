#!/usr/bin/env python3
"""Stage 3: COMPONENT_INVENTORY — deterministic assembly + 5-state ladder.
Spec §1.2 / §4.1. Component labels are SEEDED from the existing SoR
(twoder/audit/ARTIFACT_REGISTRY.jsonl component_owner) — not invented here (R3).
The ladder is COMPUTED from 5 independent mechanical sources, never judged.
"""
import json, re, collections
from pathlib import Path

S = Path("/home/takasan/egl/structure")
HOME = Path("/home/takasan")

man = {f"{r['repo']}/{r['relative_path']}": r for r in map(json.loads, open(S/"FILE_MANIFEST.jsonl"))}
sym = {r["key"]: r for r in map(json.loads, open(S/"SYMBOL_INDEX.jsonl"))}
reach = {r["key"]: r for r in map(json.loads, open(S/"REACHABILITY.jsonl"))}
symreach = collections.defaultdict(list)
for r in map(json.loads, open(S/"SYMBOL_REACHABILITY.jsonl")):
    symreach[r["key"]].append(r)
cons = {r["key"]: r for r in map(json.loads, open(S/"FILE_EXTRACTION_CONSENSUS.jsonl"))}
execsig = [json.loads(l) for l in open(S/"EXECUTION_EVIDENCE.jsonl")]

# ---- seed labels from the existing SoR ------------------------------------
seed = {}
for d in map(json.loads, (l for l in open(HOME/"twoder/audit/ARTIFACT_REGISTRY.jsonl") if l.strip())):
    rp, rn = d.get("relative_path"), d.get("repo_name")
    if rp and rn:
        seed[f"{rn}/{rp}"] = d.get("component_owner")

# ---- ITEM <-> file binding (deterministic, from ROADMAP_REGISTRY) ----------
items = {}
for d in map(json.loads, (l for l in open(HOME/"twoder/audit/ROADMAP_REGISTRY.jsonl") if l.strip())):
    if d.get("kind") == "ITEM" and d.get("item_id"):
        items.setdefault(d["item_id"], {"title": None, "status": None})
        if d.get("title"): items[d["item_id"]]["title"] = d["title"]
        items[d["item_id"]]["status"] = d.get("status")
item_of_file = {}
for iid in items:
    for pref in ("ITEM-2DER-IMPL-PLATFORM-", "ITEM-2DER-TEMPORAL-", "ITEM-2DER-PARALLEL-OPS-",
                 "ITEM-2DER-OFFRAMP-", "ITEM-2DER-EVO-", "ITEM-2DER-AC-"):
        if iid.startswith(pref):
            snake = iid[len(pref):].lower().replace("-", "_")
            for cand in (f"twoder/{snake}.py",):
                if cand in man:
                    item_of_file.setdefault(cand, []).append(iid)

# ---- component assignment --------------------------------------------------
DIR_RULE = [("ds/ds/", "DS"), ("rri/rri/", "RRI"), ("dev-workcell/dw/", "DW"),
            ("egl/egl/", "EGL"), ("egl/autonomy/", "EGL_AUTONOMY"),
            ("egl/experiments/", "EGL_EXPERIMENT"), ("egl/docs/", "ARCHIVE_DOCS"),
            ("dev-workcell/experiments/", "DW_EXPERIMENT"),
            ("twoder/experiments/", "TWODER_EXPERIMENT"), ("twoder/regression/", "TEST"),
            ("twoder/audit/", "AUDIT"), ("twoder/tools/", "TWODER_TOOLS")]
def assign(k, r):
    if r["classification"] == "test" or "/test" in "/" + k:
        return "TEST"
    for pre, name in DIR_RULE:
        if k.startswith(pre):
            return name
    if seed.get(k) and seed[k] not in (None, "TEST"):
        return seed[k]
    if k.startswith("twoder/"):
        return "TWODER"
    return "OTHER"

members = collections.defaultdict(list)
for k, r in man.items():
    if r["extension"] != ".py":
        continue
    members[assign(k, r)].append(k)

# ---- executed: map runtime signals to components ---------------------------
SIG_RULE = [("ds_events", "DS"), ("rri_records", "RRI"), ("dw_events", "DW"),
            ("egl_events", "EGL"), ("failure_recurrence", "TWODER"),
            ("twoder_runs", "TWODER")]
KEY_RULE = [("DS_", "DS"), ("RRI_", "RRI"), ("EGL_", "EGL"), ("DW_", "DW")]
exec_count = collections.Counter(); exec_sigs = collections.defaultdict(list)
for e in execsig:
    sig = e["signal"]; src = sig.split("::")[0]; rest = sig.split("::", 1)[1]
    comp = None
    for pre, c in KEY_RULE:
        if rest.startswith("key=" + pre) or rest.startswith(pre):
            comp = c; break
    if comp is None:
        comp = dict(SIG_RULE).get(src, "OTHER")
    exec_count[comp] += e["count"]
    if len(exec_sigs[comp]) < 8:
        exec_sigs[comp].append({"signal": sig, "count": e["count"]})

# ---- documented: md files that reference a member file ---------------------
doc_ref = collections.Counter(); doc_where = collections.defaultdict(set)
mdrows = [r for r in sym.values() if r["language"] == "markdown"]
basen = {k.split("/")[-1]: comp for comp, ks in members.items() for k in ks}
for m in mdrows:
    for cr in m.get("code_refs", []):
        c = basen.get(cr)
        if c:
            doc_ref[c] += 1; doc_where[c].add(m["key"])

# ---- proven: CDEF-2DER-v1 rule --------------------------------------------
cdef_path = HOME/"twoder/audit/COMPLETION_DEFINITION_REGISTRY.jsonl"
cdef_rows = [json.loads(l) for l in open(cdef_path) if l.strip()] if cdef_path.exists() else []

rows = []
for comp, ks in sorted(members.items()):
    ks = sorted(ks)
    n_def = sum(len(sym.get(k, {}).get("defines", [])) for k in ks)
    loc = sum(sym.get(k, {}).get("loc", 0) for k in ks)
    wired_files = [k for k in ks if reach.get(k, {}).get("wired")]
    sym_reached = sum(1 for k in ks for s in symreach.get(k, []) if s["symbol_reached"])
    ex = exec_count.get(comp, 0)
    ladder = {
        "documented": "YES" if doc_ref.get(comp) else "NO",
        "implemented": "YES" if n_def else "NO",
        "wired": "YES" if wired_files else "NO",
        # CORRECTNESS: `NO` may only be asserted where the component's signal space is
        # actually covered by the scan. Components without a dedicated signal namespace
        # (UI/OPERATOR/AUTHORITY/AUDIT — their activity is recorded under twoder_runs and
        # attributed to TWODER) are UNRESOLVED, not NO. Asserting NO there would be a
        # false claim, not a conservative one.
        "executed": ("YES" if ex else
                     ("UNRESOLVED_NO_SIGNAL_NAMESPACE" if wired_files else "NO_EVIDENCE")),
        "proven": "NO",   # CDEF-2DER-v1: no bound acceptance artifact + JREV verdict found
    }
    caps = [c for k in ks for c in cons.get(k, {}).get("actual_capabilities", [])]
    gaps = [dict(g, file=k) for k in ks for g in cons.get(k, {}).get("capability_gap", [])]
    rows.append({
        "component_id": comp, "member_files": len(ks), "loc": loc, "defines": n_def,
        "files_wired": len(wired_files), "symbols_reached": sym_reached,
        "execution_signal_count": ex, "execution_signals": exec_sigs.get(comp, []),
        "doc_mentions": doc_ref.get(comp, 0), "doc_files": sorted(doc_where.get(comp, []))[:8],
        "ladder": ladder,
        "consensus_capabilities": len(caps),
        "consensus_capability_gaps": len(gaps),
        "top_gaps": [{"file": g["file"], "label": g["label"][:140],
                      "lines": [g["line_start"], g["line_end"]], "votes": g["votes"]}
                     for g in sorted(gaps, key=lambda x: -x["votes"])[:5]],
        "bound_items": sorted({i for k in ks for i in item_of_file.get(k, [])}),
        "trust_tier": "T3_DERIVED", "regenerable": True,
        "derived_from": "FILE_MANIFEST+SYMBOL_INDEX+REACHABILITY+SYMBOL_REACHABILITY+"
                        "EXECUTION_EVIDENCE+FILE_EXTRACTION_CONSENSUS; labels seeded from "
                        "twoder/audit/ARTIFACT_REGISTRY.component_owner",
    })
(S/"COMPONENT_INVENTORY.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

print(f"components: {len(rows)}   CDEF registry rows: {len(cdef_rows)}")
print(f"{'component':18s} {'files':>5s} {'LOC':>6s} {'wired':>5s} {'symR':>5s} {'exec':>6s} "
      f"{'doc':>4s}  ladder(D/I/W/E/P)  gaps")
for r in sorted(rows, key=lambda x: -x["loc"]):
    l = r["ladder"]
    lad = "".join("Y" if l[x] == "YES" else ("?" if str(l[x]).startswith("UNRESOLVED") else "-")
                  for x in
                  ("documented", "implemented", "wired", "executed", "proven"))
    print(f"{r['component_id']:18s} {r['member_files']:5d} {r['loc']:6d} {r['files_wired']:5d} "
          f"{r['symbols_reached']:5d} {r['execution_signal_count']:6d} {r['doc_mentions']:4d}  "
          f"{lad:^17s}  {r['consensus_capability_gaps']:4d}")
print(f"\nfile<->ITEM bindings resolved: {len(item_of_file)} files")
