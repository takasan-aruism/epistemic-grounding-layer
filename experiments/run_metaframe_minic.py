#!/usr/bin/env python3
"""MINI-C: incremental applicability classification(batch re-induction でなく)。
既存 meta-frame predicate を固定し、新規 verified incident を独立に MATCH/PARTIAL/NO_MATCH 分類。
multi-membership 許可。target-hunting / batch re-induction / single-cluster 強制は禁止。
特に INC-16 が ARTIFACT_VS_GROUNDED predicate に適合するか → artifact family が >=3 になるか。"""
import json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import metaframe as MF
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, seed=0, mt=200):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j + 1]) if 0 <= i < j else None
    except Exception: return None

# 固定 existing meta-frames(FIRST induction run の predicate。batch scramble 前)
FRAMES = {
 "MF-001-observer-subject": {"existing_members": ["INC-03", "INC-10", "INC-11", "INC-12"],
   "required": ["system aims for autonomy/self-modeling", "architecture relies on external polling/centralized state / researcher control", "goal: reduce external dependence, increase self-state fidelity"],
   "disqualifying": ["external control is a security/audit requirement", "state must be globally consistent"]},
 "MF-M2-artifact-vs-grounded": {"existing_members": ["INC-02", "INC-07"],
   "required": ["a surface result/metric/finding is being taken at face value", "there is suspicion the observed feature is an ARTIFACT of a construction / observation / experimental-setup choice", "goal: separate apparent from grounded / find the true structure"],
   "disqualifying": ["the construction/observation choice was already varied/controlled", "no artifact/essence distinction can be established"]},
 "MF-M3-arbitrary-vs-derived": {"existing_members": ["INC-01", "INC-08"],
   "required": ["a parameter/criterion is set manually or arbitrarily (feels like 神の手/god-hand)", "goal: make it self-justifying / physically or probabilistically derived", "desire to remove researcher arbitrariness"],
   "disqualifying": ["no physical/probabilistic basis exists", "fixed regulatory standard required"]},
}
# 新規 verified incident(v9.17 batch + INC-11 の multi-membership 再確認)
def load_inc():
    cands = json.load(open("/home/takasan/egl/experiments/metaframe_candidates.json"))["candidates"] + json.load(open("/home/takasan/egl/experiments/metaframe_candidates2.json"))["new_candidates"]
    return {c["incident_id"]: c for c in cands}
NEW = ["INC-11", "INC-13", "INC-14", "INC-15", "INC-16", "INC-17", "INC-18"]

CLS_SYS = ("You classify one incident against one meta-frame applicability predicate. Judge ONLY predicate fit. "
    "Return ONLY JSON {\"verdict\":\"MATCH|PARTIAL_MATCH|NO_MATCH\",\"basis\":\"...\"}. MATCH = the incident's "
    "pre-frame + failure + added distinction clearly satisfy the required conditions and hit none of the "
    "disqualifying ones. PARTIAL_MATCH = partial. NO_MATCH = not this frame. Multi-membership is allowed "
    "(other frames may also match); judge THIS frame only.")

def main():
    inc = load_inc()
    result = {"classifications": {}, "membership": {f: list(FRAMES[f]["existing_members"]) for f in FRAMES}}
    for iid in NEW:
        c = inc.get(iid)
        if not c: continue
        summary = (f"pre-claim: {str(c.get('claim_before',''))[:120]}; tension: {str(c.get('tension_or_failure',''))[:120]}; "
                   f"added_distinctions: {c.get('added_distinctions')}; revised-claim: {str(c.get('claim_after',''))[:120]}")
        result["classifications"][iid] = {}
        for fname, f in FRAMES.items():
            u = (f"META-FRAME '{fname}': required={f['required']}; disqualifying={f['disqualifying']}.\n"
                 f"INCIDENT {iid}: {summary}\n\nReturn the JSON.")
            v = jx(chat(CLS_SYS, u, seed=0)) or {"verdict": "NO_MATCH"}
            result["classifications"][iid][fname] = v.get("verdict")
            if v.get("verdict") == "MATCH" and iid not in result["membership"][fname]:
                result["membership"][fname].append(iid)
    # 集計: 各 frame の verified member 数(multi-membership)
    print("### MINI-C incremental classification (multi-membership) ###\n")
    print("incident   ", "  ".join(f.split('-')[1][:9] for f in FRAMES))
    for iid in NEW:
        row = result["classifications"].get(iid, {})
        print(f"  {iid}   ", "  ".join(f"{row.get(f,'?')[:4]:<9}" for f in FRAMES))
    print("\nframe membership (existing + new MATCH):")
    for f in FRAMES:
        mem = result["membership"][f]
        print(f"  {f}: {len(mem)} incidents {mem}  {'>=3 ✓' if len(mem)>=3 else '<3'}")
    result["artifact_reaches_3"] = len(result["membership"]["MF-M2-artifact-vs-grounded"]) >= 3
    # residual: どの frame にも MATCH しない新 incident
    result["residual"] = [iid for iid in NEW if all(result["classifications"].get(iid,{}).get(f)!="MATCH" for f in FRAMES)]
    print(f"\nresidual (no existing frame matched): {result['residual']}")
    print(f"artifact family reaches >=3 via incremental classification: {result['artifact_reaches_3']}")
    Path("/home/takasan/egl/experiments/metaframe_minic.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
