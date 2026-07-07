#!/usr/bin/env python3
"""Pre-injection gate pilot(§11 回答 baked-in)。
gate は task state + abstract axis-class LABEL + frame applicability predicate(metadata)のみ読む。
frame/incident 本体は渡さない。UNKNOWN→NULL(live)+log。ground truth は決定的軸(class既présence / XDOMAIN_LITERAL)。
controls A(always NULL)/B(always inject concrete)/C(use-if-relevant after content)/TREATMENT(pre-injection gate)。"""
import json, sys, urllib.request
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(s, u, mt=200):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=120) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0<=i<j else None
    except Exception: return None
def jl(t):
    i, j = t.find("["), t.rfind("]")
    try: return json.loads(t[i:j+1]) if 0<=i<j else [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]
    except Exception: return [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]

# EGL abstract axis-class taxonomy(LABEL + generic def のみ。frame/incident 本体でない)
AXIS_CLASSES = {
 "artifact-vs-grounded-check": "is a surface result/metric/finding an artifact of a construction/observation/experimental-setup choice not yet varied?",
 "measure-the-assertion": "is a declared/specified claim actually measured in the local/real context (spec != local applicability)?",
 "test-set-adequacy": "do the supplied tests cover the claimed property, or is the tested surface narrower (fail-open on an untested shape)?",
 "reproduce-the-finding": "is a flagged finding substantiated by a reproducing counterexample, or an over-flag?",
 "disaggregate-average": "is a null/aggregate result hiding heterogeneous subgroups (stratify before concluding)?",
}
ESDE_LITERAL = json.load(open("/home/takasan/egl/experiments/xdomain_literal_policy.json"))["esde_literal_blocklist"]
def xdom_lit(axes): return sum(1 for a in axes for t in ESDE_LITERAL if t.lower() in str(a).lower())

