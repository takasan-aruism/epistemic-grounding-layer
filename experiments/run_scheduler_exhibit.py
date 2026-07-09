#!/usr/bin/env python3
"""Faithful STOP-SHIFT-RUN-COMPARE scheduler exhibit — generation harness (spec v0.1,
docs/scheduler_faithful_instrument_spec_v0.1.md; binding experiments/scheduler_construct_binding.json).
Target-blind (breakthrough_structure NEVER used here), cognition-agnostic (no v0.1 material). Emits the SAME
record format as the frozen exhibit so run_recon_score_qwen.py / build_recon_gpt_handoff.py / consensus reuse.
Conditions: R0 (base), RS (full scheduler, constructs 1-8), RS_pool (independence INVERTED = cumulative pooling
control), RS_flat (compare+rebuild ABSENT = views scored directly). PARALLELIZED at candidate level
(PROCESS-01 lesson: independent gen requests run concurrently; req/s derived from primitives)."""
import json, sys, argparse, urllib.request, hashlib, random, time, threading
import concurrent.futures as cf
from pathlib import Path
EXP = "/home/takasan/egl/experiments"
EP, MODEL = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
INCIDENTS = ["HBB-08", "HBB-10", "HBB-30"]
T0 = json.load(open(f"{EXP}/hbb_sealed_t0.json"))["packets"]

# --- generic, target-blind structural lenses (NO historical-target / cognition content) ---
LENS_POOL = [
    "substrate: what is the thing actually made of, or carried by?",
    "level: are you reasoning at the wrong level of description (object vs system vs protocol)?",
    "boundary: what is treated as fixed that is actually a choice?",
    "inversion: what if the assumed dependency runs the other way?",
    "temporal: is a static frame hiding a process or ordering?",
    "agent: who or what is the actor, and is it misassigned?",
    "constraint-as-variable: what constant is really a free parameter?",
    "kind: is the quantity or claim mis-typed (a category/unit error)?",
]

# --- frozen base prompts (parity with the closed exhibit R0) ---
P_BASE = "You are advising on an ongoing research project. What is the single most important thing to do next? Give one concrete alternative frame / next step."
P_SKEPTIC = "You are a skeptical research advisor. The current conclusion may be wrong. Name the frame defect and propose a concrete alternative frame that could be correct."

_calls = 0
_lock = threading.Lock()

def _sid(*parts):
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16) % 2_000_000_000

