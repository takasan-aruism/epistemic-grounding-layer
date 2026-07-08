import json
CAND = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
scored = json.load(open("/home/takasan/egl/experiments/hbb_baseline_scored.json"))["depths"]
retally = json.load(open("/home/takasan/egl/experiments/hbb_F_origin_retally.json"))
C = {"HBB-02": 2, "HBB-09": 0, "HBB-14": 4, "HBB-16": 0, "HBB-22": 2, "HBB-23": 0, "HBB-25": 0, "HBB-26": 2,
     "HBB-07": 3, "HBB-15": 0, "HBB-18": 0, "HBB-19": 3, "HBB-20": 0, "HBB-27": 0, "HBB-28": 0, "HBB-29": 3}
Ft = retally["classification"]
main = [k for k in scored if k != "HBB-22"]
AA = [k for k in main if CAND[k]["intervention_scope"].startswith("ARUISM")]
FOS = [k for k in main if CAND[k]["intervention_scope"].startswith("FORCED")]
Fgen = {k: (scored[k]["F"] if Ft.get(k) == "TRANSFER" else 0) for k in scored}
def reach(d, ids): return sum(1 for k in ids if d[k] > 0)
print("### HBB per-incident A/B/F/C matrix (external-weight, deliverable ii) ★=AA external-spot target ###")
print("incident sc | A B Fapp Fgen C | breakthrough")
for k in sorted(scored):
    sc = CAND[k]["intervention_scope"][:2]; star = "*" if sc == "AR" else " "
    line = "  %s %s%s| %d %d %d(%s) %d %d | %s" % (k, sc, star, scored[k]["A"], scored[k]["B"], scored[k]["F"], Ft.get(k, "")[:4], Fgen[k], C[k], CAND[k]["breakthrough_structure"][:46])
    print(line)
A = {k: scored[k]["A"] for k in scored}; B = {k: scored[k]["B"] for k in scored}; Fa = {k: scored[k]["F"] for k in scored}
print("\nBreakthrough Reach (non-calib 15): A %d | B %d | F-apparent %d | F-genuine %d | C(AFE) %d" % (reach(A, main), reach(B, main), reach(Fa, main), reach(Fgen, main), reach(C, main)))
print("AA(6): A %d | B %d | F-app %d | F-genuine %d | C %d" % (reach(A, AA), reach(B, AA), reach(Fa, AA), reach(Fgen, AA), reach(C, AA)))
print("FOS(9): A %d | B %d | F-app %d | F-genuine %d | C %d" % (reach(A, FOS), reach(B, FOS), reach(Fa, FOS), reach(Fgen, FOS), reach(C, FOS)))
cb = [k for k in AA if B[k] > 0 or C[k] > 0]
print("AA reached by C or B (union): %d/6 %s" % (len(cb), cb))
print("AA C-unique (B missed): %s" % [k for k in AA if C[k] > 0 and B[k] == 0])
print("AA reached by NOBODY: %s" % [k for k in AA if A[k] == 0 and B[k] == 0 and Fgen[k] == 0 and C[k] == 0])
json.dump({"matrix": {k: {"A": scored[k]["A"], "B": scored[k]["B"], "F_apparent": scored[k]["F"], "F_class": Ft.get(k), "F_genuine": Fgen[k], "C_AFE": C[k], "scope": CAND[k]["intervention_scope"]} for k in scored},
          "reach": {"A": reach(A, main), "B": reach(B, main), "F_apparent": reach(Fa, main), "F_genuine": reach(Fgen, main), "C": reach(C, main)},
          "AA_reach": {"A": reach(A, AA), "B": reach(B, AA), "F_genuine": reach(Fgen, AA), "C": reach(C, AA)},
          "external_spot_targets_AA": AA, "scorer": "Claude external-weight; provenance recorded; external spot-check assumed (AA load-bearing)"},
          open("/home/takasan/egl/experiments/hbb_matrix.json", "w"), ensure_ascii=False, indent=2)
