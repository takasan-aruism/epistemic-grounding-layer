#!/usr/bin/env python3
"""Recon-exhibit consensus + H_exhibit. Integrates Qwen scores + GPT return -> per-candidate consensus
(GPT ∧ Qwen), -> per (condition,incident,seed) reached (>=1 candidate consensus REC2), -> per (condition,incident)
reach-rate over M seeds, incident-reached = >= ceil(M/2) seeds. H_exhibit(primary) = R2 reach exceeds R0 by
binomial (alpha=0.05, Bonferroni over 3 incidents). Secondaries: H_scheduler (R4>max(R3,R_bon)), H_structure
(R5-Lk), H_assist (R1/R3 vs R2). All under GPT-drop caveat (Qwen-alone REC2 reported)."""
import json, sys, math
from collections import defaultdict
EXP = "/home/takasan/egl/experiments"

def binom_tail(k, n, p):
    """P(X >= k | Binomial(n,p)). p=0 -> 1.0 if k==0 else 0.0."""
    if p <= 0: return 1.0 if k == 0 else 0.0
    if p >= 1: return 1.0
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def main():
    qfile = sys.argv[1] if len(sys.argv) > 1 else f"{EXP}/hbb_recon_qwen_scores.json"
    gfile = sys.argv[2] if len(sys.argv) > 2 else f"{EXP}/hbb_recon_gpt_return.json"
    M = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    alpha = 0.05
    qwen = {s["opaque_id"]: s for s in json.load(open(qfile))["scores"]}
    gret = json.load(open(gfile))
    gret = gret if isinstance(gret, list) else gret.get("scores", gret.get("items", []))
    gpt = {g["opaque_id"]: g for g in gret}
    # per-candidate consensus (only Qwen-REC2 candidates were sent to GPT; others cannot be consensus REC2)
    # reached[(cond,incident,seed)] = any candidate with GPT REC2==2 AND Qwen REC2==2
    reached = defaultdict(lambda: {"rec": False, "qwen_only_rec": False})
    for opq, s in qwen.items():
        cond, iid, seed = s["condition"], s["incident"], s["seed"]
        key = (cond, iid, seed)
        if s.get("RECONSTRUCTION") == 2:
            reached[key]["qwen_only_rec"] = True          # GPT-drop robustness (Qwen-alone)
            g = gpt.get(opq)
            if g and g.get("RECONSTRUCTION") == 2:
                reached[key]["rec"] = True                # consensus REC2
    # aggregate per (cond, incident): seeds reached
    incidents = sorted({s["incident"] for s in qwen.values()})
    conds = sorted({s["condition"] for s in qwen.values()})
    agg = {}  # (cond,inc) -> {seeds_reached, seeds_qwen}
    for cond in conds:
        for inc in incidents:
            sr = sum(1 for seed in range(M) if reached[(cond, inc, seed)]["rec"])
            sq = sum(1 for seed in range(M) if reached[(cond, inc, seed)]["qwen_only_rec"])
            agg[(cond, inc)] = {"seeds_reached": sr, "seeds_qwen": sq, "reach_rate": sr / M,
                                "incident_reached": sr >= math.ceil(M / 2)}
    # H_exhibit: R2 vs R0 per incident, binomial (null p = R0 reach-rate), Bonferroni /len(incidents)
    a_corr = alpha / len(incidents)
    hexb = []
    for inc in incidents:
        r0 = agg.get(("R0", inc), {"seeds_reached": 0, "reach_rate": 0.0})
        r2 = agg.get(("R2", inc), {"seeds_reached": 0, "reach_rate": 0.0, "incident_reached": False})
        p = binom_tail(r2["seeds_reached"], M, r0["reach_rate"])
        hexb.append({"incident": inc, "R0_reach": r0["reach_rate"], "R2_reach": r2["reach_rate"],
                     "R2_seeds": r2["seeds_reached"], "binom_p_vs_R0": p, "sig": p < a_corr,
                     "incident_reached": r2["incident_reached"], "H_exhibit_incident": r2["incident_reached"] and p < a_corr})
    H_exhibit = any(h["H_exhibit_incident"] for h in hexb)

    def rr(cond, inc): return agg.get((cond, inc), {"reach_rate": 0.0})["reach_rate"]
    out = {
        "object": "RECON_EXHIBIT_CONSENSUS", "M": M, "alpha": alpha, "bonferroni_alpha": a_corr,
        "consensus_rule": "REC2 = GPT RECON==2 AND Qwen RECON==2 (GPT-drop robust = Qwen-alone RECON==2 reported)",
        "per_condition_incident": {f"{c}|{i}": agg[(c, i)] for c in conds for i in incidents if (c, i) in agg},
        "H_exhibit_primary": {"confirmed": H_exhibit, "per_incident": hexb,
            "claim": "capability exhibit: R2 (frozen include-all mechanism) produces consensus-REC2 reconstructions of a hard-core incident above base R0. NO generalization/autonomy."},
        "H_scheduler_secondary": {inc: {"R4": rr("R4", inc), "R3": rr("R3", inc), "R_bon": rr("R_bon", inc),
            "R4_gt_max": rr("R4", inc) > max(rr("R3", inc), rr("R_bon", inc))} for inc in incidents},
        "H_structure_secondary": {inc: {lvl: rr(f"R5-{lvl}", inc) for lvl in ("L1", "L2", "L3")} for inc in incidents},
        "H_assist_secondary": {inc: {"R1": rr("R1", inc), "R3": rr("R3", inc), "R2": rr("R2", inc)} for inc in incidents},
        "caveats": ["consensus is GPT-bound (GPT strict binding, Qwen concurs)",
                    "reach-rates are at N=44; absolute values are N-dependent (do not over-read)",
                    "targets partly Claude-authored (contamination) -> non-load-bearing for the exhibit claim (DE-0123)",
                    "generalization (transfer/autonomy) NOT claimed -> FUTURE-SEALED"]}
    open(f"{EXP}/hbb_recon_exhibit_consensus.json", "w").write(json.dumps(out, ensure_ascii=False, indent=2))
    print("H_exhibit (primary) CONFIRMED:", H_exhibit)
    for h in hexb:
        print(f"  {h['incident']}: R2 {h['R2_seeds']}/{M} vs R0 {h['R0_reach']:.2f} | p={h['binom_p_vs_R0']:.4g} | exhibit={h['H_exhibit_incident']}")
    print("-> hbb_recon_exhibit_consensus.json")

if __name__ == "__main__":
    main()
