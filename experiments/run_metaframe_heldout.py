#!/usr/bin/env python3
"""§24/§25 held-out transfer + CONTROL A/B/C/D + TREATMENT。
held-out pre-frame は intervention 前の状態のみ(leak制御, §6)。各条件が ≤3 research/audit axis を提案し、
実際に後で追加された missing axis を回収できたかを測る。outcome-neutral(§25.1)。"""
import json, sys, urllib.request, hashlib
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, seed=0, mt=500):
    b = json.dumps({"model": M, "temperature": 0, "seed": seed, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=180) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""

# held-out: TIER-2 operational(primitive 記録あり)+ 1 ESDE。pre_frame は intervention 前のみ(leak制御)。
HELDOUT = [
 {"id":"HO-1","tier":"TIER_2","family":"artifact/signal-vs-inflated","primitive_ref":"DE-0081",
  "pre_frame":"An independent code auditor returned several findings on a validator that passed all of its load-bearing tests. Should the code be reworked based on those findings? Propose what to check.",
  "missing_axis":"Is each finding substantiated by a reproducing counterexample (real defect) or an over-flag? Disposition before rework; reject findings that do not reproduce."},
 {"id":"HO-2","tier":"TIER_2","family":"artifact/test-set-adequacy","primitive_ref":"DE-0076",
  "pre_frame":"A gate implementation passes its 7 supplied tests and the auditor found nothing. Is it ready to ship? Propose what to check.",
  "missing_axis":"Do the supplied tests cover all malformed shapes? The tested surface may be narrower than the claimed property (a fail-open on an untested shape). Attack test-set adequacy."},
 {"id":"HO-3","tier":"TIER_2","family":"declared-vs-local","primitive_ref":"DE-0086",
  "pre_frame":"Official vendor docs document a capability with 'fast resume'. We want to use it to reduce our model-switch cost. Propose what to check before adopting.",
  "missing_axis":"Does the SPECIFIED capability actually work / perform in OUR local config? Docs give no local numbers; measure local behavior — it may fail locally. Specification != local applicability."},
 {"id":"HO-4","tier":"TIER_2","family":"measure-the-assertion","primitive_ref":"DE-0073",
  "pre_frame":"Two models are said to be un-co-servable on our GPUs, so we must pick an operating mode. Propose what to check before choosing.",
  "missing_axis":"The co-serve impossibility is a DECLARED assertion, not measured — measure it first. And the operating-mode choice depends on an unmeasured variable (swap frequency); measure before deciding."},
 {"id":"HO-5","tier":"TIER_1","family":"artifact-vs-grounded","primitive_ref":"gold G3 (v9.17 held-out)",
  "pre_frame":"In the main run, 77% of firings are one-directional (vs 25.6% in the short smoke run). Propose what to check before treating 77% as a property of the mechanism.",
  "missing_axis":"Confirm the firing CONDITION mechanism: is 77% a property of the mechanism, or an artifact of the experimental setup (tracking length / accumulation)? Check the construction before treating the metric as a finding."},
]

# CONTROL 材料
LESSONS = ("過去の教訓: (a) 主要所見が birth 方式/構成の変更で崩れる可能性を常に想定する。 (b) 平均化・見かけ構造で潰れる。"
           " (c) 語(失敗/認識)を物理操作へ還元できるか確認する。 (d) 観測方法・実験設定を確認してから所見化する。")
RETRIEVAL = ("検証済み過去incident(frame-delta): "
    "[INC-02: v9.11のlabel所見(n=2主体67%)を実構造と受容→R=0混入の見かけ構造と判明→純度基準で再measure]; "
    "[INC-11: 固定50step結果を『自己認識』と解釈→timing固定=研究者制御のアーティファクトと判明→event駆動へ]; "
    "[INC-05: runtime先行設計→paired auditを先に挿入しbit-identity検証]。")
mf001 = json.load(open("/home/takasan/egl/metaframe_ledger.jsonl").splitlines()[0]) if False else None
prov = json.loads(Path("/home/takasan/egl/metaframe_ledger.jsonl").read_text().splitlines()[0])
mfm2 = next(m for m in json.load(open("/home/takasan/egl/experiments/metaframe_induced.json"))["views"]["masked"] if m["meta_frame_id"]=="MF-M2")
def mf_block(m):
    ap=m.get("applicability_predicate",{})
    return (f"META-FRAME '{m.get('name')}': applies when {ap.get('required_conditions')}; "
            f"NOT when {ap.get('disqualifying_conditions') or m.get('non_applicable_cases')}; suggested axes: {m.get('suggested_axes')}.")

BASE="Propose AT MOST 3 concrete research/audit axes (things to check/measure) for the situation. Return ONLY a JSON list of short strings."
CONDS = {
 "A_ordinary": (BASE, lambda ho: ho["pre_frame"]),
 "B_skepticism": ("Be skeptical and consider hidden assumptions. "+BASE, lambda ho: ho["pre_frame"]),
 "C_lessons": (BASE, lambda ho: LESSONS+"\n\n"+ho["pre_frame"]),
 "D_retrieval": (BASE, lambda ho: RETRIEVAL+"\n\n"+ho["pre_frame"]),
 "T1_MF001": (BASE, lambda ho: mf_block(prov)+"\nIf applicable, use it.\n\n"+ho["pre_frame"]),
 "T2_MFM2artifact": (BASE, lambda ho: mf_block(mfm2)+"\nIf applicable, use it.\n\n"+ho["pre_frame"]),
}

def jl(t):
    i,j=t.find("["),t.rfind("]")
    try: return json.loads(t[i:j+1]) if 0<=i<j else [x.strip("-• ") for x in t.splitlines() if x.strip()][:3]
    except Exception: return [x.strip("-• ") for x in t.splitlines() if x.strip()][:3]

def main():
    out={"heldout":[], "conditions":list(CONDS)}
    for ho in HELDOUT:
        rec={"id":ho["id"],"family":ho["family"],"missing_axis":ho["missing_axis"],
             "pre_frame_hash":hashlib.sha256(ho["pre_frame"].encode()).hexdigest()[:12],"axes":{}}
        for cond,(sysp,uf) in CONDS.items():
            rec["axes"][cond]=jl(chat(sysp, uf(ho), seed=0))
        out["heldout"].append(rec)
        print(f"[{ho['id']} {ho['family']}] done", flush=True)
    Path("/home/takasan/egl/experiments/metaframe_heldout.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print("\n-> metaframe_heldout.json 保存。次: 外部weight採点(missing-axis recovery)")

if __name__=="__main__":
    main()
