#!/usr/bin/env python3
"""PHASE B: axis-level blind rescore(既存 walking outputs、新規実験なし)。
Qwen blind scorer(arm/operator/source 非開示)が各 axis に one primary disposition。
external-weight(Claude)は B/D 判定を別途 verify。composite trust score 作らない。"""
import json, sys, urllib.request, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=60):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else None
    except Exception: return None
RUBRIC = ("Score ONE proposed research/audit axis against a TARGET missing axis for a situation. You do NOT know which "
  "method produced it. Assign exactly ONE primary disposition: TARGET_MATCH (recovers the specific target axis); "
  "USEFUL_NOVEL (genuinely useful for the situation but not the target); IRRELEVANT (unrelated to the situation); "
  "OVER_TRIGGER (forces an abstract/philosophical framework not grounded in the situation, e.g. 'cognitive axis "
  "creation','symmetry of existence'); UNSUPPORTED (asserts facts not present in the situation / fabricated); "
  "AMBIGUOUS (too vague to classify). Return ONLY JSON {\"disposition\":\"...\"}.")
HELD = {h["id"]: h["pre_frame"] for h in json.load(open("/home/takasan/egl/experiments/afe_heldout.json"))["incidents"]}
def score(it):
    u = f"SITUATION: {HELD[it['_id']]}\nTARGET_AXIS: {it['target']}\nPROPOSED_AXIS ({it['anon']}): {it['axis']}\n\nReturn the JSON."
    d = jx(chat(RUBRIC, u)) or {"disposition": "AMBIGUOUS"}
    return {**it, "disposition": d.get("disposition", "AMBIGUOUS")}
def main():
    items = json.load(open("/home/takasan/egl/experiments/afe_axis_batch.json"))
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        scored = list(ex.map(score, items))
    Path("/home/takasan/egl/experiments/afe_axis_scored.json").write_text(json.dumps(scored, ensure_ascii=False, indent=2))
    # PHASE C: per-condition raw dimensions
    DISP = ["TARGET_MATCH", "USEFUL_NOVEL", "IRRELEVANT", "OVER_TRIGGER", "UNSUPPORTED", "AMBIGUOUS"]
    arms = ["A", "B", "C", "D", "E", "F"]
    tab = {a: {d: 0 for d in DISP} for a in arms}
    for s in scored:
        tab[s["_arm"]][s["disposition"]] += 1
    # historical target recall: incidents where the arm had >=1 TARGET_MATCH axis
    recall = {a: len({s["_id"] for s in scored if s["_arm"] == a and s["disposition"] == "TARGET_MATCH"}) for a in arms}
    print("### PHASE C axis-level dimensions (Qwen blind, N=348 axes) ###")
    print("arm  count TARGET USEFUL IRREL OVER UNSUP AMBIG | axis_precision | target_recall/24")
    out = {}
    for a in arms:
        t = tab[a]; n = sum(t.values()); prec = (t["TARGET_MATCH"] + t["USEFUL_NOVEL"]) / n if n else 0
        out[a] = {"count": n, **t, "axis_precision": round(prec, 3), "target_recall": recall[a]}
        print(f"  {a}  {n:>4}  {t['TARGET_MATCH']:>5} {t['USEFUL_NOVEL']:>6} {t['IRRELEVANT']:>5} {t['OVER_TRIGGER']:>4} {t['UNSUPPORTED']:>5} {t['AMBIGUOUS']:>5} | {prec:>13.3f} | {recall[a]:>3}/24")
    json.dump({"dimensions": out, "scorer": "Qwen3.6 blind (arm非開示)"}, open("/home/takasan/egl/experiments/afe_axis_dimensions.json", "w"), ensure_ascii=False, indent=2)
    print("\n=== B vs D (Qwen blind) ===")
    b, d = out["B"], out["D"]
    print(f"  B: precision {b['axis_precision']} recall {b['target_recall']}/24 irrel {b['IRRELEVANT']} over {b['OVER_TRIGGER']}")
    print(f"  D: precision {d['axis_precision']} recall {d['target_recall']}/24 irrel {d['IRRELEVANT']} over {d['OVER_TRIGGER']}")

if __name__ == "__main__":
    main()
