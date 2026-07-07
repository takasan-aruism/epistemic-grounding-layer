#!/usr/bin/env python3
"""Meta-Frame deterministic gates + §28 failure-shape rejection tests。"""
import sys, metaframe as MF
R=[]
def ck(n,c): R.append((n,c)); print(f"  [{'PASS ✅' if c else 'FAIL ❌'}] {n}")
GOODINC={"incident_id":"INC-1","source_document":"/docs/概念理解.md","source_span_refs":["1388-1448"],
 "observation":"o","initial_interpretation":"i","tension_or_failure":"t","intervention":{"actor":"AUDIT"},
 "added_distinctions":[{"left":"apparent","relation":"!=","right":"real"}],"outcome":"o2","claim_after":"c2",
 "field_support":{"observation":"EXPLICIT","initial_interpretation":"EXPLICIT","tension_or_failure":"EXPLICIT","intervention":"EXPLICIT","outcome":"EXPLICIT"},
 "extraction_status":"CANDIDATE","origin":"CORPUS_EXTRACTION","corpus_tier":"TIER_1_RETROSPECTIVE_CORPUS","pre_frame_fidelity":"RETROSPECTIVE_RECONSTRUCTION"}
# incident
ck("valid incident → valid+eligible", MF.validate_incident(GOODINC)["valid"] and MF.validate_incident(GOODINC)["eligible"])
ck("non-CORPUS_EXTRACTION origin → invalid (§5)", not MF.validate_incident({**GOODINC,"origin":"HUMAN_LESSON"})["valid"])
ck("missing source_span → invalid (§9)", not MF.validate_incident({**GOODINC,"source_span_refs":[]})["valid"])
ck("INFERRED load-bearing w/o basis → invalid (§9)", not MF.validate_incident({**GOODINC,"field_support":{**GOODINC['field_support'],"tension_or_failure":"INFERRED"}})["valid"])
ck("TIER_1 w/o pre_frame_fidelity → invalid (§9.1)", not MF.validate_incident({k:v for k,v in GOODINC.items() if k!='pre_frame_fidelity'})["valid"])
ck("no added frame → eligible=False (§8 INELIGIBLE)", not MF.validate_incident({k:v for k,v in GOODINC.items() if k!='added_distinctions'})["eligible"])
# frame_delta
GOODFD={"frame_delta_id":"FD-1","incident_id":"INC-1","origin":"DERIVED_FROM_INCIDENT","decision_effect":"REVERSED",
 "pre_frame":{},"post_frame":{"added_distinctions":["apparent!=real"]}}
ck("valid frame_delta → valid", MF.validate_frame_delta(GOODFD,["INC-1"])["valid"])
ck("frame_delta on non-verified incident → invalid (§10)", not MF.validate_frame_delta(GOODFD,["INC-9"])["valid"])
ck("frame_delta no added post-frame → invalid", not MF.validate_frame_delta({**GOODFD,"post_frame":{}},["INC-1"])["valid"])
# meta_frame
GOODMF={"meta_frame_id":"MF-1","version":1,"name":"construction-artifact vs grounded finding",
 "derived_from_incidents":["INC-1","INC-2","INC-3"],"source_frame_delta_refs":["FD-1","FD-2","FD-3"],
 "shared_frame_delta":"surface result taken as grounded; construction/observation choice revealed as artifact; add apparent!=real; re-measure",
 "applicability_predicate":{"required_conditions":["a positive/structural result drives a claim","the result depends on a construction/observation choice not yet varied"],"disqualifying_conditions":["the construction choice was already varied/controlled"]},
 "suggested_axes":["vary the construction choice and re-measure","separate apparent from grounded"],
 "non_applicable_cases":["already controlled"],"origin":"INDUCED_FROM_INCIDENT_CLUSTER","status":"CANDIDATE"}
FDIDS=["FD-1","FD-2","FD-3"]; VIDS=["INC-1","INC-2","INC-3"]
ck("valid meta_frame → valid", MF.validate_meta_frame(GOODMF,VIDS,FDIDS)["valid"])
ck("<3 verified incidents → invalid (§18)", not MF.validate_meta_frame({**GOODMF,"derived_from_incidents":["INC-1","INC-2"]},VIDS,FDIDS)["valid"])
ck("MF-R6 human-origin laundering (wrong origin) → invalid", not MF.validate_meta_frame({**GOODMF,"origin":"HUMAN_LESSON"},VIDS,FDIDS)["valid"])
ck("no disqualifier/non-applicable → invalid (§18)", not MF.validate_meta_frame({**GOODMF,"applicability_predicate":{"required_conditions":["x"]},"non_applicable_cases":[]},VIDS,FDIDS)["valid"])
GENMF={**GOODMF,"name":"be skeptical and check assumptions","shared_frame_delta":"be skeptical","suggested_axes":[],"applicability_predicate":{"required_conditions":["any failure"]},"non_applicable_cases":[]}
ck("MF-R4 generic virtue → invalid (§18)", not MF.validate_meta_frame(GENMF,VIDS,FDIDS)["valid"])
ck("MF-R9 duplicate human heuristic → invalid", not MF.validate_meta_frame({**GOODMF,"name":"H-OPS-01 dependency check"},VIDS,FDIDS,existing_human_heuristics=["H-OPS-01"])["valid"])
# version lineage
ck("two CURRENT versions → invalid (§29 uniqueness)", not MF.validate_version_lineage([{"meta_frame_id":"MF-1","version":1,"status":"CURRENT"},{"meta_frame_id":"MF-1","version":2,"status":"CURRENT"}])["valid"])
ck("SUPERSEDED w/o superseded_by → invalid", not MF.validate_version_lineage([{"meta_frame_id":"MF-1","version":1,"status":"SUPERSEDED"}])["valid"])
ck("valid lineage (1 CURRENT, append-only) → valid", MF.validate_version_lineage([{"meta_frame_id":"MF-1","version":1,"status":"SUPERSEDED","superseded_by_version":2},{"meta_frame_id":"MF-1","version":2,"status":"CURRENT"}])["valid"])
if __name__=="__main__":
    print("=== Meta-Frame gates + §28 failure-shape rejection ===")
    f=[n for n,c in R if not c]; print(f"\n=== {len(R)-len(f)}/{len(R)} PASS ==="); sys.exit(1 if f else 0)
