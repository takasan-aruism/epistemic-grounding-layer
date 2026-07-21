#!/usr/bin/env python3
"""Stage 1e: the `executed` column — from T2_RUNTIME evidence only. Deterministic.
Spec §1.2 / §4.4. T2 sources are the ONLY admissible basis for `executed`.
"""
import json, glob, collections
from pathlib import Path

STRUCT = Path("/home/takasan/egl/structure")
HOME = Path("/home/takasan")

SOURCES = {
    "twoder_runs":        sorted(glob.glob(str(HOME / "twoder/runs/*.json"))),
    "dw_events":          [str(HOME / "dev-workcell/events.jsonl")],
    "ds_events":          [str(HOME / "ds/ds_events.jsonl")],
    "rri_records":        [str(HOME / "rri/rri_records.jsonl")],
    "failure_recurrence": [str(HOME / "twoder/failure_recurrence.jsonl")],
    "egl_events":         sorted(glob.glob(str(HOME / "egl/data*/events.jsonl"))),
}

obs = collections.defaultdict(lambda: {"count": 0, "sources": set(), "samples": []})
stats = {}

def note(sig, src, sample=None):
    o = obs[sig]
    o["count"] += 1
    o["sources"].add(src)
    if sample and len(o["samples"]) < 3:
        o["samples"].append(str(sample)[:120])

for src, paths in SOURCES.items():
    n_files = n_rec = n_bad = 0
    for p in paths:
        if not Path(p).exists():
            continue
        n_files += 1
        if p.endswith(".jsonl"):
            for line in open(p, encoding="utf-8", errors="replace"):
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    n_bad += 1; continue
                n_rec += 1
                if not isinstance(d, dict):
                    continue
                # NOTE: `phase`/`role` were missing in v1 and made all 674 dev-workcell
                # events invisible (found by TR-5 failing). Key lists are themselves an
                # instrument — an unmatched schema reads identically to "no activity".
                for k in ("kind", "event_kind", "type", "record_type", "event", "op",
                          "operation", "stage", "actor", "actor_role",
                          "phase", "role", "status", "action", "event_type"):
                    v = d.get(k)
                    if isinstance(v, str) and v:
                        note(f"{src}::{k}={v}", src, Path(p).name)
        else:
            try:
                d = json.load(open(p, encoding="utf-8", errors="replace"))
            except Exception:
                n_bad += 1; continue
            n_rec += 1
            if isinstance(d, dict):
                for k in d:
                    note(f"{src}::key={k}", src, Path(p).name)
                for k in ("ACTOR_ROLE", "SELECTED_ACQUISITION_METHOD", "RRI_REQUEST_TYPE",
                          "NEXT_LEGAL_OPERATION", "DISPATCH_RESULT"):
                    v = d.get(k)
                    if isinstance(v, str) and v:
                        note(f"{src}::{k}={v[:60]}", src, Path(p).name)
    stats[src] = {"files": n_files, "records": n_rec, "unparsable": n_bad}

rows = []
for sig, o in sorted(obs.items(), key=lambda kv: -kv[1]["count"]):
    rows.append({"signal": sig, "count": o["count"],
                 "sources": sorted(o["sources"]), "samples": o["samples"],
                 "trust_tier": "T2_RUNTIME",
                 "derived_from": "runtime evidence scan", "regenerable": True})
(STRUCT / "EXECUTION_EVIDENCE.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

print("source scan:")
for k, v in stats.items():
    print(f"  {k:20s} files={v['files']:4d} records={v['records']:7d} unparsable={v['unparsable']}")
print(f"\ndistinct runtime signals: {len(rows)}")
print("\ntop 25:")
for r in rows[:25]:
    print(f"  {r['count']:6d}  {r['signal']}")
