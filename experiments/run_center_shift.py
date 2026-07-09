#!/usr/bin/env python3
"""Center-shift effect construct test (frozen prereg v0.1, seal 7bceee2e). CONTROL vs ATTENTION-SWEEP vs
ATTENTION-RANDOM on HBB-30. Same-system invariant: ONE system prompt / task / source / decoding; the ONLY
cross-condition difference is the appended center line. Target-blind: mechanical sentence regions, all swept, no
selection; rubric is scorer-only (Claude excluded). Modes: gen / score / decide. PROCESS-01: logs wall/calls."""
import json, sys, re, math, random, argparse, time, hashlib, threading, urllib.request
import concurrent.futures as cf
from pathlib import Path
EXP = "/home/takasan/egl/experiments"
EP, MODEL = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"

# --- FROZEN PARAMS (prereg 7bceee2e) ---
INCIDENT = "HBB-30"
M = 10                 # seeds per (condition, region)
TEMP = 0.8
GEN_MT = 350           # matched max_tokens (same across all conditions)
SEED_BASE = 20260710
RAND_SEED = 20260710   # random-span offset seed (fixed, auditable)
ALPHA = 0.05
# same-system: ONE neutral system prompt + task lives inside the source frame (identical across conditions)
SYSTEM = "You are a research advisor. Carry out the task described in the situation."
CENTER_TMPL = "OBSERVATION CENTER (verbatim, already in the source above): {span}. Keep the same task and the same rules."
# scorer-only rubric (NEVER shown to the generator)
SCORE_SYS = ("You judge whether a research answer contains a DISCRIMINATING OBSERVATION about the evidential status "
             "of a stated numeric claim. Reference (correct direction): the approximately-6x figure is a DECLARED / "
             "reported historical claim whose derivation and provenance are not recovered; the correct handling treats "
             "it as an unverified claim to be superseded by later evidence, not as a result whose derivation must exist. "
             "Score the ANSWER only: 0 = accepts the 6x as given and merely explains/derives it (no status observation); "
             "1 = partial (hints the figure may be unverified / needs provenance but does not commit); 2 = decisive "
             "(treats 6x as DECLARED/unverified / provenance-unrecovered / to be superseded). Return ONLY JSON {\"NDO\":0|1|2}.")

_calls = 0
_lock = threading.Lock()

