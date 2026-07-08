#!/usr/bin/env python3
"""N=13 two-axis MULTI_SCORER_CONSENSUS.
Two independent 2-axis scorers: GPT rubric-v2 and Qwen rubric-v2 (both frozen-rubric).
Granularity = per (incident, arm), best-across-rungs (matches GPT incident_arm_summary + the C-unique /
hard-core questions). Consensus reach = BOTH scorers agree at the threshold. Claude (author of C/D) is
NOT a scorer here; HBB-04/30 scored by {Qwen, GPT} only (Claude 当事者 excluded)."""
import json, hashlib
from pathlib import Path
EXP = "/home/takasan/egl/experiments"

# ---- scope per incident ----
CAND = {x["id"]: x for x in json.load(open(f"{EXP}/hbb_candidates.json"))["candidates"]}
def scope(i): return CAND[i]["intervention_scope"]

# ---- GPT best per (incident,arm) ----
gpt_scores = json.load(open(f"{EXP}/HBB_GPT_v2_scores.json"))
gpt_best = {}  # (inc,arm) -> {"det":x,"rec":y}
for row in gpt_scores["incident_arm_summary"]:   # the 11
    gpt_best[(row["incident_id"], row["arm"])] = {"det": row["best_DETECTION"], "rec": row["best_RECONSTRUCTION"]}

# 04/30: map opaque_id -> (inc,arm,rung) from run cells, then best per (inc,arm)
R = json.load(open(f"{EXP}/hbb_sealed_run.json"))["results"]
opq2cell = {hashlib.sha256(f"{r['id']}|{r['arm']}|{r['rung']}".encode()).hexdigest()[:12]: (r["id"], r["arm"], r["rung"]) for r in R}
ret = json.load(open(f"{EXP}/HBB_GPT_v2_scores_04_30_return.json"))
gpt_0430 = {}
for it in ret:
    inc, arm, rung = opq2cell[it["opaque_id"]]
    k = (inc, arm)
    b = gpt_0430.setdefault(k, {"det": 0, "rec": 0})
    b["det"] = max(b["det"], it["DETECTION"]); b["rec"] = max(b["rec"], it["RECONSTRUCTION"])
gpt_best.update(gpt_0430)

# ---- Qwen best per (incident,arm) ----
qwen = json.load(open(f"{EXP}/hbb_qwen_v2_scores.json"))["scores"]
qwen_best = {}
for s in qwen:
    k = (s["id"], s["arm"])
    b = qwen_best.setdefault(k, {"det": 0, "rec": 0})
    b["det"] = max(b["det"], s["DETECTION"]); b["rec"] = max(b["rec"], s["RECONSTRUCTION"])

INC = sorted({i for (i, a) in gpt_best})
ARMS = ["A", "B", "C", "D", "F"]
AA = [i for i in INC if scope(i).startswith("ARUISM")]
FOS = [i for i in INC if i not in AA]

# ---- consensus per (incident,arm) ----
cons = {}
for i in INC:
    for a in ARMS:
        g = gpt_best.get((i, a), {"det": 0, "rec": 0}); q = qwen_best.get((i, a), {"det": 0, "rec": 0})
        cons[(i, a)] = {
            "gpt_det": g["det"], "gpt_rec": g["rec"], "qwen_det": q["det"], "qwen_rec": q["rec"],
            "consensus_DET2": g["det"] == 2 and q["det"] == 2,
            "consensus_REC2": g["rec"] == 2 and q["rec"] == 2,
            "consensus_DET_ge1": g["det"] >= 1 and q["det"] >= 1,
            "consensus_REC_ge1": g["rec"] >= 1 and q["rec"] >= 1,
        }

def reach(arm, subset, key):
    return sorted([i for i in subset if cons[(i, arm)][key]])

# ---- per-arm consensus reconstruction reach (strict REC2) ----
rec2 = {a: {"AA": reach(a, AA, "consensus_REC2"), "FOS": reach(a, FOS, "consensus_REC2"), "ALL": reach(a, INC, "consensus_REC2")} for a in ARMS}
det2 = {a: {"AA": reach(a, AA, "consensus_DET2"), "FOS": reach(a, FOS, "consensus_DET2"), "ALL": reach(a, INC, "consensus_DET2")} for a in ARMS}
rec1 = {a: {"ALL": reach(a, INC, "consensus_REC_ge1")} for a in ARMS}
det1 = {a: {"ALL": reach(a, INC, "consensus_DET_ge1")} for a in ARMS}

B = set(rec2["B"]["AA"]); C = set(rec2["C"]["AA"]); D = set(rec2["D"]["AA"])
C_unique_AA = sorted(C - B); D_unique_AA = sorted(D - B)
Ball = set(rec2["B"]["ALL"]); Call = set(rec2["C"]["ALL"]); Dall = set(rec2["D"]["ALL"])
C_unique_ALL = sorted(Call - Ball); D_unique_ALL = sorted(Dall - Ball)

