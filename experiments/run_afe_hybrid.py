#!/usr/bin/env python3
"""Hybrid design test: Stage1 skepticism(wide, recall)→ Stage2 AFE discipline filter(precision)。
核心仮説: AFE-discipline が skepticism の noise(irrelevant/unsupported)を落としつつ target-match を保つか。
既存 B outputs に filter を適用(再生成なし)。external-weight dispositions と confusion 比較。"""
import json, sys, urllib.request, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=80):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else None
    except Exception: return None
# AFE discipline filter — AFE の admission 規律を precision gate として適用(target は見せない、frame への grounding のみ)
FILTER = ("You are a precision-discipline filter applying an admission rule to a proposed research/audit axis. "
  "You do NOT see any 'correct answer'. Decide KEEP or DROP. DROP if the axis: (a) has NO basis in the incident "
  "frame, (b) is not decision-relevant to THIS incident, (c) imports concepts from an unrelated domain "
  "(irrelevant), (d) forces an abstract/philosophical framework not grounded here, (e) asserts facts not present "
  "in the frame OR is a refusal/error message. KEEP only well-grounded, decision-relevant axes. Return ONLY JSON "
  "{\"verdict\":\"KEEP|DROP\",\"reason\":\"\"}.")
HELD = {h["id"]: h["pre_frame"] for h in json.load(open("/home/takasan/egl/experiments/afe_heldout.json"))["incidents"]}
# external-weight B dispositions (T=TARGET_MATCH,U=USEFUL,I=IRRELEVANT,S=UNSUPPORTED) by 6-hex anon suffix
BD = {"34371a":"U","3be157":"T","9805d8":"U","26186a":"T","532414":"U","f77ee2":"U","5415f8":"U","db0171":"T","dca9a6":"T",
"0573b8":"U","8af37d":"U","cd5b2d":"T","87a44d":"U","d47da9":"T","e43fbe":"U","07771b":"U","5f5697":"T","a74592":"U",
"31971b":"U","c52ac3":"T","cfc0e4":"U","60ee5f":"U","67d697":"U","c78fc5":"U","052c51":"U","21537c":"T","fff1c7":"T",
"7a1212":"T","88d0e8":"I","981acc":"T","3a7052":"T","9a1bbc":"U","c0682f":"T","478e7f":"U","75cef0":"U","9e0a6d":"U",
"41fd02":"U","c23f5a":"T","c7c879":"U","e289d9":"U","e38532":"U","098277":"T","43b429":"U","dbbbef":"T","63d629":"U",
"870f72":"U","d8561b":"T","3769fb":"T","8b125b":"U","a4819b":"U","1aa714":"I","3c621c":"U","a8d455":"T","89654b":"U",
"df6964":"T","e733c2":"T","3a93bd":"U","8c6246":"U","e38367":"T","1cf5b5":"T","5065a9":"U","f7e80c":"U","64706a":"I",
"809171":"I","f37106":"I","8b4a95":"T","b92038":"U","be038a":"U","2ef093":"S","3e4415":"S"}
def run(it):
    u = f"INCIDENT FRAME: {HELD[it['_id']]}\nPROPOSED AXIS: {it['axis']}\n\nReturn the JSON."
    d = jx(chat(FILTER, u)) or {"verdict": "KEEP"}
    return {**it, "keep": d.get("verdict") == "KEEP"}
def main():
    B = [i for i in json.load(open("/home/takasan/egl/experiments/afe_axis_batch.json")) if i["_arm"] == "B"]
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run, B))
    for r in res: r["ew_disp"] = BD.get(r["anon"].split("-")[1], "?")
    # confusion: should-drop = I/S, should-keep = T/U
    tp_drop = sum(1 for r in res if not r["keep"] and r["ew_disp"] in ("I", "S"))
    fn_drop = sum(1 for r in res if r["keep"] and r["ew_disp"] in ("I", "S"))       # noise that survived
    fp_drop = sum(1 for r in res if not r["keep"] and r["ew_disp"] in ("T", "U"))   # good axes wrongly dropped
    kept_T = sum(1 for r in res if r["keep"] and r["ew_disp"] == "T")
    dropped_T = sum(1 for r in res if not r["keep"] and r["ew_disp"] == "T")
    kept = [r for r in res if r["keep"]]
    hybrid_recall = len({r["_id"] for r in kept if r["ew_disp"] == "T"})
    hy_T = sum(1 for r in kept if r["ew_disp"]=="T"); hy_U = sum(1 for r in kept if r["ew_disp"]=="U")
    hy_prob = sum(1 for r in kept if r["ew_disp"] in ("I","S"))
    prec = round((hy_T+hy_U)/len(kept),3) if kept else 0
    Path("/home/takasan/egl/experiments/afe_hybrid.json").write_text(json.dumps({"filtered":res,"kept_count":len(kept)},ensure_ascii=False,indent=2))
    print("### Hybrid (skepticism-generate -> AFE-discipline filter) on existing B ###")
    print(f"  B input: 70 axes (T25/U38/I5/S2), recall 19/24, problematic 7")
    print(f"  filter dropped {70-len(kept)} axes, kept {len(kept)}")
    print(f"  noise removal: dropped {tp_drop}/7 problematic (I/S); {fn_drop} noise survived")
    print(f"  target preservation: kept {kept_T}/25 TARGET_MATCH; dropped {dropped_T} target-match (over-filter)")
    print(f"  => HYBRID: recall {hybrid_recall}/24 | precision {prec} | problematic {hy_prob}")
    print(f"\n  compare: B recall 19 prec 0.90 prob 7 | D(AFE) recall 13 prec 0.96 prob 0 | HYBRID recall {hybrid_recall} prec {prec} prob {hy_prob}")

if __name__ == "__main__":
    main()
