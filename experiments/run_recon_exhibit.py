#!/usr/bin/env python3
"""Reconstruction CAPABILITY-EXHIBIT — generation harness (frozen prereg v0.4.4, seal 4cb77d89..., DE-0124;
bindings B-1..B-5 = hbb_recon_impl_binding.json). Generates candidate reconstructions for the conditions on
hard-core {08,10,30}. NO author selection: every condition emits ALL N candidates; target-blind scorers certify
(separate step). Target (breakthrough_structure) is NEVER used in generation. Run is GATED (Taka 'run' go);
--smoke = tiny end-to-end check only.
FROZEN: operators=11 (6 AFE ADMITTED + 5 Formal clean) · N=44 (=11x4) · pass_cap=4 · M=10 · budget=exhaustive.
B-1 diversity=temp0.8+seed · B-2 R4 pass-chaining · B-3 R5 L1/L2/L3 · B-5 frozen prompts."""
import json, sys, re, argparse, urllib.request, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, "/home/takasan/egl/experiments")
sys.path.insert(0, "/home/takasan/egl")   # metaframe_mask lives here (B-3 fix)
import run_afe_walking as afe          # run_operator, ADMITTED
import metaframe_mask as MP            # MASK_PIPELINE v2 (seal 2bfd70f9); hard import — R5 masking is load-bearing
EXP = "/home/takasan/egl/experiments"
EP, MODEL = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
INCIDENTS = ["HBB-08", "HBB-10", "HBB-30"]
TEMP = 0.8                              # B-1

# --- frozen 11 operators = 6 AFE ADMITTED + 5 Formal clean ---
AFE_OPS = afe.ADMITTED
_FML = json.load(open(f"{EXP}/formal_esde_operators.json"))
FORMAL_OPS = [{"operator_id": p["probe_id"], "structural_function": p["structural_function"],
               "probe_contract": {"primary_question": p["primary_question"], "secondary_questions": [],
                                  "forbidden_expansions": p["forbidden"]}}
              for p in _FML["sealable_axiom_grounded_probes"]]
OPERATORS = AFE_OPS + FORMAL_OPS
assert len(OPERATORS) == 11, f"expected 11 operators, got {len(OPERATORS)}"
T0 = json.load(open(f"{EXP}/hbb_sealed_t0.json"))["packets"]

# --- B-5 frozen prompts ---
P_BASE = "You are advising on an ongoing research project. What is the single most important thing to do next? Give one concrete alternative frame / next step."
P_SKEPTIC = "You are a skeptical research advisor. The current conclusion may be wrong. Name the frame defect and propose a concrete alternative frame that could be correct."
P_R2 = ("You are a frame reconstructor. Given ONLY the current stuck frame, propose an alternative frame that "
        "changes the subject / level / key distinction, and state the next action that follows. Do not reference "
        "any known result or answer. Output the alternative frame + next action.")
P_DETECT = "You are a skeptical research advisor. Name only the single most consequential frame defect (locus + why)."
P_RECON = ("You are a frame reconstructor. Given the current stuck frame and a detected frame-defect, build an "
           "alternative frame structurally different at the subject/level/distinction, and the next action.")
P_R3_SINGLE = ("You are a research advisor. In ONE step, given the current stuck frame, both (a) detect its most "
               "consequential frame defect and (b) build an alternative frame structurally different at the "
               "subject/level/distinction, with the next action. Single combined answer.")