# ---- robust hard-core: incidents with ZERO consensus REC2 across ALL arms ----
hard_core_rec = sorted([i for i in INC if not any(cons[(i, a)]["consensus_REC2"] for a in ARMS)])
# of those, which had SOME consensus detection (detected-but-not-reconstructed) vs fully missed
hc_detected = sorted([i for i in hard_core_rec if any(cons[(i, a)]["consensus_DET_ge1"] for a in ARMS)])
hc_fully_missed = sorted([i for i in hard_core_rec if i not in hc_detected])

# ---- B detection->reconstruction gap (consensus) ----
B_gap = {"DET2_incidents": sorted(det2["B"]["ALL"]), "REC2_incidents": sorted(rec2["B"]["ALL"]),
         "DET_ge1_incidents": sorted(det1["B"]["ALL"]), "REC_ge1_incidents": sorted(rec1["B"]["ALL"])}

out = {
  "object": "HBB_N13_TWO_AXIS_MULTI_SCORER_CONSENSUS",
  "scorers": ["GPT rubric-v2 (incident_arm_summary for 11 + 04/30 return)", "Qwen rubric-v2 (all 13, blind)"],
  "claude_role": "author of arms C/D; NOT a scorer. HBB-04/30 scored by {Qwen, GPT} only (当事者 excluded).",
  "granularity": "per (incident, arm), best-across-rungs",
  "rubric_sha256": "012941aba485f33b8328b7e5cba2a84b5c1db82119bb96554bc8dea84f4f9f17",
  "N": len(INC), "incidents": INC, "AA": AA, "FOS": FOS,
  "consensus_REC2_reach": {a: {k: v for k, v in rec2[a].items()} for a in ARMS},
  "consensus_DET2_reach": {a: {k: v for k, v in det2[a].items()} for a in ARMS},
  "counts_REC2": {a: {"AA": len(rec2[a]["AA"]), "FOS": len(rec2[a]["FOS"]), "ALL": len(rec2[a]["ALL"])} for a in ARMS},
  "counts_DET2": {a: {"AA": len(det2[a]["AA"]), "FOS": len(det2[a]["FOS"]), "ALL": len(det2[a]["ALL"])} for a in ARMS},
  "C_unique_AA": C_unique_AA, "D_unique_AA": D_unique_AA,
  "C_unique_ALL": C_unique_ALL, "D_unique_ALL": D_unique_ALL,
  "B_detection_reconstruction_gap": B_gap,
  "robust_hard_core_no_consensus_REC2": hard_core_rec,
  "hard_core_detected_not_reconstructed": hc_detected,
  "hard_core_fully_missed": hc_fully_missed,
  "per_incident_arm": {f"{i}|{a}": cons[(i, a)] for i in INC for a in ARMS},
}
Path(f"{EXP}/hbb_n13_consensus.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

# ---- print summary ----
print("N =", len(INC), "| AA:", AA, "| FOS:", FOS)
print("\nconsensus REC2 (both scorers best_REC==2) reach counts  [AA / FOS / ALL]:")
for a in ARMS:
    print(f"  {a}: {len(rec2[a]['AA'])}/{len(AA)}  {len(rec2[a]['FOS'])}/{len(FOS)}  {len(rec2[a]['ALL'])}/{len(INC)}   REC2 incidents(ALL)= {rec2[a]['ALL']}")
print("\nconsensus DET2 reach counts  [AA / FOS / ALL]:")
for a in ARMS:
    print(f"  {a}: {len(det2[a]['AA'])}/{len(AA)}  {len(det2[a]['FOS'])}/{len(FOS)}  {len(det2[a]['ALL'])}/{len(INC)}")
print("\nC_unique_AA:", C_unique_AA, "| D_unique_AA:", D_unique_AA)
print("C_unique_ALL:", C_unique_ALL, "| D_unique_ALL:", D_unique_ALL)
print("\nB consensus DET2 incidents:", B_gap["DET2_incidents"], f"(n={len(B_gap['DET2_incidents'])})")
print("B consensus REC2 incidents:", B_gap["REC2_incidents"], f"(n={len(B_gap['REC2_incidents'])})")
print("B consensus DET>=1 incidents:", len(B_gap["DET_ge1_incidents"]), "| REC>=1:", len(B_gap["REC_ge1_incidents"]))
print("\nrobust hard-core (no consensus REC2 by any arm):", hard_core_rec)
print("  detected-not-reconstructed:", hc_detected)
print("  fully-missed:", hc_fully_missed)
print("\n-> hbb_n13_consensus.json")
