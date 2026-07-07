#!/usr/bin/env python3
"""Round C value-axis: A0 NULL / A1 ABSTRACT_V2 / A2 FULL-PREDICATE META-FRAME(MF-002)。
A0/A1 は roundb_v2_run から再利用。A2 のみ Qwen。匿名化 shuffle batch を external-weight(Claude)採点用に出力。"""
import json, sys, hashlib, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
from run_roundb import HELDOUT, chat, jl, BASE
# MF-002 full-predicate(applicability predicate + suggested axes。incident 無し・domain 名詞無し)
MF002 = ("A general pattern that sometimes applies: when a surface result/metric/finding is being taken at face "
    "value, suspect it may be an artifact of a construction/observation/experimental-setup choice that has not yet "
    "been varied; the goal is to separate the apparent from the grounded. Suggested axes: (1) vary the "
    "construction/observation choice and re-measure; (2) separate apparent from grounded (signal vs artifact-of-"
    "setup); (3) confirm the mechanism before treating the metric as a finding.")

def main():
    rb = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/roundb_v2_run.json"))["heldout"]}
    strat = {t["id"]: t["base_has_target"] for t in json.load(open("/home/takasan/egl/experiments/gate_pilot.json"))["tasks"]}
    pf = {h["id"]: h["pre"] for h in HELDOUT}
    tasks = []
    for h in HELDOUT:
        tid = h["id"]; r = rb[tid]
        a2 = jl(chat(BASE, f"{MF002}\n\nUsing it if helpful:\n{h['pre']}", seed=0))
        tasks.append({"id": tid, "domain": h["domain"], "target": h["axis"], "base_has_target": strat[tid],
                      "arms": {"A0_null": r["axes"]["ordinary"], "A1_abstract_v2": r["axes"]["abstract_v2"], "A2_full_predicate": a2}})
        print(f"[{tid} {h['domain']}] A2 done (base_has_target={strat[tid]})", flush=True)
    Path("/home/takasan/egl/experiments/roundc_run.json").write_text(json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
    # 匿名化 shuffle batch(label 除去、hash id)→ external-weight 採点用
    batch = []
    for t in tasks:
        for arm, axes in t["arms"].items():
            aid = "C-" + hashlib.sha256(f"{t['id']}|{arm}".encode()).hexdigest()[:5]
            batch.append({"anon": aid, "_id": t["id"], "_arm": arm, "domain": t["domain"], "target": t["target"],
                          "situation": pf[t["id"]], "axes": axes})
    batch.sort(key=lambda x: x["anon"])
    Path("/home/takasan/egl/experiments/roundc_batch.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2))
    print(f"\n=== anonymized batch (N={len(batch)}) for external-weight scoring ===")
    for b in batch:
        print(f"\n[{b['anon']}] ({b['domain']}) TARGET: {b['target'][:95]}")
        print(f"    SITUATION: {b['situation'][:110]}")
        for i, a in enumerate(b["axes"][:3]): print(f"    axis{i+1}: {str(a)[:120]}")

if __name__ == "__main__":
    main()
