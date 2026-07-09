#!/usr/bin/env python3
"""Qwen rubric-v2 per-candidate 2-axis scorer for the recon-exhibit (frozen rubric sha 012941ab).
Scores every candidate on DETECTION/RECONSTRUCTION, BLIND to condition (condition kept in the output record but
never sent to the model). RECONSTRUCTION reference = held-out breakthrough_structure (never shown to generators).
opaque_id = sha256(incident|condition|seed|cand_idx)[:14] for the GPT-handoff join. Run is GATED (Taka go)."""
import json, sys, hashlib, urllib.request, concurrent.futures as cf
from pathlib import Path
EXP = "/home/takasan/egl/experiments"
EP, MODEL = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
RUB = json.load(open(f"{EXP}/HBB_GPT_rubric_v2_frozen.json"))["rubric"]
DET, REC = RUB["dimensions"]["DETECTION"], RUB["dimensions"]["RECONSTRUCTION"]
SYS = ("You score one candidate reconstruction on TWO INDEPENDENT axes using a frozen rubric. You do NOT know which "
       "method produced it; judge only content.\nDETECTION: 0=" + DET["0"] + " 1=" + DET["1"] + " 2=" + DET["2"] +
       "\nRECONSTRUCTION: 0=" + REC["0"] + " 1=" + REC["1"] + " 2=" + REC["2"] + "\n" + RUB["independence_rule"] + " " +
       RUB["historical_equivalence_rule"] + " Do not reward generic skepticism as reconstruction. Do not penalize "
       "concise label-style answers for brevity. When between levels choose the lower. Return ONLY JSON "
       "{\"DETECTION\":0|1|2,\"RECONSTRUCTION\":0|1|2}.")
CAND = {x["id"]: x for x in json.load(open(f"{EXP}/hbb_candidates.json"))["candidates"]}
PACK = json.load(open(f"{EXP}/hbb_sealed_t0.json"))["packets"]

def chat(u):
    b = json.dumps({"model": MODEL, "temperature": 0, "seed": 0, "max_tokens": 60,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""

def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else {}
    except Exception: return {}

def clamp(v):
    try: v = int(v)
    except Exception: return 0
    return v if v in (0, 1, 2) else 0

def score_one(item):
    iid, cond, seed, k, cand = item
    opq = hashlib.sha256(f"{iid}|{cond}|{seed}|{k}".encode()).hexdigest()[:14]
    base = {"opaque_id": opq, "incident": iid, "condition": cond, "seed": seed, "cand_idx": k}
    if not cand.strip() or "(no structural proposal)" in cand:
        return {**base, "DETECTION": 0, "RECONSTRUCTION": 0}
    fr = PACK[iid]["t0_stuck_frame"]; tg = CAND[iid]["breakthrough_structure"]
    u = (f"SITUATION (stuck frame):\n{fr[:450]}\n\nHISTORICAL BREAKTHROUGH TARGET (RECONSTRUCTION reference only):\n"
         f"{tg[:280]}\n\nCANDIDATE:\n{cand[:700]}\n\nReturn the JSON.")
    d = jx(chat(u))
    return {**base, "DETECTION": clamp(d.get("DETECTION")), "RECONSTRUCTION": clamp(d.get("RECONSTRUCTION"))}

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else f"{EXP}/hbb_recon_exhibit_candidates.json"
    out = sys.argv[2] if len(sys.argv) > 2 else f"{EXP}/hbb_recon_qwen_scores.json"
    doc = json.load(open(src))
    items = [(r["incident"], r["condition"], r["seed"], k, c)
             for r in doc["records"] for k, c in enumerate(r["candidates"])]
    print(f"scoring {len(items)} candidates (Qwen, blind to condition)", flush=True)
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        scored = list(ex.map(score_one, items))
    Path(out).write_text(json.dumps({"object": "RECON_QWEN_SCORES", "rubric_sha256": RUB.get("_", "012941ab"),
                                     "n": len(scored), "scores": scored}, ensure_ascii=False, indent=2))
    print("->", out)

if __name__ == "__main__":
    main()
