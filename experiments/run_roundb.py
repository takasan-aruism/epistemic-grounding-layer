#!/usr/bin/env python3
"""Round B pair design: 同一 verified incident を CONCRETE(domain名詞込み)vs ABSTRACT(MASK_PIPELINE v1)で提示。
主RQ: 抽象化は concrete retrieval より cross-domain literal misfire を減らすか、有用情報をどれだけ失うか。
N=15(5 domain×3)。leak制御 pre-frame。3条件 ordinary / concrete / abstract。複合スコア作らない。"""
import json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import metaframe_mask as MP
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, seed=0, mt=280):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jl(t):
    i, j = t.find("["), t.rfind("]")
    try: return json.loads(t[i:j+1]) if 0<=i<j else [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]
    except Exception: return [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]

# retrieved ESDE incidents (concrete, heavy domain nouns)。abstract は MASK_PIPELINE v1 で生成(手書きしない)。
RETRIEVED = {
 "INC-02": "In v9.11 a label finding (n=2 core dominant, 67%) was taken as real structure. A Step-0 audit found 99.64% of links never reach R>0 and 2/3 of labels were R=0-contaminated apparent structure. The distinction apparent-structure != grounded-structure was added; re-measuring with birth-time R>0 purity showed n=2 dominance was an artifact and n=5 became modal.",
 "INC-11": "A CidSelfBuffer with a fixed 50-step pulse produced a result read as 'the CID knows change' (self-awareness). Taka noted the Fetch timing was FIXED at 50 steps, so the researcher was still controlling the read; the apparent self-awareness was an artifact of the fixed-interval construction. Distinction researcher-controlled-timing != event-driven was added; it moved to event-driven reads.",
 "INC-16": "E3_contact events showed 77% one-way firing in the main run (vs 25.6% in the smoke run). Code A investigated the firing condition and found the 77% came from ghost accumulation over tracking length (one CID already retired). The surprising metric was explained by a construction/accumulation effect, not a mechanism property.",
}
# 15 held-out(5 domain×3)。missing_axis = 実際に後で追加された decision-relevant 軸。retr=引く ESDE incident。
HELDOUT = [
 # data interpretation
 {"id":"B01","domain":"data","retr":"INC-02","pre":"A dashboard reports that a marketing campaign had no average effect on signups. Should we conclude it didn't work? What to check?","axis":"Is the null AVERAGE hiding heterogeneous subgroups? Disaggregate / stratify before concluding no effect (averaging artifact)."},
 {"id":"B02","domain":"data","retr":"INC-16","pre":"An A/B test shows a striking 40% lift in the treatment. Propose what to check before shipping.","axis":"Is the 40% an artifact of the experimental setup (sample ratio mismatch, novelty/seasonality, selection)? Confirm the mechanism before treating the number as the effect."},
 {"id":"B03","domain":"data","retr":"INC-11","pre":"A clustering run produced 5 clean clusters. Propose what to check before treating them as real groups.","axis":"Are the clusters an artifact of the algorithm/parameter choice (k, distance, seed)? Vary the construction and check stability before treating clusters as real structure."},
 # software validator
 {"id":"B04","domain":"software","retr":"INC-02","pre":"A code auditor returned several findings on a validator that passed all its load-bearing tests. Rework based on them? What to check?","axis":"Is each finding substantiated by a reproducing counterexample, or an over-flag? Disposition before rework; reject findings that don't reproduce."},
 {"id":"B05","domain":"software","retr":"INC-11","pre":"A gate passes its 7 supplied tests and the auditor found nothing. Ready to ship? What to check?","axis":"Do the supplied tests cover all malformed shapes? The tested surface may be narrower than the claimed property (fail-open on an untested shape)."},
 {"id":"B06","domain":"software","retr":"INC-16","pre":"A service shows 99.9% success in monitoring. Propose what to check before claiming it is reliable.","axis":"Is 99.9% an artifact of what the monitor counts (transport success != content/task success)? Confirm the metric definition before treating it as reliability."},
 # GPU / infra
 {"id":"B07","domain":"gpu","retr":"INC-02","pre":"Vendor docs document a capability with 'fast resume'. We want it to cut model-switch cost. What to check before adopting?","axis":"Does the SPECIFIED capability actually work/perform in OUR local config? Docs give no local numbers; measure locally (spec != local applicability)."},
 {"id":"B08","domain":"gpu","retr":"INC-16","pre":"Two models are said to be un-co-servable on our GPUs so we must pick an operating mode. What to check before choosing?","axis":"The co-serve impossibility is a DECLARED assertion, not measured — measure it first; and the mode choice depends on an unmeasured variable (swap frequency)."},
 {"id":"B09","domain":"gpu","retr":"INC-11","pre":"A benchmark shows our new kernel is 3x faster. Propose what to check before reporting the speedup.","axis":"Is the 3x an artifact of the benchmark setup (warmup, batch, cache, fixed input)? Vary the setup and measure under real conditions."},
 # workflow / agent
 {"id":"B10","domain":"workflow","retr":"INC-11","pre":"An agent's plan passed the reviewer and all steps executed. Ship the output? What to check?","axis":"Did the reviewer/steps actually exercise the load-bearing property, or is 'passed' an artifact of a weak/self review? Check the review's independence and coverage."},
 {"id":"B11","domain":"workflow","retr":"INC-02","pre":"An automated audit of our pipeline found zero issues. Propose what to check before trusting it.","axis":"Is 'zero issues' grounded, or an artifact of the audit not covering the real failure modes? Attack the audit's coverage before trusting the null."},
 {"id":"B12","domain":"workflow","retr":"INC-16","pre":"Batching cut our run time by half in one trial. Propose what to check before adopting batching.","axis":"Is the 50% saving representative or an artifact of the one trial's conditions (rework frequency, task mix)? Measure across varied conditions before adopting."},
 # ESDE
 {"id":"B13","domain":"esde","retr":"INC-02","pre":"A run shows axis contribution is 73% phase+r dominant. Propose what to check before treating it as the system's structure.","axis":"Is the 73% dominance a composition/construction artifact (subset mixing, contamination)? Re-measure under a purified construction before treating it as structure."},
 {"id":"B14","domain":"esde","retr":"INC-16","pre":"A metric jumped from 25% to 77% between short and long runs. Propose what to check before treating 77% as a property.","axis":"Is the jump a property of the mechanism or an artifact of run length/accumulation? Confirm the generating condition before treating the metric as a finding."},
 {"id":"B15","domain":"esde","retr":"INC-11","pre":"A fixed-interval readout suggests the unit tracks its own change. Propose what to check before claiming self-tracking.","axis":"Is 'self-tracking' an artifact of the fixed interval (researcher-controlled timing)? Make the readout event-driven/unpredictable before claiming genuine self-tracking."},
]

BASE = "Propose AT MOST 3 concrete research/audit axes (things to check/measure) for the situation. Return ONLY a JSON list of short strings."
def conds(ho):
    r = RETRIEVED[ho["retr"]]
    return {
     "ordinary": ho["pre"],
     "concrete": f"A relevant past incident: {r}\n\nUsing it if helpful:\n{ho['pre']}",
     "abstract": f"A relevant past incident (abstracted): {MP.abstract_incident(r)}\n\nUsing it if helpful:\n{ho['pre']}",
    }

def main():
    out = {"mask_pipeline": MP.VERSION, "heldout": []}
    for ho in HELDOUT:
        rec = {"id": ho["id"], "domain": ho["domain"], "retr": ho["retr"], "missing_axis": ho["axis"], "axes": {}}
        for cond, u in conds(ho).items():
            rec["axes"][cond] = jl(chat(BASE, u, seed=0))
        out["heldout"].append(rec)
        print(f"[{ho['id']} {ho['domain']}] done", flush=True)
    Path("/home/takasan/egl/experiments/roundb_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n-> roundb_run.json 保存。次: blind score(XDOMAIN/HIT等)")

if __name__ == "__main__":
    main()
