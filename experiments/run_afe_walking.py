#!/usr/bin/env python3
"""AFE walking experiment: 6-arm (A ordinary / B skepticism / C meta-frame self-select / D AFE ensemble /
E sealed direct-source / F placebo ensemble) × 24 held-out incidents.
D/F: operators run concurrently (independent contexts, §11) → deterministic aggregation → orchestrator.
Process cost measured (§29). Leak-controlled: input = pre_frame only."""
import json, sys, time, urllib.request, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl")
EP, M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
def chat(sysp, u, mt=320):
    b = json.dumps({"model": M, "temperature": 0, "seed": 0, "max_tokens": mt, "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": u}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=180) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else None
    except Exception: return None
def jl(t):
    i, j = t.find("["), t.rfind("]")
    try: return json.loads(t[i:j+1]) if 0 <= i < j else [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]
    except Exception: return [x.strip("-•* ") for x in t.splitlines() if x.strip()][:3]

OPS = json.load(open("/home/takasan/egl/experiments/afe_operators.json"))["operators"]
ADMITTED = [o for o in OPS if o["compilation_status"] == "COMPILED_CANDIDATE"]
PLACEBO = json.load(open("/home/takasan/egl/experiments/afe_control_f.json"))["placebo_prompts"]
E_EXC = json.load(open("/home/takasan/egl/experiments/afe_control_e.json"))["excerpts"]
MF = [json.loads(l) for l in Path("/home/takasan/egl/metaframe_ledger.jsonl").read_text().splitlines() if l.strip() and json.loads(l).get("object") not in ("META_FRAME_REVIEW_NEED","META_FRAME_REVIEW_NEED_UPDATE","META_FRAME_ANNOTATION")]

SIGSYS = ("You are a narrow structural operator. Decide SIGNAL or NO_SIGNAL for the incident frame. SIGNAL requires "
  "(a) a basis quoted from the frame, (b) decision relevance, (c) >=1 concrete added structure. Generic outputs "
  "('consider another perspective','check assumptions','be skeptical') are INVALID as SIGNAL — use NO_SIGNAL. "
  "Return ONLY JSON {\"verdict\":\"SIGNAL|NO_SIGNAL\",\"added_variables\":[],\"added_distinctions\":[{\"left\":\"\",\"relation\":\"!=\",\"right\":\"\"}],"
  "\"added_relations\":[],\"suggested_operations\":[],\"basis_refs\":[],\"decision_relevance\":\"\",\"non_signal_reason\":null}. "
  "Limits: <=3 each.")
def run_operator(op, frame):
    pc = op["probe_contract"]
    u = (f"OPERATOR FUNCTION: {op['structural_function']}\nPROBE: {pc['primary_question']} {' '.join(pc['secondary_questions'])}\n"
         f"DO NOT: {'; '.join(pc['forbidden_expansions'])}\n\nINCIDENT FRAME:\n{frame}\n\nReturn the SIGNAL JSON.")
    s = jx(chat(SIGSYS, u)) or {"verdict": "NO_SIGNAL"}
    s["operator_id"] = op["operator_id"]; return s
def run_placebo(text, i, frame):
    u = f"CRITIQUE INSTRUCTION: {text}\n\nINCIDENT FRAME:\n{frame}\n\nReturn the SIGNAL JSON."
    s = jx(chat(SIGSYS, u)) or {"verdict": "NO_SIGNAL"}
    s["operator_id"] = f"PLACEBO-{i}"; return s

def aggregate(signals):
    """deterministic: valid-SIGNAL filter + dedup + same-structure grouping + support count + provenance."""
    def valid(s):
        struct = s.get("added_variables") or s.get("added_distinctions") or s.get("added_relations") or s.get("suggested_operations")
        return s.get("verdict") == "SIGNAL" and s.get("basis_refs") and s.get("decision_relevance") and struct
    def norm(s):
        parts = []
        for v in (s.get("added_variables") or []): parts.append(("VAR", str(v).lower().strip()))
        for d in (s.get("added_distinctions") or []):
            if isinstance(d, dict): parts.append(("DIST", f"{str(d.get('left','')).lower().strip()}|{str(d.get('right','')).lower().strip()}"))
        for r in (s.get("added_relations") or []): parts.append(("REL", str(r).lower().strip()))
        for o in (s.get("suggested_operations") or []): parts.append(("OP", str(o).lower().strip()))
        return parts
    groups = {}
    for s in signals:
        if not valid(s): continue
        for typ, key in norm(s):
            g = groups.setdefault((typ, key), {"type": typ, "key": key, "ops": set(), "raw": []})
            g["ops"].add(s["operator_id"]); g["raw"].append(s)
    cands = [{"type": g["type"], "structure": g["key"], "support_count": len(g["ops"]), "supporting_ops": sorted(g["ops"]),
              "basis_union": sorted({b for s in g["raw"] for b in (s.get("basis_refs") or [])})[:5],
              "decision_relevance": next((s.get("decision_relevance") for s in g["raw"] if s.get("decision_relevance")), "")} for g in groups.values()]
    return cands

