#!/usr/bin/env python3
"""Qwen rubric-v2 two-axis blind scorer (2nd independent 2-axis scorer for MULTI_SCORER_CONSENSUS).
Applies the FROZEN rubric HBB_SEALED_GPT_RUBRIC_V2 (sha256 012941ab..., verified) to each SEALED arm
answer, scoring DETECTION (0/1/2) and RECONSTRUCTION (0/1/2) independently. Arm is NEVER sent to the
model (blind). RECONSTRUCTION is judged against the held-out historical breakthrough target.
Run AFTER hbb_sealed_run.json is extended to N=13 (HBB-04/30 cells present)."""
import json, sys, hashlib, urllib.request, concurrent.futures as cf
from pathlib import Path
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
EXP = "/home/takasan/egl/experiments"

def chat(sysp, u, mt=60):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""

def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else None
    except Exception: return None

# --- frozen rubric (load, do not paraphrase the level anchors) ---
RUB = json.load(open(f"{EXP}/HBB_GPT_rubric_v2_frozen.json"))["rubric"]
DET = RUB["dimensions"]["DETECTION"]; REC = RUB["dimensions"]["RECONSTRUCTION"]
SYS = (
  "You score one research-advice answer on TWO INDEPENDENT axes using a frozen rubric. "
  "You do NOT know which method produced the answer; judge only its content.\n"
  "DETECTION: 0=" + DET["0"] + " 1=" + DET["1"] + " 2=" + DET["2"] + "\n"
  "RECONSTRUCTION: 0=" + REC["0"] + " 1=" + REC["1"] + " 2=" + REC["2"] + "\n"
  "Rules: " + RUB["independence_rule"] + " " + RUB["historical_equivalence_rule"] + " "
  "Do not reward generic skepticism as reconstruction. Do not penalize concise label-style answers for "
  "brevity if the structure is explicit. Do not reward prose fluency or philosophical vocabulary. "
  "When genuinely between levels, choose the LOWER score. "
  "Return ONLY JSON {\"DETECTION\":0|1|2,\"RECONSTRUCTION\":0|1|2}."
)

# --- data sources ---
CAND = {x["id"]: x for x in json.load(open(f"{EXP}/hbb_candidates.json"))["candidates"]}
TMAP = json.load(open(f"{EXP}/HBB_GPT_v2_scores.json")).get("target_map", {})
PACK = json.load(open(f"{EXP}/hbb_sealed_t0.json")).get("packets", {})
# extra T0 files for the two handoff incidents (loaded if present)
EXTRA_T0 = {}
for fn in ("HBB-04_T0_GPT_draft.json", "HBB-30_T0_GPT_user_attested.json"):
    p = Path(f"{EXP}/{fn}")
    if p.exists():
        d = json.loads(p.read_text()); EXTRA_T0[d["id"]] = d

def stuck_frame(iid):
    if iid in PACK:
        return PACK[iid].get("t0_stuck_frame", "")
    d = EXTRA_T0.get(iid)
    if d:
        tp = d.get("t0_packet", {})
        return " ".join(str(tp.get(k, "")) for k in ("document_claim", "active_frame", "current_task")).strip()
    return CAND.get(iid, {}).get("t0_stuck_frame", "")

def target(iid):
    # held-out historical breakthrough reference (never shown to the arms; used only for RECONSTRUCTION judging)
    return TMAP.get(iid) or CAND.get(iid, {}).get("breakthrough_structure", "")

def outtext(r):
    parts = []
    for a in (r.get("output") or [])[:3]:
        parts.append(" ".join(str(v) for v in a.values() if v) if isinstance(a, dict) else str(a))
    return " || ".join(parts)[:600]

def score(r):
    iid = r["id"]; fr = stuck_frame(iid); tg = target(iid); ans = outtext(r)
    opaque = hashlib.sha256(f"{iid}|{r['arm']}|{r['rung']}".encode()).hexdigest()[:12]
    base = {"opaque_id": opaque, "id": iid, "arm": r["arm"], "rung": r["rung"],
            "depth": r["depth"], "scope": r.get("scope", CAND.get(iid, {}).get("intervention_scope"))}
    if not ans.strip() or not fr or not tg:
        return {**base, "DETECTION": 0, "RECONSTRUCTION": 0, "note": "empty_answer_or_missing_frame_target"}
    u = f"SITUATION (current stuck frame):\n{fr[:500]}\n\nHISTORICAL BREAKTHROUGH TARGET (reference for RECONSTRUCTION only):\n{tg[:300]}\n\nANSWER TO SCORE:\n{ans}\n\nReturn the JSON."
    d = jx(chat(SYS, u)) or {}
    def clamp(v):
        try: v = int(v)
        except Exception: return 0
        return v if v in (0, 1, 2) else 0
    return {**base, "DETECTION": clamp(d.get("DETECTION")), "RECONSTRUCTION": clamp(d.get("RECONSTRUCTION"))}

def main():
    R = json.load(open(f"{EXP}/hbb_sealed_run.json"))["results"]
    ids = sorted(set(x["id"] for x in R))
    print(f"scoring {len(R)} cells over {len(ids)} incidents: {ids}", flush=True)
    missing = [i for i in ids if not stuck_frame(i) or not target(i)]
    if missing:
        print(f"WARNING: missing frame/target for {missing} — those cells score 0/0. "
              f"(Expected until HBB-04 T0 draft is provided.)", flush=True)
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        scored = list(ex.map(score, R))
    out = {"object": "HBB_QWEN_V2_SCORES", "scorer": "Qwen3.6-35B-A3B (blind, arm withheld)",
           "rubric_sha256": "012941aba485f33b8328b7e5cba2a84b5c1db82119bb96554bc8dea84f4f9f17",
           "n_incidents": len(ids), "incidents": ids, "scores": scored}
    Path(f"{EXP}/hbb_qwen_v2_scores.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    # quick per-arm 2-axis means (sanity, not a claim)
    import statistics as st
    for a in "ABCDF":
        s = [x for x in scored if x["arm"] == a]
        if s:
            print(f"  arm {a}: DET {st.mean(x['DETECTION'] for x in s):.3f} | "
                  f"REC {st.mean(x['RECONSTRUCTION'] for x in s):.3f} | n={len(s)}")
    print("-> hbb_qwen_v2_scores.json")

if __name__ == "__main__":
    main()