def qgen(system, user, seed, temp=TEMP, mt=GEN_MT):
    global _calls
    with _lock: _calls += 1
    b = json.dumps({"model": MODEL, "temperature": temp, "seed": int(seed), "max_tokens": mt,
                    "chat_template_kwargs": {"enable_thinking": False},
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(EP, data=b, headers={"Content-Type": "application/json"}), timeout=150) as r:
        return (json.load(r)["choices"][0]["message"].get("content") or "").strip()

def source_frame():
    return json.load(open(f"{EXP}/hbb_sealed_t0.json"))["packets"][INCIDENT]["t0_stuck_frame"]

def regions(fr):
    """R1: mechanical sentence split (regex boundary), verbatim, no field labels, no human pick."""
    return [s.strip() for s in re.split(r"(?<=\.)\s+", fr) if s.strip()]

def random_spans(fr, regs):
    """N2: contiguous substrings length-matched to each region, seed-fixed offsets (deterministic/auditable)."""
    rng = random.Random(RAND_SEED); spans = []
    for k, reg in enumerate(regs):
        L = len(reg); hi = max(0, len(fr) - L)
        off = rng.randint(0, hi) if hi > 0 else 0
        spans.append(fr[off:off + L])
    return spans

def build_user(fr, center_span=None):
    """SAME source+task; the ONLY variable is the appended center line (None for CONTROL)."""
    u = f"SITUATION:\n{fr}"
    if center_span is not None:
        u += "\n\n" + CENTER_TMPL.format(span=center_span)
    return u

def opq(cond, idx, m):
    return hashlib.sha256(f"{cond}|{idx}|{m}".encode()).hexdigest()[:14]

def gen_jobs(fr, regs, rspans, Mval):
    jobs = []
    for m in range(Mval):
        jobs.append(("CONTROL", -1, m, None))
        for k in range(len(regs)):
            jobs.append(("SWEEP", k, m, regs[k]))
            jobs.append(("RANDOM", k, m, rspans[k]))
    return jobs

def do_gen(fr, job):
    cond, idx, m, span = job
    seed = SEED_BASE + {"CONTROL": 0, "SWEEP": 1, "RANDOM": 2}[cond] * 100000 + (idx + 1) * 1000 + m
    text = qgen(SYSTEM, build_user(fr, span), seed)
    return {"opaque_id": opq(cond, idx, m), "condition": cond, "region_idx": idx, "m": m,
            "center_span": span, "seed": seed, "text": text}

def jx(t):
    i, j = t.find("{"), t.rfind("}")
    try: return json.loads(t[i:j + 1]) if 0 <= i < j else {}
    except Exception: return {}

def score_one(rec):
    d = jx(qgen(SCORE_SYS, f"ANSWER:\n{rec['text'][:1200]}\n\nReturn the JSON.", seed=0, temp=0, mt=16))
    v = d.get("NDO"); v = v if v in (0, 1, 2) else 0
    return {"opaque_id": rec["opaque_id"], "NDO": v}   # condition NOT included -> scorer stays blind

def binom_tail(k, n, p):
    if p <= 0: return 1.0 if k == 0 else 0.0
    if p >= 1: return 1.0
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=["gen", "score", "decide", "precheck"], required=True)
    ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
    fr = source_frame(); regs = regions(fr); rspans = random_spans(fr, regs)
    Mval = 2 if a.smoke else M
    if a.mode == "precheck":
        # frozen RANDOM-overlap pre-check (auditable): does any random span overlap R0 or the "6x" token?
        r0 = regs[0]
        out = [{"k": k, "len": len(s), "overlaps_R0_text": (s in r0 or r0 in s),
                "contains_6x": ("6x" in s)} for k, s in enumerate(rspans)]
        print("RANDOM-overlap pre-check:", json.dumps(out)); return
    t0 = time.time()
    if a.mode == "gen":
        jobs = gen_jobs(fr, regs, rspans, Mval)
        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            recs = list(ex.map(lambda j: do_gen(fr, j), jobs))
        out = {"object": "CENTER_SHIFT_CANDIDATES", "seal": "7bceee2e", "incident": INCIDENT, "M": Mval,
               "regions": regs, "random_spans": rspans, "system": SYSTEM, "center_template": CENTER_TMPL,
               "process": {"wall_seconds": round(time.time() - t0, 1), "gen_calls": _calls, "note": "PROCESS-01"},
               "records": recs}
        Path(f"{EXP}/center_shift_candidates{'_SMOKE' if a.smoke else ''}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print(f"gen -> {len(recs)} records, wall={time.time()-t0:.1f}s calls={_calls}")
    elif a.mode == "score":
        doc = json.load(open(f"{EXP}/center_shift_candidates{'_SMOKE' if a.smoke else ''}.json"))
        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            scores = list(ex.map(score_one, doc["records"]))
        Path(f"{EXP}/center_shift_scores{'_SMOKE' if a.smoke else ''}.json").write_text(
            json.dumps({"object": "CENTER_SHIFT_SCORES", "scorer": "Qwen blind, condition-withheld, Claude excluded",
                        "process": {"wall_seconds": round(time.time() - t0, 1), "score_calls": _calls}, "scores": scores}, indent=2))
        print(f"score -> {len(scores)} scored, wall={time.time()-t0:.1f}s")
    elif a.mode == "decide":
        doc = json.load(open(f"{EXP}/center_shift_candidates.json"))
        sc = {s["opaque_id"]: s["NDO"] for s in json.load(open(f"{EXP}/center_shift_scores.json"))["scores"]}
        by = {"CONTROL": [], "SWEEP": [], "RANDOM": []}
        per_region = {}
        for r in doc["records"]:
            ndo = sc.get(r["opaque_id"], 0); by[r["condition"]].append(ndo)
            if r["condition"] == "SWEEP":
                per_region.setdefault(r["region_idx"], []).append(ndo)
        def pdisc(v): return sum(1 for x in v if x >= 1) / len(v) if v else 0.0
        def pdec(v): return sum(1 for x in v if x == 2) / len(v) if v else 0.0
        c, sw, rd = by["CONTROL"], by["SWEEP"], by["RANDOM"]
        k_sw = sum(1 for x in sw if x >= 1)
        p_binom = binom_tail(k_sw, len(sw), pdisc(c))
        sweep_gt_control = pdisc(sw) > pdisc(c) and p_binom < ALPHA
        sweep_ge_random = pdisc(sw) >= pdisc(rd)
        confirmed = sweep_gt_control and sweep_ge_random
        out = {"object": "CENTER_SHIFT_RESULT", "seal": "7bceee2e", "incident": INCIDENT, "alpha": ALPHA,
               "p_disc": {"CONTROL": round(pdisc(c), 3), "SWEEP": round(pdisc(sw), 3), "RANDOM": round(pdisc(rd), 3)},
               "p_dec": {"CONTROL": round(pdec(c), 3), "SWEEP": round(pdec(sw), 3), "RANDOM": round(pdec(rd), 3)},
               "n": {"CONTROL": len(c), "SWEEP": len(sw), "RANDOM": len(rd)},
               "H_center_shift": {"sweep_gt_control_binom_p": round(p_binom, 5), "sweep_gt_control": sweep_gt_control,
                                  "sweep_ge_random": sweep_ge_random, "confirmed": confirmed,
                                  "claim_if_positive": "observation-center shift can alter produced discriminating observations under a preserved reasoning system"},
               "per_region_sweep_p_disc": {f"R{k}": round(pdisc(v), 3) for k, v in sorted(per_region.items())},
               "R0_interpretive_note": "if the effect is driven by R0 alone (R1-R3 not > RANDOM), read as 'attention to the pre-existing attribution sentence', NOT center-coherence, NOT salience-selection",
               "random_overlap_precheck": [{"k": k, "overlaps_R0": (s in regs[0] or regs[0] in s), "contains_6x": "6x" in s} for k, s in enumerate(doc["random_spans"])]}
        Path(f"{EXP}/center_shift_result_v0.1.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
        print("H_center_shift confirmed:", confirmed)
        print(f"  p_disc CONTROL={pdisc(c):.2f} SWEEP={pdisc(sw):.2f} RANDOM={pdisc(rd):.2f} | binom p(SWEEP>CONTROL)={p_binom:.4g} | SWEEP>=RANDOM={sweep_ge_random}")
        print("  per-region SWEEP p_disc:", {f"R{k}": round(pdisc(v), 2) for k, v in sorted(per_region.items())})

if __name__ == "__main__":
    main()