def main():
    rb = json.load(open("/home/takasan/egl/experiments/roundb_v2_run.json"))["heldout"]
    from run_roundb import HELDOUT, RETRIEVED
    pf = {h["id"]: h["pre"] for h in HELDOUT}
    out = {"tasks": [], "axis_classes": list(AXIS_CLASSES)}
    for h in rb:
        tid = h["id"]; base = h["axes"]["ordinary"]; conc = h["axes"]["concrete"]; abv2 = h["axes"]["abstract_v2"]
        target = h["missing_axis"]
        # --- allow-list signal: base answer が各 axis-class を既にカバーするか(class LABEL/def のみ、frame本体なし)---
        pres = jx(chat("Return ONLY JSON {\"covered\":[class names already covered by the answer]}. Judge which abstract axis-classes the answer already addresses.",
            f"ANSWER: {json.dumps(base,ensure_ascii=False)}\nAXIS_CLASSES: {json.dumps(AXIS_CLASSES,ensure_ascii=False)}\n\nReturn JSON.")) or {"covered": []}
        covered = pres.get("covered", [])
        # --- ground truth: base が target を既に回収? (決定的軸の一方) ---
        gt = jx(chat("Return ONLY JSON {\"base_has_target\":true|false}. Does the ANSWER already contain the TARGET axis (the specific decision-relevant check)?",
            f"TARGET: {target}\nANSWER: {json.dumps(base,ensure_ascii=False)}\n\nReturn JSON.")) or {"base_has_target": False}
        base_has_target = bool(gt.get("base_has_target"))
        conc_xdom = xdom_lit(conc)   # 決定的: concrete injection が literal 誤射を導入したか
        # ground truth: NULL_WIN = 注入が冗長(base既回収) or 有害(concrete XDOMAIN_LITERAL)
        null_win = base_has_target or conc_xdom > 0
        # abstract_v2 が base の欠落 target を補ったか(memory helpful の一方)
        mem_added = jx(chat("Return ONLY JSON {\"added\":true|false}. Does ANSWER_B recover the TARGET axis that ANSWER_A misses?",
            f"TARGET: {target}\nANSWER_A(base): {json.dumps(base,ensure_ascii=False)}\nANSWER_B(memory): {json.dumps(abv2,ensure_ascii=False)}\n\nReturn JSON.")) or {"added": False}
        memory_helpful = (not base_has_target) and bool(mem_added.get("added"))
        # --- GATE(task state + class LABEL + applicability metadata のみ。frame/incident本体なし)---
        gate = jx(chat("You are a PRE-INJECTION gate. Decide if injecting an external reasoning-prior (a past frame) into the "
            "main reasoning is worth it, WITHOUT seeing the frame content. You see: the task, the base first-pass answer's "
            "axes, the abstract axis-class labels, and which classes the base already covers. Rule: if the base already "
            "covers the relevant axis-classes, injection is redundant -> NO. If the base clearly MISSES an axis-class that "
            "the task plausibly needs, injection may help -> YES. If unclear -> UNKNOWN. Return ONLY JSON "
            "{\"decision\":\"YES|NO|UNKNOWN\",\"gap_class\":\"...|null\"}.",
            f"TASK ({h['domain']}): {pf[tid]}\nBASE_ANSWER_AXES: {json.dumps(base,ensure_ascii=False)}\nAXIS_CLASSES: {json.dumps(AXIS_CLASSES,ensure_ascii=False)}\nCLASSES_BASE_ALREADY_COVERS: {covered}\n\nReturn JSON.")) or {"decision": "UNKNOWN"}
        decision = gate.get("decision", "UNKNOWN")
        # TREATMENT downstream answer: YES→abstract_v2, NO/UNKNOWN→base(NULL)
        treat_axes = abv2 if decision == "YES" else base
        out["tasks"].append({"id": tid, "domain": h["domain"], "target": target,
            "base_covers": covered, "base_has_target": base_has_target, "concrete_xdomain_literal": conc_xdom,
            "ground_truth_null_win": null_win, "ground_truth_memory_helpful": memory_helpful,
            "gate_decision": decision, "gap_class": gate.get("gap_class"),
            "treatment_xdomain_literal": xdom_lit(treat_axes)})
        print(f"[{tid} {h['domain']}] gate={decision} | GT null_win={null_win} mem_helpful={memory_helpful} | conc_xdom={conc_xdom}", flush=True)
    # --- metrics ---
    T = out["tasks"]
    null_win = [t for t in T if t["ground_truth_null_win"]]
    mem_help = [t for t in T if t["ground_truth_memory_helpful"]]
    out["metrics"] = {
        "n": len(T), "n_null_win": len(null_win), "n_memory_helpful": len(mem_help),
        "NULL_WIN_correctly_gated_NO": sum(1 for t in null_win if t["gate_decision"] == "NO"),
        "MEMORY_HELPFUL_correctly_gated_YES": sum(1 for t in mem_help if t["gate_decision"] == "YES"),
        "false_positive_injection": sum(1 for t in null_win if t["gate_decision"] == "YES"),
        "false_negative_suppression": sum(1 for t in mem_help if t["gate_decision"] == "NO"),
        "UNKNOWN_rate": sum(1 for t in T if t["gate_decision"] == "UNKNOWN"),
        # control comparison: always-inject-concrete XDOMAIN_LITERAL vs TREATMENT(gate) vs always-NULL(0)
        "controlB_always_concrete_xdom_literal": sum(t["concrete_xdomain_literal"] for t in T),
        "treatment_gate_xdom_literal": sum(t["treatment_xdomain_literal"] for t in T),
        "controlA_always_null_xdom_literal": 0,
    }
    Path("/home/takasan/egl/experiments/gate_pilot.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    m = out["metrics"]
    print("\n### GATE PILOT metrics ###")
    print(f"  N={m['n']} | ground-truth NULL_WIN={m['n_null_win']} MEMORY_HELPFUL={m['n_memory_helpful']}")
    print(f"  NULL_WIN correctly gated NO: {m['NULL_WIN_correctly_gated_NO']}/{m['n_null_win']}")
    print(f"  MEMORY_HELPFUL correctly gated YES: {m['MEMORY_HELPFUL_correctly_gated_YES']}/{m['n_memory_helpful']}")
    print(f"  false-positive injection: {m['false_positive_injection']} | false-negative suppression: {m['false_negative_suppression']} | UNKNOWN: {m['UNKNOWN_rate']}")
    print(f"  XDOMAIN_LITERAL: controlB(always concrete)={m['controlB_always_concrete_xdom_literal']} | TREATMENT(gate)={m['treatment_gate_xdom_literal']} | controlA(always NULL)=0")

if __name__ == "__main__":
    main()