def qgen(sysp, user, seed, temp=0.9, mt=200):
    global _calls
    with _lock:
        _calls += 1
    b = json.dumps({"model": MODEL, "temperature": temp, "seed": int(seed), "max_tokens": mt,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": user}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=150) as r:
        return (json.load(r)["choices"][0]["message"].get("content") or "").strip()

# --- construct 3: sampled viewpoint shift (varies by seed AND attempt) ---
def sample_lenses(seed, attempt, V):
    rng = random.Random(_sid("lens", seed, attempt))
    return rng.sample(LENS_POOL, V)

# --- construct 1+4+5: short interrupted, independent reread of T0 only (prior only in RS_pool) ---
SYS_VIEW = ("You read a stuck research situation through ONE lens and give only your FIRST, rough, PARTIAL "
            "structural impression: one or two sentences. Then STOP. Do NOT resolve it, do NOT propose a full "
            "solution, do NOT conclude.")
def view_call(fr, lens, seed, prior=None):
    u = f"LENS: {lens}\n\nSITUATION (read this only):\n{fr}"
    if prior:  # RS_pool INVERSION only: cumulative pooling of prior views
        u += "\n\n[prior rough views, pooled]\n" + "\n".join(f"- {p[:160]}" for p in prior)
    return qgen(SYS_VIEW, u, seed, mt=70)

# --- construct 6: structural signature from the VIEW only ---
SYS_SIG = ("Reduce one rough partial impression to its structural signature. Output exactly one line: "
           "SUBJECT=<what it is about> | LEVEL=<level of description> | KEY-DISTINCTION=<the distinction it turns on>.")
def signature_call(view, seed):
    return qgen(SYS_SIG, f"IMPRESSION:\n{view}", seed, mt=60)

# --- construct 7: COMPARE over signatures only (name differences, pick no winner) ---
SYS_CMP = ("You are given several structural signatures from independent rough views of the SAME situation. "
           "Name the STRUCTURAL DIFFERENCES among them: where do they disagree on subject / level / key-distinction? "
           "List the deltas. Do NOT pick a best one. Do NOT restate the situation.")
def compare_call(sigs, seed):
    body = "\n".join(f"VIEW {i+1}: {s}" for i, s in enumerate(sigs))
    return qgen(SYS_CMP, f"SIGNATURES:\n{body}", seed, mt=140)

# --- construct 8a: REBUILD from differences (+T0 anchor), NOT from any view ---
SYS_REB = ("You rebuild ONE replacement frame for a stuck situation, driven by the STRUCTURAL DIFFERENCES found "
           "among rough views. Change the subject / level / key-distinction as the differences suggest, and give "
           "the next action that follows. Synthesize from the differences; do NOT restate any single view.")
def rebuild_call(deltas, fr, seed):
    u = f"SOURCE (anchor only):\n{fr}\n\nSTRUCTURAL DIFFERENCES AMONG ROUGH VIEWS:\n{deltas}\n\nOutput: the replacement frame + next action."
    return qgen(SYS_REB, u, seed, mt=200)

# --- construct 8b: bounded convergence (SELECT / HOLD-2 / SHIFT-AGAIN) ---
SYS_CHK = ("Does the replacement frame change the SUBJECT, LEVEL, or KEY-DISTINCTION relative to the source, or "
           "is it merely a restatement? Answer exactly CHANGED or HOLD.")
def check_call(rebuild, fr, seed):
    out = qgen(SYS_CHK, f"SOURCE:\n{fr[:300]}\n\nREPLACEMENT:\n{rebuild}", seed, mt=8).upper()
    return "HOLD" if "HOLD" in out and "CHANGED" not in out else "CHANGED"

def rs_run(fr, seed, V, pool=False, cap=2):
    """One RS candidate. pool=True => RS_pool (views cumulatively pooled = independence INVERTED)."""
    trace = {"attempts": []}
    rebuild = ""
    for attempt in range(1, cap + 1):
        lenses = sample_lenses(seed, attempt, V)
        views, prior = [], []
        for j, lens in enumerate(lenses):
            v = view_call(fr, lens, _sid("v", seed, attempt, j), prior=(prior if pool else None))
            views.append(v)
            if pool:
                prior.append(v)               # RS_pool ONLY: accumulate (the R4 inversion)
        sigs = [signature_call(v, _sid("s", seed, attempt, j)) for j, v in enumerate(views)]
        deltas = compare_call(sigs, _sid("c", seed, attempt))
        rebuild = rebuild_call(deltas, fr, _sid("r", seed, attempt))
        verdict = check_call(rebuild, fr, _sid("k", seed, attempt))
        trace["attempts"].append({"attempt": attempt, "lenses": lenses, "verdict": verdict})
        if verdict == "CHANGED":
            break                              # SELECT
        # else HOLD -> SHIFT-AGAIN with fresh lenses (bounded by cap = HOLD-2)
    trace["final_attempts"] = len(trace["attempts"])
    trace["resolved"] = trace["attempts"][-1]["verdict"] == "CHANGED"   # False => ESCALATE (HOLD-2 exhausted, unresolved)
    return rebuild, trace

def rs_flat_view(fr, seed, k):
    """RS_flat candidate = ONE independent short view (constructs 1-5 present; 6-8 ABSENT)."""
    lens = LENS_POOL[_sid("flatlens", seed, k) % len(LENS_POOL)]
    return view_call(fr, lens, _sid("flat", seed, k), prior=None)

def gen_candidate(job, V):
    cond, iid, seed, k = job
    fr = T0[iid]["t0_stuck_frame"]
    tr = None
    if cond == "R0":
        cand = qgen(P_BASE if k % 2 == 0 else P_SKEPTIC, f"SITUATION:\n{fr}", _sid("r0", seed, k), temp=0.9, mt=200)
    elif cond == "RS":
        cand, tr = rs_run(fr, _sid("RS", seed, k), V, pool=False)
    elif cond == "RS_pool":
        cand, tr = rs_run(fr, _sid("RSp", seed, k), V, pool=True)
    elif cond == "RS_flat":
        cand = rs_flat_view(fr, seed, k)
    else:
        raise ValueError(cond)
    return {"incident": iid, "condition": cond, "seed": seed, "cand_idx": k, "candidate": cand, "trace": tr}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=6); ap.add_argument("--M", type=int, default=10)
    ap.add_argument("--V", type=int, default=3); ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--incidents", nargs="*", default=INCIDENTS)
    ap.add_argument("--conditions", nargs="*", default=["R0", "RS", "RS_pool", "RS_flat"])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default=f"{EXP}/scheduler_exhibit_candidates.json")
    ap.add_argument("--trace-out", default=f"{EXP}/scheduler_exhibit_trace.json")
    a = ap.parse_args()
    if a.smoke:
        a.N, a.M, a.V, a.incidents = 2, 1, 2, ["HBB-08"]
        a.out, a.trace_out = f"{EXP}/scheduler_exhibit_SMOKE.json", f"{EXP}/scheduler_exhibit_SMOKE_trace.json"
    jobs = [(cond, iid, seed, k) for iid in a.incidents for seed in range(a.M)
            for cond in a.conditions for k in range(a.N)]
    print(f"conditions={a.conditions} incidents={a.incidents} N={a.N} M={a.M} V={a.V} workers={a.workers} | {len(jobs)} candidate jobs", flush=True)
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(lambda j: gen_candidate(j, a.V), jobs))
    dt = time.time() - t0
    # group into scorer record format
    from collections import defaultdict
    grp = defaultdict(list)
    for r in results:
        grp[(r["incident"], r["seed"], r["condition"])].append(r)
    records, traces = [], []
    for (iid, seed, cond), rs in sorted(grp.items()):
        rs.sort(key=lambda x: x["cand_idx"])
        cands = [x["candidate"] for x in rs]
        records.append({"incident": iid, "seed": seed, "condition": cond, "n": len(cands),
                        "n_distinct": len(set(cands)), "candidates": cands})
        for x in rs:
            if x["trace"] is not None:
                traces.append({"opaque_id": hashlib.sha256(f'{iid}|{cond}|{seed}|{x["cand_idx"]}'.encode()).hexdigest()[:14],
                               "incident": iid, "condition": cond, "seed": seed, "cand_idx": x["cand_idx"], "trace": x["trace"]})
    # PROCESS-01: derive throughput from primitives, do not trust GPU-util
    reqs = _calls / dt if dt else 0
    proc = {"total_llm_calls": _calls, "wall_seconds": round(dt, 1), "req_per_s": round(reqs, 2),
            "workers": a.workers, "note": "req/s derived from request primitives (PROCESS-01); not GPU-util."}
    Path(a.out).write_text(json.dumps({"object": "SCHEDULER_EXHIBIT_CANDIDATES", "spec": "scheduler_faithful_instrument_spec_v0.1.md",
                                       "binding": "scheduler_construct_binding.json", "target_blind": True,
                                       "params": {"N": a.N, "M": a.M, "V": a.V, "lens_pool": len(LENS_POOL)},
                                       "process": proc, "records": records}, ensure_ascii=False, indent=2))
    Path(a.trace_out).write_text(json.dumps({"object": "SCHEDULER_EXHIBIT_TRACE", "traces": traces}, ensure_ascii=False, indent=2))
    print(f"-> {a.out} | records={len(records)} | calls={_calls} wall={dt:.1f}s req/s={reqs:.2f}", flush=True)

if __name__ == "__main__":
    main()
