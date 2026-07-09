#!/usr/bin/env python3
"""Build the GPT handoff for the recon-exhibit. Consensus REC2 = GPT ∧ Qwen (both RECON==2), so ONLY candidates
Qwen already scored RECON==2 need GPT scoring (Qwen-rejected candidates cannot be consensus-certified). This
shrinks the handoff faithfully (no-author-selection preserved: Qwen is a target-blind scorer, not the author).
Blind: condition withheld; opaque_id keyed = sha256(incident|condition|seed|cand_idx)[:14]; incident+target shown."""
import json, sys, hashlib
from pathlib import Path
EXP = "/home/takasan/egl/experiments"
CAND = {x["id"]: x for x in json.load(open(f"{EXP}/hbb_candidates.json"))["candidates"]}

def main():
    cfile = sys.argv[1] if len(sys.argv) > 1 else f"{EXP}/hbb_recon_exhibit_candidates.json"
    qfile = sys.argv[2] if len(sys.argv) > 2 else f"{EXP}/hbb_recon_qwen_scores.json"
    out = sys.argv[3] if len(sys.argv) > 3 else f"{EXP}/hbb_recon_gpt_handoff.json"
    doc = json.load(open(cfile))
    qwen = {s["opaque_id"]: s for s in json.load(open(qfile))["scores"]}
    # candidate text lookup by opaque_id
    text = {}
    for r in doc["records"]:
        for k, c in enumerate(r["candidates"]):
            opq = hashlib.sha256(f"{r['incident']}|{r['condition']}|{r['seed']}|{k}".encode()).hexdigest()[:14]
            text[opq] = (r["incident"], c)
    items = []
    incidents = set()
    for opq, s in qwen.items():
        if s.get("RECONSTRUCTION") == 2:          # only Qwen-REC2 candidates need GPT (consensus = both)
            iid, c = text[opq]; incidents.add(iid)
            items.append({"opaque_id": opq, "incident_id": iid, "candidate": c[:700]})
    items.sort(key=lambda x: x["opaque_id"])
    inc = {i: {"historical_target": CAND[i]["breakthrough_structure"]} for i in incidents}
    Path(out).write_text(json.dumps({
        "object": "RECON_GPT_HANDOFF",
        "rubric_sha256": "012941aba485f33b8328b7e5cba2a84b5c1db82119bb96554bc8dea84f4f9f17",
        "scoring_instruction": ("Score each candidate on DETECTION (0/1/2) and RECONSTRUCTION (0/1/2) per the frozen "
            "rubric v2. Condition is withheld (blind); judge content only. Use per-incident 'historical_target' ONLY "
            "as the RECONSTRUCTION reference. Return a JSON array of {\"opaque_id\":...,\"DETECTION\":0|1|2,\"RECONSTRUCTION\":0|1|2}."),
        "note": ("Only candidates Qwen already scored RECONSTRUCTION==2 are here; consensus REC2 = GPT ∧ Qwen. "
                 "Claude re-derives condition/seed locally on return via opaque_id. Do NOT return condition."),
        "incidents": inc, "n_items": len(items), "items": items}, ensure_ascii=False, indent=2))
    print(f"-> {out} | {len(items)} candidates for GPT (Qwen-REC2 subset) over {len(incidents)} incidents")

if __name__ == "__main__":
    main()
