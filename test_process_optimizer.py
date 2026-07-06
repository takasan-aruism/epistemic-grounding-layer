#!/usr/bin/env python3
"""§11/§12/§13 Process Optimizer deterministic contracts の test。"""
import sys, process_optimizer as PO
R=[]
def ck(n,c): R.append((n,c)); print(f"  [{'PASS ✅' if c else 'FAIL ❌'}] {n}")

# §11 versioning / review candidates
cur=PO.current_property_set()
ck("§11 current property-set = v1, P1-P7", cur["process_property_set_version"]==1 and len(cur["properties"])==7)
# simulate: an optimization preserved against v1; current still v1 -> no review needed
ck("§11 preserved_against=current → no review candidate", PO.review_candidates([{"id":"OPT-1","preserved_against_property_set_version":1}])==[])
ck("§11 preserved_against=None → review candidate (unreviewed props)", len(PO.review_candidates([{"id":"OPT-0","preserved_against_property_set_version":None}]))==1)

# §12 preservation review
full=[{"property_id":p["id"],"verdict":"PRESERVED","mechanism_ref":"DW gate"} for p in cur["properties"]]
ck("§12 全 PRESERVED + mechanism_ref → auto_adoptable", PO.validate_preservation_review({"property_verdicts":full})["auto_adoptable"])
ck("§12 missing property entry → not adoptable (missing != PRESERVED)", not PO.validate_preservation_review({"property_verdicts":full[:-1]})["auto_adoptable"])
weak=[dict(x) for x in full]; weak[0]["verdict"]="WEAKENED"
ck("§12 WEAKENED → not adoptable", not PO.validate_preservation_review({"property_verdicts":weak})["auto_adoptable"])
unk=[dict(x) for x in full]; unk[1]["verdict"]="UNKNOWN"
ck("§12 UNKNOWN → not adoptable", not PO.validate_preservation_review({"property_verdicts":unk})["auto_adoptable"])
noref=[dict(x) for x in full]; noref[0].pop("mechanism_ref")
ck("§12 PRESERVED without mechanism_ref → not adoptable", not PO.validate_preservation_review({"property_verdicts":noref})["auto_adoptable"])
ck("§12 malformed verdict → fail-closed", not PO.validate_preservation_review({"property_verdicts":[{"property_id":"P1","verdict":"MAYBE"}]})["auto_adoptable"])
ck("§12 non-dict review → fail-closed", not PO.validate_preservation_review("x")["auto_adoptable"])

# §13 native capability
ck("§13 ESTABLISHED + egl ref → established, no research", PO.validate_native_capability({"coverage_status":"ESTABLISHED","component":"vLLM","blocked_property":"model resume","egl_record_ref":"DE-0099"})["effective_status"]=="ESTABLISHED")
r=PO.validate_native_capability({"coverage_status":"ESTABLISHED","component":"vLLM","blocked_property":"model resume"})
ck("§13 ESTABLISHED without egl ref → NOT_ESTABLISHED + research_need (self-report 禁止)", r["effective_status"]=="NOT_ESTABLISHED" and r["research_need"])
ck("§13 NOT_ESTABLISHED → research_need", PO.validate_native_capability({"coverage_status":"NOT_ESTABLISHED","component":"vLLM","blocked_property":"x"})["research_need"])
ck("§13 non-dict → fail-closed NOT_ESTABLISHED", PO.validate_native_capability(None)["effective_status"]=="NOT_ESTABLISHED")

if __name__=="__main__":
    print("=== §11/§12/§13 Process Optimizer contracts ===")
    f=[n for n,c in R if not c]; print(f"\n=== {len(R)-len(f)}/{len(R)} PASS ==="); sys.exit(1 if f else 0)
