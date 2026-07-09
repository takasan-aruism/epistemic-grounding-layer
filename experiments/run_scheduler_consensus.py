#!/usr/bin/env python3
"""Scheduler-exhibit consensus + hypotheses (spec v0.1). Same consensus rule as the frozen exhibit:
REC2 = GPT RECON==2 AND Qwen RECON==2 (Claude excluded). per (cond,inc,seed) reached = >=1 candidate consensus
REC2; reach-rate over M; incident-reached = >= ceil(M/2). PRIMARY H_sched_exhibit = RS reach > R0 (binomial,
alpha=0.05, Bonferroni/3). SECONDARY H_independence = RS vs RS_pool; H_compare_rebuild = RS vs RS_flat.
GPT-drop caveat: Qwen-alone REC2 reported. If GPT return absent, computes Qwen-alone only and flags."""
import json, sys, math
from collections import defaultdict
EXP = "/home/takasan/egl/experiments"

def binom_tail(k, n, p):
    if p <= 0: return 1.0 if k == 0 else 0.0
    if p >= 1: return 1.0
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def main():
    qfile = sys.argv[1] if len(sys.argv) > 1 else f"{EXP}/scheduler_qwen_scores.json"
    gfile = sys.argv[2] if len(sys.argv) > 2 else None      # GPT return (optional; Qwen-alone if missing)
    M = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    alpha = 0.05
    qwen = {s["opaque_id"]: s for s in json.load(open(qfile))["scores"]}
    gpt = {}
    if gfile:
        gr = json.load(open(gfile)); gr = gr if isinstance(gr, list) else gr.get("scores", gr.get("items", []))
        gpt = {g["opaque_id"]: g for g in gr}
    have_gpt = bool(gpt)
    reached = defaultdict(lambda: {"rec": False, "qwen_only": False})
    for opq, s in qwen.items():
        key = (s["condition"], s["incident"], s["seed"])
        if s.get("RECONSTRUCTION") == 2:
            reached[key]["qwen_only"] = True
            g = gpt.get(opq)
            if (not have_gpt) or (g and g.get("RECONSTRUCTION") == 2):
                reached[key]["rec"] = True      # consensus (or Qwen-alone if no GPT yet)
    incidents = sorted({s["incident"] for s in qwen.values()})
    conds = sorted({s["condition"] for s in qwen.values()})
    agg = {}
    for c in conds:
        for inc in incidents:
            sr = sum(1 for seed in range(M) if reached[(c, inc, seed)]["rec"])
            sq = sum(1 for seed in range(M) if reached[(c, inc, seed)]["qwen_only"])
            agg[(c, inc)] = {"seeds_reached": sr, "seeds_qwen": sq, "reach_rate": sr / M,
                             "incident_reached": sr >= math.ceil(M / 2)}

    def rr(c, inc): return agg.get((c, inc), {"reach_rate": 0.0})["reach_rate"]
    def sd(c, inc): return agg.get((c, inc), {"seeds_reached": 0})["seeds_reached"]
    a_corr = alpha / len(incidents)

    def test(primary, base):     # primary reach > base reach, binomial (null p = base reach-rate)
        rows = []
        for inc in incidents:
            p = binom_tail(sd(primary, inc), M, rr(base, inc))
            reached_ok = agg.get((primary, inc), {"incident_reached": False})["incident_reached"]
            rows.append({"incident": inc, f"{primary}_seeds": sd(primary, inc), f"{primary}_reach": rr(primary, inc),
                         f"{base}_reach": rr(base, inc), "binom_p": p, "sig": p < a_corr,
                         "incident_reached": reached_ok, "hyp_incident": reached_ok and p < a_corr})
        return {"rows": rows, "confirmed": any(r["hyp_incident"] for r in rows)}

    H_exhibit = test("RS", "R0")
    H_indep = test("RS", "RS_pool")
    H_cmp = test("RS", "RS_flat")
    out = {"object": "SCHEDULER_EXHIBIT_CONSENSUS", "M": M, "alpha": alpha, "bonferroni_alpha": a_corr,
           "consensus_rule": ("REC2 = GPT RECON==2 AND Qwen RECON==2" if have_gpt else "QWEN-ALONE (GPT return not yet integrated)"),
           "gpt_integrated": have_gpt,
           "per_condition_incident": {f"{c}|{i}": agg[(c, i)] for c in conds for i in incidents if (c, i) in agg},
           "H_sched_exhibit_PRIMARY": {**H_exhibit, "claim": "capability exhibit: a faithful STOP-SHIFT-RUN-COMPARE scheduler (RS) produces consensus-REC2 reconstructions of a hard-core incident above base R0. NOT generalization/autonomy/cognition."},
           "H_independence_SECONDARY": {**H_indep, "reads": "RS > RS_pool => independence / non-accumulation is an active ingredient"},
           "H_compare_rebuild_SECONDARY": {**H_cmp, "reads": "RS > RS_flat => compare + rebuild-from-differences is an active ingredient"},
           "caveats": ["consensus GPT-bound when integrated (Qwen-alone reported as GPT-drop reference)",
                       "reach-rates are at N per cell; absolute values N-dependent",
                       "capability-exhibit only; cognition claim quarantined (v0.1); transfer/autonomy FUTURE-SEALED",
                       "DE-0127 exhibit untouched; this is a distinct instrument"]}
    Path = __import__("pathlib").Path
    Path(f"{EXP}/scheduler_exhibit_consensus.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    tag = "CONSENSUS" if have_gpt else "QWEN-ALONE (provisional)"
    print(f"[{tag}] H_sched_exhibit PRIMARY confirmed:", H_exhibit["confirmed"])
    for r in H_exhibit["rows"]:
        print(f"  {r['incident']}: RS {r['RS_seeds']}/{M} (rr={r['RS_reach']:.2f}) vs R0 {r['R0_reach']:.2f} | p={r['binom_p']:.4g} | exhibit={r['hyp_incident']}")
    print("H_independence (RS>RS_pool):", H_indep["confirmed"], "| H_compare_rebuild (RS>RS_flat):", H_cmp["confirmed"])
    print("-> scheduler_exhibit_consensus.json")

if __name__ == "__main__":
    main()