def qgen(sysp, user, seed, temp=TEMP, mt=280):
    """B-1: Qwen generation with temperature + seed (candidate diversity)."""
    b = json.dumps({"model": MODEL, "temperature": temp, "seed": int(seed), "max_tokens": mt,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": user}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=150) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""

def op_candidate(op, frame):
    """one operator's structural proposal as a readable candidate (deterministic; diversity via frame-chaining B-2).
    NO_SIGNAL / empty -> explicit 'no proposal' (scorer -> 0). Rendering bound in hbb_recon_impl_binding.json."""
    try:
        s = afe.run_operator(op, frame)
        parts = []
        for key in ("added_distinctions", "added_variables", "added_relations", "suggested_operations"):
            parts += [str(x) for x in (s.get(key) or [])]
        body = " ; ".join(p for p in parts if p.strip())
        oid = op.get("operator_id")
        if not body or s.get("verdict") == "NO_SIGNAL":
            return f"[{oid}] (no structural proposal)"
        return f"[{oid}] proposed reframe: {body}"[:1400]
    except Exception as e:
        return f"(operator {op.get('operator_id')} error: {e})"

def r4_passes(frame0, pass_cap):
    """B-2: STOP-SHIFT-RUN-COMPARE. pass1 = 11 ops on frame0; pass p>1 = 11 ops on frame0 + pooled prior outputs."""
    pooled, frame = [], frame0
    for p in range(pass_cap):
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            outs = list(ex.map(lambda o: op_candidate(o, frame), OPERATORS))
        pooled += outs
        prior = " || ".join(x[:180] for x in pooled)[:2500]
        frame = f"{frame0}\n\n[prior structural proposals, all pooled — no selection]\n{prior}"
    return pooled

# --- B-3 lossy ladder ---
_TOKN = re.compile(r"[A-Z][a-zA-Z_]{2,}|[A-Za-z]*\d[A-Za-z0-9_.]*|[A-Za-z]{4,}")
def lossy(frame, level):
    assert MP is not None, "metaframe_mask (MASK v2) required for R5 lossy ladder"
    if level == "L1":
        return MP.mask_v2(frame)
    if level == "L2":
        return _TOKN.sub("[term]", MP.mask_v2(frame))   # 2nd pass: remaining domain/technical tokens
    if level == "L3":                              # structure-only skeleton
        return ("A claim/quantity about [X] is being treated as [established/expected]. "
                "Frame: reason within this from-[premise]-to-[conclusion] setup. "
                "Decision: choose the next step and its boundary.")
    raise ValueError(level)

def candidates_for(cond, iid, seed, N, pass_cap):
    fr = T0[iid]["t0_stuck_frame"]
    out = []
    if cond == "R0":
        for k in range(N):
            out.append(qgen(P_BASE if k % 2 == 0 else P_SKEPTIC, f"SITUATION:\n{fr}", seed * 1000 + k))
    elif cond == "R2":
        for k in range(N):
            out.append(qgen(P_R2, f"CURRENT STUCK FRAME:\n{fr}", seed * 1000 + k))
    elif cond == "R_bon":
        for k in range(N):
            out.append(qgen(P_BASE, f"SITUATION:\n{fr}", seed * 1000 + k))
    elif cond == "R4":
        out = r4_passes(fr, pass_cap)
    elif cond == "R1":                     # 2-stage: detect (1 call) -> reconstruct (N calls)
        defect = qgen(P_DETECT, f"SITUATION:\n{fr}", seed)
        u = f"SITUATION:\n{fr}\n\nDETECTED DEFECT:\n{defect}"
        for k in range(N):
            out.append(qgen(P_RECON, u, seed * 1000 + k))
    elif cond == "R3":                     # single-stage: detect+reconstruct in one step (distinct control, decorrelated seed)
        for k in range(N):
            out.append(qgen(P_R3_SINGLE, f"SITUATION:\n{fr}", seed * 2000 + k))
    else:
        raise ValueError(cond)
    return out[:N]

def candidates_r5(iid, seed, N, pass_cap, level):
    return r4_passes(lossy(T0[iid]["t0_stuck_frame"], level), pass_cap)[:N]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=44); ap.add_argument("--M", type=int, default=10)
    ap.add_argument("--pass-cap", type=int, default=4)
    ap.add_argument("--incidents", nargs="*", default=INCIDENTS)
    ap.add_argument("--conditions", nargs="*", default=["R0", "R1", "R2", "R3", "R4", "R_bon", "R5"])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=f"{EXP}/hbb_recon_exhibit_candidates.json")
    a = ap.parse_args()
    if a.smoke:
        a.N, a.M, a.incidents, a.conditions, a.out = 3, 1, ["HBB-08"], ["R0", "R2", "R4"], f"{EXP}/hbb_recon_exhibit_SMOKE.json"
    print(f"operators={len(OPERATORS)} N={a.N} M={a.M} pass_cap={a.pass_cap} incidents={a.incidents} conditions={a.conditions}", flush=True)
    rec = []
    for iid in a.incidents:
        for seed in range(a.M):
            for cond in a.conditions:
                if cond == "R5":
                    for lvl in ("L1", "L2", "L3"):
                        c = candidates_r5(iid, seed, a.N, a.pass_cap, lvl)
                        rec.append({"incident": iid, "seed": seed, "condition": f"R5-{lvl}", "n": len(c),
                                    "n_distinct": len(set(c)), "candidates": c})
                        print(f"  {iid} s{seed} R5-{lvl}: {len(c)} ({len(set(c))} distinct)", flush=True)
                else:
                    c = candidates_for(cond, iid, seed, a.N, a.pass_cap)
                    rec.append({"incident": iid, "seed": seed, "condition": cond, "n": len(c),
                                "n_distinct": len(set(c)), "candidates": c})
                    print(f"  {iid} s{seed} {cond}: {len(c)} ({len(set(c))} distinct)", flush=True)
    Path(a.out).write_text(json.dumps({"prereg_seal": "4cb77d89b30e682122d5f90806c1135e8034ea85cdf1cd82ac15577b45f23a01",
                                       "binding": "hbb_recon_impl_binding.json",
                                       "params": {"N": a.N, "M": a.M, "pass_cap": a.pass_cap, "operators": len(OPERATORS), "temp": TEMP},
                                       "records": rec}, ensure_ascii=False, indent=2))
    print("->", a.out, "| records:", len(rec))

if __name__ == "__main__":
    main()
