#!/usr/bin/env python3
"""Pass B frame-delta 導出 + §16 clustering(2 view)+ Pass C induction(Qwen, <=3 candidate)。
induction 入力: VERIFIED frame-delta のみ。lesson heading / 教訓文 / family label は渡さない(§6 blindness)。
view2 は ESDE 固有名詞を mask(structural vs topical)。gold は非開示。"""
import json, re, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
import metaframe as MF
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, seed=0, mt=1600):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t, o="{", c="}"):
    i, j = t.find(o), t.rfind(c)
    try: return json.loads(t[i:j + 1]) if 0 <= i < j else None
    except Exception: return None

VERIFIED = ["INC-01", "INC-02", "INC-03", "INC-05", "INC-06", "INC-07", "INC-08", "INC-10", "INC-11", "INC-12"]
MASK = {"B_Gen": "PARAM_X", "CID": "UNIT", "cid": "unit", "label": "GROUP", "S≥0.20": "THRESHOLD_T",
        "R=0": "ZERO_STATE", "R>0": "ACTIVE_STATE", "n_core": "SIZE", "Q_remaining": "RESERVE",
        "Fetch": "READ_OP", "E3": "EVENT_E", "Layer A": "TRACK_A", "Layer B": "TRACK_B",
        "phase+r": "AXIS_PR", "theta": "ANGLE", "ESDE": "SYSTEM", "v9.1": "vX", "認知層": "COG_LAYER"}
def mask(s):
    s = str(s)
    for k, v in MASK.items(): s = s.replace(k, v)
    return s

def build_frame_deltas(cands):
    fds = []
    for c in cands:
        if c["incident_id"] not in VERIFIED: continue
        cb, ca = str(c.get("claim_before", "")), str(c.get("claim_after", ""))
        eff = "REVERSED" if ("誤" in ca or "artifact" in ca.lower() or "でない" in ca or "not" in ca.lower()) else "REDIRECTED"
        fds.append({"frame_delta_id": f"FD-{c['incident_id'][-2:]}", "incident_id": c["incident_id"],
                    "origin": "DERIVED_FROM_INCIDENT", "decision_effect": eff,
                    "pre_frame": {"terminal_or_active_claim": cb, "represented_distinctions": [], "available_operations": []},
                    "post_frame": {"added_variables": c.get("added_dimensions", []),
                                   "added_distinctions": c.get("added_distinctions", []),
                                   "added_operations": c.get("added_operations", []), "revised_claim": ca},
                    "delta_summary": f"{cb[:60]} -> {ca[:60]}"})
    return fds

IND_SYS = ("You induce META-FRAME candidates from VERIFIED frame-delta objects. A frame-delta records how a "
    "represented problem-frame changed (pre-claim -> added distinction/operation -> revised claim). Find whether "
    "MULTIPLE frame-deltas share the SAME frame-changing STRUCTURE despite different surface topics. Return AT MOST "
    "3 candidates. Do NOT restate a lesson. Reject generic virtues (be skeptical / check assumptions). Each "
    "candidate MUST have: name, derived_from_incidents (>=3 incident_ids that share it), shared_pre_frame, "
    "shared_failure_shape, shared_missing_dimension_shape, shared_frame_delta, applicability_predicate "
    "{required_conditions[], supporting_signals[], disqualifying_conditions[]}, suggested_axes[], "
    "non_applicable_cases[]. Prefer ONE strong structural family over many generic ones. Return ONLY JSON "
    "{\"candidates\":[...]}.")

def induce(fds, view, seed):
    payload = [{"id": f["incident_id"], "pre": f["pre_frame"]["terminal_or_active_claim"],
                "added_distinctions": f["post_frame"]["added_distinctions"],
                "added_operations": f["post_frame"]["added_operations"], "post": f["post_frame"]["revised_claim"]}
               for f in fds]
    if view == "masked":
        payload = json.loads(mask(json.dumps(payload, ensure_ascii=False)))
    raw = chat(IND_SYS, f"FRAME_DELTAS ({view} view):\n{json.dumps(payload, ensure_ascii=False)}\n\nReturn the JSON.", seed=seed, mt=1800)
    return (jx(raw) or {}).get("candidates", [])

def main():
    cands = json.load(open("/home/takasan/egl/experiments/metaframe_candidates.json"))["candidates"]
    cands += json.load(open("/home/takasan/egl/experiments/metaframe_candidates2.json"))["new_candidates"]
    fds = build_frame_deltas(cands)
    fdids = [f["frame_delta_id"] for f in fds]
    print(f"### frame-delta {len(fds)} 件(VERIFIED {len(VERIFIED)})→ induction 2 view ###\n")
    out = {"frame_deltas": fds, "views": {}}
    for view, seed in [("full", 0), ("masked", 7)]:
        mfs = induce(fds, view, seed)
        graded = []
        for i, mf in enumerate(mfs):
            mf["meta_frame_id"] = f"MF-{view[:1].upper()}{i+1}"; mf["version"] = 1
            mf["origin"] = "INDUCED_FROM_INCIDENT_CLUSTER"; mf["status"] = "CANDIDATE"
            mf["source_frame_delta_refs"] = [f"FD-{x[-2:]}" for x in (mf.get("derived_from_incidents") or [])]
            g = MF.validate_meta_frame(mf, VERIFIED, fdids, existing_human_heuristics=["H-OPS-01", "H-OPS-02"])
            mf["_gate"] = g
            graded.append(mf)
            print(f"  [{view}] {mf['meta_frame_id']} '{str(mf.get('name'))[:50]}' incidents={mf.get('derived_from_incidents')} gate_valid={g['valid']}")
            if not g["valid"]: print(f"       gate: {g['problems'][:2]}")
        out["views"][view] = graded
    Path("/home/takasan/egl/experiments/metaframe_induced.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n-> metaframe_induced.json 保存。次: 外部weight監査(Claude §19)")

if __name__ == "__main__":
    main()
