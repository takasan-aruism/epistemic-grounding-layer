#!/usr/bin/env python3
"""HBB arm C (AFE ensemble) × DEV/VAL(16) × Hint ladder H0-H3 (rung独立)。
6 Aruism-core operators concurrent → deterministic aggregation → anonymized orchestrator → <=3 FEC。
baseline と同一 T0 packet + 同一 hint。leak-controlled (input = T0 pre-intervention only)."""
import json, sys, urllib.request, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl/experiments")
from run_afe_walking import ADMITTED, run_operator, aggregate, orchestrate  # reuse AFE machinery
HINTS = {"H0": "次にどう進めるべきか。", "H1": "現在の問題設定自体に、暗黙の追加前提はないか。",
  "H2": "定義と予測、機構と導入時期、局所とprogram、層/主体などを分離して再検討せよ。",
  "H3": "比較対象または観測変数を直接測り、現在のframeを反証できる実験を提案せよ。"}
DEPTH = {"H0": 4, "H1": 3, "H2": 2, "H3": 1}
T0 = json.load(open("/home/takasan/egl/experiments/hbb_t0_packets.json"))["packets"]
CAND = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
def cell(args):
    iid, rung = args
    frame = T0[iid]["t0_stuck_frame"] + "\n\n(hint) " + HINTS[rung]
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        sigs = list(ex.map(lambda o: run_operator(o, frame), ADMITTED))
    cands = aggregate(sigs)
    fec = orchestrate(frame, cands)
    return {"id": iid, "class": CAND[iid]["class"], "scope": CAND[iid]["intervention_scope"], "rung": rung, "depth": DEPTH[rung],
            "fec": fec, "n_signal": sum(1 for s in sigs if s.get("verdict") == "SIGNAL"), "n_cand": len(cands)}
def main():
    ids = json.load(open("/home/takasan/egl/experiments/hbb_split.json"))
    run_ids = ids["DEV"] + ids["VALIDATION"]
    cells = [(iid, rung) for iid in run_ids for rung in ("H0", "H1", "H2", "H3")]
    print(f"arm C (AFE): {len(run_ids)} incidents × 4 rungs = {len(cells)} cells")
    res = []
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for r in ex.map(cell, cells):
            res.append(r); print(f"[{r['id']} {r['rung']}] sig {r['n_signal']}/6 fec {len(r['fec']) if isinstance(r['fec'],list) else 0}", flush=True)
    Path("/home/takasan/egl/experiments/hbb_armC_run.json").write_text(json.dumps({"results": res}, ensure_ascii=False, indent=2))
    print("-> hbb_armC_run.json")
if __name__ == "__main__":
    main()
