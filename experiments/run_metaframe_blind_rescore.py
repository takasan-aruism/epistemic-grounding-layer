#!/usr/bin/env python3
"""PHASE 1: 現 pilot の blind rescore。条件label除去 + hash-shuffle 匿名化。
固定 rubric で genuinely-blind scorer(Qwen、condition非開示・私の仮説非開示)が採点。
T2(artifact candidate)の cross-domain safety signal(3HIT/0XDOMAIN/0over-trigger)が残るか確認。"""
import json, sys, hashlib, urllib.request
from pathlib import Path
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, seed=0, mt=250):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j + 1]) if 0 <= i < j else None
    except Exception: return None

RUBRIC = ("You score proposed research/audit axes against a TARGET missing axis. You do NOT know which method "
    "produced them. Return ONLY JSON {\"recovery\":\"HIT|PARTIAL|MISS\",\"flags\":[...]}. recovery: HIT = the "
    "proposed axes specifically recover the TARGET axis (the decision-relevant check); PARTIAL = they touch it "
    "vaguely; MISS = they do not. flags (0+): \"XDOMAIN\" = axes literally import concepts from an unrelated domain "
    "(e.g. quantum/qubit/physics/biology terms applied to a software/GPU problem); \"OVER_TRIGGER\" = axes force an "
    "abstract framework clearly irrelevant to THIS situation; \"IRRELEVANT_AXIS\" = one or more axes are unrelated "
    "to the problem. Judge the axes on merit vs the target and situation only.")

def main():
    ho = json.load(open("/home/takasan/egl/experiments/metaframe_heldout.json"))["heldout"]
    # 匿名化 + hash-shuffle(RNG 不使用、決定的)
    items = []
    for h in ho:
        for cond, axes in h["axes"].items():
            aid = "R-" + hashlib.sha256(f"{h['id']}|{cond}".encode()).hexdigest()[:4]
            items.append({"anon_id": aid, "_ho": h["id"], "_cond": cond, "missing_axis": h["missing_axis"],
                          "pre_frame_of": h["id"], "axes": axes})
    from run_metaframe_heldout import HELDOUT
    pf = {h["id"]: h["pre_frame"] for h in HELDOUT}
    items.sort(key=lambda x: x["anon_id"])  # shuffle by hash
    scored = []
    for it in items:
        u = (f"SITUATION: {pf[it['pre_frame_of']]}\nTARGET_AXIS: {it['missing_axis']}\n"
             f"PROPOSED_AXES ({it['anon_id']}): {json.dumps(it['axes'], ensure_ascii=False)}\n\nReturn the JSON.")
        s = jx(chat(RUBRIC, u, seed=0)) or {"recovery": "MISS", "flags": []}
        scored.append({**it, "blind": s})
    # 集計(condition ごと、blind scorer=Qwen)
    conds = ["A_ordinary", "B_skepticism", "C_lessons", "D_retrieval", "T1_MF001", "T2_MFM2artifact"]
    tally = {c: {"HIT": 0, "PARTIAL": 0, "MISS": 0, "XDOMAIN": 0, "OVER_TRIGGER": 0, "IRRELEVANT_AXIS": 0} for c in conds}
    for s in scored:
        c = s["_cond"]
        tally[c][s["blind"]["recovery"]] = tally[c].get(s["blind"]["recovery"], 0) + 1
        for f in s["blind"].get("flags", []):
            if f in tally[c]: tally[c][f] += 1
    Path("/home/takasan/egl/experiments/metaframe_blind_rescore.json").write_text(json.dumps({"scorer": "Qwen3.6 blind (condition非開示)", "scored": scored, "tally": tally}, ensure_ascii=False, indent=2))
    print("### PHASE 1 blind rescore (Qwen, condition非開示) ###")
    print("condition            HIT PART MISS XDOM OVER IRREL")
    for c in conds:
        t = tally[c]; print(f"  {c:<18} {t['HIT']:>3} {t['PARTIAL']:>4} {t['MISS']:>4} {t['XDOMAIN']:>4} {t['OVER_TRIGGER']:>4} {t['IRRELEVANT_AXIS']:>5}")
    print("\n[Round1 私採点] T2=3HIT/0XDOM/0over, T1=2HIT/2over, C/D=各1XDOM")
    print("[確認] blind でも T2 の XDOMAIN=0 / over-trigger=0 が残るか、T1 の over-trigger が残るか")

if __name__ == "__main__":
    main()
