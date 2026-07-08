#!/usr/bin/env python3
"""N=13 closure: run ONLY the two handoff incidents HBB-04/30 (5 arms x 4 rungs = 40 cells) on local
Qwen, reusing the frozen run_hbb_sealed.cell() pipeline, and APPEND to hbb_sealed_run.json. The original
220 cells (11 incidents, already GPT-scored) are left byte-identical. Deterministic (temp=0, seed=0)."""
import json, concurrent.futures as cf
from pathlib import Path
import run_hbb_sealed as rh

NEW = ["HBB-04", "HBB-30"]
RUNF = "/home/takasan/egl/experiments/hbb_sealed_run.json"

def main():
    for iid in NEW:
        assert iid in rh.T0 and rh.T0[iid].get("t0_stuck_frame"), f"{iid} T0 missing"
        assert iid in rh.ORIGIN, f"{iid} ORIGIN markers missing"
    cells = [(iid, arm, rung) for iid in NEW for arm in ("A", "B", "F", "C", "D") for rung in ("H0", "H1", "H2", "H3")]
    print(f"running {len(cells)} new cells for {NEW}", flush=True)
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        new_res = list(ex.map(rh.cell, cells))

    doc = json.load(open(RUNF))
    existing = doc["results"]
    have = {(r["id"], r["arm"], r["rung"]) for r in existing}
    added = [r for r in new_res if (r["id"], r["arm"], r["rung"]) not in have]
    doc["results"] = existing + added
    Path(RUNF).write_text(json.dumps(doc, ensure_ascii=False, indent=2))

    ids = sorted(set(r["id"] for r in doc["results"]))
    print(f"appended {len(added)} cells | total {len(doc['results'])} | incidents {len(ids)}: {ids}")
    for iid in NEW:
        n = sum(1 for r in doc["results"] if r["id"] == iid)
        empt = sum(1 for r in doc["results"] if r["id"] == iid and not r.get("output"))
        print(f"  {iid}: {n} cells, {empt} empty-output")

if __name__ == "__main__":
    main()
