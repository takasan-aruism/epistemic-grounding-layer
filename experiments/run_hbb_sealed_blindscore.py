#!/usr/bin/env python3
"""Skeptical re-check: SEALED を arm 匿名化して genuinely-blind な Qwen で再採点。
私の scoring の format bias(prose甘め/terse辛め)+ 部分盲検バイアスを検査。
各 output に arm label を見せず『target axis を回収したか』を YES/PARTIAL/NO で判定。"""
import json, sys, hashlib, urllib.request, concurrent.futures as cf
from pathlib import Path
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=50):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else None
    except Exception: return None
CAND = {x["id"]: x for x in json.load(open("/home/takasan/egl/experiments/hbb_candidates.json"))["candidates"]}
T0 = json.load(open("/home/takasan/egl/experiments/hbb_sealed_t0.json"))["packets"]
R = json.load(open("/home/takasan/egl/experiments/hbb_sealed_run.json"))["results"]
DEPTH = {"H0": 4, "H1": 3, "H2": 2, "H3": 1}
RUB = ("You judge whether a proposed next-step axis RECOVERS a specific TARGET insight for a stuck research "
  "situation. You do NOT know which method produced it; judge only the content. A terse structural label "
  "(e.g. 'procedure_induced_structure', 'individuation_rule') counts as recovery if it names the target "
  "insight — do NOT penalize brevity vs prose. Return ONLY JSON {\"recover\":\"YES|PARTIAL|NO\"}.")
def outtext(r):
    o = r.get("output") or []
    parts = []
    for a in o[:3]:
        if isinstance(a, dict): parts.append(" ".join(str(v) for v in a.values() if v))
        else: parts.append(str(a))
    return " || ".join(parts)[:400]
def score(r):
    txt = outtext(r)
    if not txt.strip(): return {**{k: r[k] for k in ("id", "arm", "rung", "depth")}, "recover": "NO"}
    u = f"SITUATION: {T0[r['id']]['t0_stuck_frame'][:300]}\nTARGET INSIGHT: {CAND[r['id']]['breakthrough_structure']}\nPROPOSED AXIS: {txt}\n\nReturn the JSON."
    d = jx(chat(RUB, u)) or {"recover": "NO"}
    return {**{k: r[k] for k in ("id", "arm", "rung", "depth")}, "scope": CAND[r["id"]]["intervention_scope"], "recover": d.get("recover", "NO")}
def main():
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        scored = list(ex.map(score, R))
    # depth = 最高(最弱hint)で YES に達した rung
    best = {}
    for s in scored:
        if s["recover"] == "YES":
            key = (s["id"], s["arm"]); best[key] = max(best.get(key, 0), s["depth"])
    ids = list(T0); AA = [k for k in ids if CAND[k]["intervention_scope"].startswith("ARUISM")]; FOS = [k for k in ids if k not in AA]
    def dep(iid, arm): return best.get((iid, arm), 0)
    def rc(arm, S): return [k for k in S if dep(k, arm) > 0]
    print("### SEALED blind re-score (Qwen, arm-anonymized, brevity-neutral) ###")
    print("Breakthrough Reach (blind):")
    for a in "ABFCD": print(f"  {a}: total {len(rc(a,ids))}/11 | AA {len(rc(a,AA))}/6 | FOS {len(rc(a,FOS))}/5")
    BA = set(rc("B", AA)); CA = set(rc("C", AA)); DA = set(rc("D", AA))
    print(f"\nB on AA: {sorted(BA)}")
    print(f"C on AA: {sorted(CA)} | C-unique(C∖B): {sorted(CA-BA)}")
    print(f"D on AA: {sorted(DA)} | D-unique(D∖B): {sorted(DA-BA)}")
    print(f"B∪C on AA: {len(BA|CA)} | max(B,C): {max(len(BA),len(CA))}")
    print(f"H_primary [B∪C>max AND (C-unique OR D-unique)>=1]: {'CONFIRMED' if len(BA|CA)>max(len(BA),len(CA)) and (len(CA-BA)>=1) else 'NOT_CONFIRMED'}")
    Path("/home/takasan/egl/experiments/hbb_sealed_blindscore.json").write_text(json.dumps({"scored": scored, "reach": {a: {"total": len(rc(a, ids)), "AA": len(rc(a, AA)), "FOS": len(rc(a, FOS))} for a in "ABFCD"}, "C_unique_AA": sorted(CA - BA), "D_unique_AA": sorted(DA - BA), "B_AA": sorted(BA), "C_AA": sorted(CA), "D_AA": sorted(DA)}, ensure_ascii=False, indent=2))
if __name__ == "__main__":
    main()
