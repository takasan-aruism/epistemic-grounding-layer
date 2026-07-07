#!/usr/bin/env python3
"""Round B blind score。condition 匿名化 + hash-shuffle。Qwen scorer が固定 rubric で採点。
主指標 XDOMAIN_MISFIRE / DOMAIN_LITERALIZATION、cost HIT/PARTIAL/MISS/USEFUL_AXIS、harm OVER_TRIGGER/IRRELEVANT。複合スコア無し。"""
import json, sys, hashlib, urllib.request
from pathlib import Path
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, seed=0, mt=220):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0<=i<j else None
    except Exception: return None

RUBRIC = ("You score proposed research/audit axes for a SITUATION against a TARGET missing axis. You do NOT know "
    "which method produced them. Return ONLY JSON {\"recovery\":\"HIT|PARTIAL|MISS\",\"useful_axis\":true|false,"
    "\"flags\":[...]}. recovery: HIT=axes specifically recover the TARGET axis; PARTIAL=vaguely; MISS=no. "
    "useful_axis: true if at least one axis is genuinely useful for THIS situation. flags (0+): "
    "\"XDOMAIN_MISFIRE\"=axes import concepts/terms from an unrelated domain (e.g. simulation/biology/quantum "
    "terms like CID, R=0, label-contamination, ghost, node/link, birth-mode, into a software/GPU/data/marketing "
    "problem); \"DOMAIN_LITERALIZATION\"=axes literally transplant a specific past mechanism onto the new domain "
    "where it does not belong; \"OVER_TRIGGER\"=force an abstract framework clearly irrelevant here; "
    "\"IRRELEVANT_AXIS\"=one+ axes unrelated to the problem. Judge on merit vs THIS situation and target only.")

def main():
    run = json.load(open("/home/takasan/egl/experiments/roundb_run.json"))["heldout"]
    items = []
    for h in run:
        for cond, axes in h["axes"].items():
            aid = "Q-" + hashlib.sha256(f"{h['id']}|{cond}".encode()).hexdigest()[:5]
            items.append({"anon": aid, "_id": h["id"], "_cond": cond, "domain": h["domain"], "target": h["missing_axis"], "axes": axes})
    items.sort(key=lambda x: x["anon"])  # shuffle by hash
    from run_roundb import HELDOUT
    pf = {h["id"]: h["pre"] for h in HELDOUT}
    conds = ["ordinary", "concrete", "abstract"]
    tally = {c: {"HIT":0,"PARTIAL":0,"MISS":0,"USEFUL":0,"XDOMAIN_MISFIRE":0,"DOMAIN_LITERALIZATION":0,"OVER_TRIGGER":0,"IRRELEVANT_AXIS":0} for c in conds}
    scored = []
    for it in items:
        u = f"SITUATION ({it['domain']} domain): {pf[it['_id']]}\nTARGET_AXIS: {it['target']}\nPROPOSED_AXES ({it['anon']}): {json.dumps(it['axes'],ensure_ascii=False)}\n\nReturn the JSON."
        s = jx(chat(RUBRIC, u, seed=0)) or {"recovery":"MISS","useful_axis":False,"flags":[]}
        scored.append({**{k:it[k] for k in ('anon','_id','_cond','domain')}, "score":s})
        c = it["_cond"]; tally[c][s.get("recovery","MISS")] += 1
        if s.get("useful_axis"): tally[c]["USEFUL"] += 1
        for f in s.get("flags",[]):
            if f in tally[c]: tally[c][f] += 1
    Path("/home/takasan/egl/experiments/roundb_scored.json").write_text(json.dumps({"scorer":"Qwen3.6 blind (condition非開示)","scored":scored,"tally":tally},ensure_ascii=False,indent=2))
    print("### Round B blind score (Qwen, condition非開示) N=15 ###")
    print("condition  HIT PART MISS USEFUL | XDOMAIN DOM_LIT OVER IRREL")
    for c in conds:
        t=tally[c]; print(f"  {c:<9} {t['HIT']:>3} {t['PARTIAL']:>4} {t['MISS']:>4} {t['USEFUL']:>6} | {t['XDOMAIN_MISFIRE']:>7} {t['DOMAIN_LITERALIZATION']:>7} {t['OVER_TRIGGER']:>4} {t['IRRELEVANT_AXIS']:>5}")
    print("\n[主仮説] abstract の XDOMAIN+DOM_LIT < concrete か? / HIT は concrete と同等か?")

if __name__ == "__main__":
    main()
