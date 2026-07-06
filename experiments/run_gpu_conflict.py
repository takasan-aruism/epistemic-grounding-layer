#!/usr/bin/env python3
"""GPU co-serve conflict — system-level operational decision experiment(Taka directive v0.1）。

§16 順: RRI 形成(Qwen3.6)→ measurement-need decision → measurement plan(要る場合)→ independent audit。
禁止 pre-seed(sleep mode / cold-swap benchmark / phase batching / Claude auditor / sequential swap /
CPU RAM / Environment Registry / Environment Packet / static-vs-current)は prompt に入れない。
RRI は external specification question と local operational performance question を明示分離する（§5）。
"""
import json
import urllib.request
import socket
import urllib.error
from pathlib import Path

_EP = "http://localhost:8005/v1/chat/completions"
_M = "Qwen3.6-35B-A3B"
E = Path(__file__).resolve().parent
FROZEN = json.load(open(E / "GPU_CONFLICT_FROZEN.json"))
OBS = json.load(open(E / "GPU_CONFLICT_OBSERVATIONS.json"))


def chat(system, user, seed=0, max_tokens=1200):
    body = json.dumps({"model": _M, "temperature": 0, "seed": seed, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(_EP, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""


def js(t):
    i, j = t.find("{"), t.rfind("}")
    try:
        return json.loads(t[i:j + 1]) if 0 <= i < j else None
    except Exception:
        return None


RRI_SYS = (
    "You are an RRI Research-Intent worker. An operational conflict is blocking a decision. Determine the decision "
    "process — do NOT propose or pick a solution/operating-mode. CRITICALLY distinguish an EXTERNAL SPECIFICATION "
    "question (answerable from docs: does a feature exist?) from a LOCAL OPERATIONAL PERFORMANCE question (only "
    "answerable by observing THIS machine: actual latency, RAM peak, failure rate, cost). Do not convert local "
    "unknowns into generic web-research. Return ONLY JSON with keys: blocked_decision, blockage_classification "
    "(research|measurement|implementation|policy|mixed), currently_known (list), currently_unknown (list), "
    "resolution_requirements (list of what must be KNOWN/MEASURED), research_axes (list, external spec only), "
    "measurement_axes (list, local-machine behavior only), stop_condition (what evidence is sufficient to COMPARE "
    "the operating modes), measurement_required (true|false), measurement_required_basis."
)


def main():
    u = (f"OPERATIONAL_EVENT:\n{json.dumps(FROZEN, ensure_ascii=False)}\n\n"
         f"DIRECTLY_OBSERVED (factual, not a solution):\n{json.dumps(OBS, ensure_ascii=False)}\n\nReturn the JSON.")
    print("### GPU-conflict: RRI formation (Qwen3.6 seed=0) ###\n")
    rri = js(chat(RRI_SYS, u, seed=0, max_tokens=1400)) or {"_unparseable": True}
    print(f"[blocked_decision] {rri.get('blocked_decision')}")
    print(f"[blockage] {rri.get('blockage_classification')}")
    print(f"[currently_unknown] {rri.get('currently_unknown')}")
    print(f"[research_axes (external spec)] {rri.get('research_axes')}")
    print(f"[measurement_axes (local)] {rri.get('measurement_axes')}")
    print(f"[stop_condition] {rri.get('stop_condition')}")
    print(f"[measurement_required] {rri.get('measurement_required')} — {rri.get('measurement_required_basis')}")

    plan = None
    if rri.get("measurement_required"):
        MP_SYS = (
            "You form the SMALLEST load-bearing local measurement plan to decide between (as-yet-unnamed) DW "
            "operating modes. A metric that cannot change the operating choice is NOISE — exclude it. Return ONLY "
            "JSON {\"benchmarks\":[{\"decision_property\":\"...\",\"measured_variable\":\"...\","
            "\"why_it_can_change_the_decision\":\"...\",\"procedure\":\"...\",\"runs_and_stop_condition\":\"...\","
            "\"failure_recording\":\"...\",\"result_format\":\"...\"}]}. Include ONLY variables whose value could "
            "flip the operating choice; justify each."
        )
        mu = (f"MEASUREMENT_AXES:\n{json.dumps(rri.get('measurement_axes'), ensure_ascii=False)}\n"
              f"STOP_CONDITION:\n{rri.get('stop_condition')}\n"
              f"OBSERVED:\n{json.dumps(OBS, ensure_ascii=False)}\n\nReturn the JSON.")
        plan = js(chat(MP_SYS, mu, seed=1, max_tokens=1500)) or {"_unparseable": True}
        print(f"\n[measurement plan] {len(plan.get('benchmarks', []))} benchmark(s):")
        for b in plan.get("benchmarks", []):
            print(f"   - var={b.get('measured_variable')} | why_flips={str(b.get('why_it_can_change_the_decision'))[:90]}")

    AUD_SYS = (
        "You are an independent auditor of a measurement/decision design for a GPU operating-mode decision. Attack: "
        "premature preference; external-doc->local-performance expansion; single-run->operational-policy expansion; "
        "model-existence->role-availability expansion; server-ready->task-ready expansion; benchmark metrics that do "
        "NOT change the decision; hidden human-solution leakage; a fallback becoming default without evidence; "
        "same-model audit accepted as independent; switch cost ASSUMED instead of measured. Return ONLY JSON "
        "{\"findings\":[{\"category\":\"...\",\"evidence\":\"...\"}]}."
    )
    au = f"RRI_OUTPUT:\n{json.dumps(rri, ensure_ascii=False)}\nMEASUREMENT_PLAN:\n{json.dumps(plan, ensure_ascii=False)}\n\nReturn the JSON."
    audit = js(chat(AUD_SYS, au, seed=207, max_tokens=1000)) or {"findings": []}
    print(f"\n[independent audit] findings={[f.get('category') for f in audit.get('findings', [])]}")
    for f in audit.get("findings", []):
        print(f"   - {f.get('category')}: {str(f.get('evidence'))[:120]}")

    out = {"frozen": FROZEN, "observations": OBS, "rri": rri, "measurement_plan": plan, "design_audit": audit}
    (E / "gpu_conflict_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n→ gpu_conflict_run.json 保存。DW candidate 形成は sealed 未見の fresh subagent(次 step）。measurement は未実行。")


if __name__ == "__main__":
    main()