ORCHSYS = ("You receive candidate frame-expansions (sources anonymized) for an incident. Return AT MOST 3 that add a "
  "decision-relevant dimension/distinction/relation/operation NOT already represented in the current frame. Support "
  "count is provenance, NOT a truth vote — a single specific candidate may beat many generic ones. Return ONLY a JSON "
  "list of {\"missing_dimension\":\"\",\"new_distinction\":\"\",\"decision_effect\":\"\"}.")
def orchestrate(frame, cands):
    if not cands: return []
    anon = [{"structure": c["structure"], "type": c["type"], "support": c["support_count"], "relevance": c["decision_relevance"]} for c in cands]
    out = jl(chat(ORCHSYS, f"FRAME:\n{frame}\n\nCANDIDATES (anonymized):\n{json.dumps(anon, ensure_ascii=False)}\n\nReturn <=3 JSON list."))
    return out[:3] if isinstance(out, list) else []

def arm_ABE(kind, frame):
    if kind == "A": s = "Propose AT MOST 3 concrete research/audit axes (things to check/measure) for the incident. Return ONLY a JSON list of short strings."
    elif kind == "B": s = "Be skeptical of the incident's conclusion. Propose AT MOST 3 concrete things to check that could show the conclusion is wrong. Return ONLY a JSON list of short strings."
    return jl(chat(s, f"INCIDENT FRAME:\n{frame}\n\nReturn the JSON list."))
def arm_E(frame):
    ex = "\n".join(f"- {k}: {v}" for k, v in E_EXC.items())
    return jl(chat("Here are bounded excerpts from an ontological source. Using them only if they help, propose AT MOST 3 concrete research/audit axes for the incident. Return ONLY a JSON list of short strings.",
                   f"SOURCE EXCERPTS:\n{ex}\n\nINCIDENT FRAME:\n{frame}\n\nReturn the JSON list."))
def arm_C(frame):
    preds = [{"name": m.get("name"), "applicability": m.get("applicability_predicate", {}).get("required_conditions"), "axes": m.get("suggested_axes")} for m in MF]
    return jl(chat("You have a small library of frame predicates. FIRST decide whether any applies to this incident (you may select none). Then propose AT MOST 3 concrete axes; use a predicate's axes only if it genuinely applies. Return ONLY a JSON list of short strings.",
                   f"FRAME PREDICATE LIBRARY:\n{json.dumps(preds, ensure_ascii=False)}\n\nINCIDENT FRAME:\n{frame}\n\nReturn the JSON list."))

def main():
    ho = json.load(open("/home/takasan/egl/experiments/afe_heldout.json"))["incidents"]
    results = []; proc = {"D_wall": [], "F_wall": []}
    for inc in ho:
        fr = inc["pre_frame"]; rec = {"id": inc["id"], "cause_type": inc["cause_type"], "target": inc["missing_axis"], "arms": {}}
        rec["arms"]["A"] = arm_ABE("A", fr)
        rec["arms"]["B"] = arm_ABE("B", fr)
        rec["arms"]["C"] = arm_C(fr)
        rec["arms"]["E"] = arm_E(fr)
        # D: concurrent operators
        t0 = time.monotonic()
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            sigs = list(ex.map(lambda o: run_operator(o, fr), ADMITTED))
        proc["D_wall"].append(round(time.monotonic() - t0, 2))
        cands = aggregate(sigs)
        rec["arms"]["D"] = orchestrate(fr, cands)
        rec["D_signals"] = [{"op": s["operator_id"], "verdict": s.get("verdict")} for s in sigs]
        rec["D_candidate_count"] = len(cands)
        # F: concurrent placebo
        t0 = time.monotonic()
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            psigs = list(ex.map(lambda it: run_placebo(it[1], it[0], fr), list(enumerate(PLACEBO))))
        proc["F_wall"].append(round(time.monotonic() - t0, 2))
        rec["arms"]["F"] = orchestrate(fr, aggregate(psigs))
        results.append(rec)
        print(f"[{inc['id']} {inc['cause_type']}] A/B/C/D/E/F done | D signals {sum(1 for s in sigs if s.get('verdict')=='SIGNAL')}/6 cands {len(cands)} | D_wall {proc['D_wall'][-1]}s", flush=True)
    Path("/home/takasan/egl/experiments/afe_walking_run.json").write_text(json.dumps({"results": results, "process_cost": proc, "admitted_operators": [o["operator_id"] for o in ADMITTED]}, ensure_ascii=False, indent=2))
    import statistics as st
    print(f"\nprocess cost: D mean {st.mean(proc['D_wall'])}s (6 concurrent ops) | F mean {st.mean(proc['F_wall'])}s")
    print("-> afe_walking_run.json saved. next: external-weight scoring.")

if __name__ == "__main__":
    main()
