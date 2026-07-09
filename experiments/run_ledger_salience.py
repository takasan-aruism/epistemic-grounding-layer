#!/usr/bin/env python3
"""Minimum temporal-salience prototype (LEDGER CATEGORY STREAM ADAPTER, v0.1).
Target-blind. Applies FROZEN ESDE-derived salience primitives to the append-ordered categorical stream of
DESIGN_EVIDENCE_LEDGER.jsonl and compares to a COUNT-PRESERVING ORDER-SHUFFLE null. Tests only H_salience_structure
(temporal salience structure beyond count-matched null). NO SHAKE label, NO category->value encoding, NO
known-incident positions used. Contract=ledger_stream_contract_v0.1.json, binding=ledger_salience_construct_binding_v0.1.json,
prereg=docs/ledger_salience_prereg_v0.1.md. PROCESS-01: logs wall/primitive-counts/null-count."""
import json, sys, math, random, argparse, time, hashlib
from collections import Counter
LEDGER = "/home/takasan/egl/DESIGN_EVIDENCE_LEDGER.jsonl"
EXP = "/home/takasan/egl/experiments"

# --- FROZEN PARAMS (prereg) ---
W = 10            # window-distribution window
EWMA_ALPHA = 0.3  # self-history deviation
WARMUP = 10       # causal warmup (z=0 during)
L0 = 3            # persistent-segment min run length
N_NULL = 2000     # order-shuffle null count
SEED = 20260710   # frozen null seed (no Date.now)
ENT_BASE = 2      # entropy base
ALPHA = 0.05
PRIMARY_STREAM = "evidence_class"
PRIMARY_METRICS = ["max_run", "n_runs_ge3", "uppertail_run_mass", "max_causal_entropy_z"]
# --- INPUT PIN (reproducibility fix, DE-0132): pin to the sealed snapshot; the prototype's own result
#     entries must never enter their own input (self-reference). Only input selection is pinned here;
#     no detector/normalization/primitive/threshold/window/null/metric is changed. ---
N_SEALED = 130     # ledger length at prereg freeze (270196d4)
STREAM_SHA256 = "82051d270e8b5dafac0a582462011e5e12904bdc7babc723af7cecf1dad4c7ad"  # sha256 of sealed evidence_class stream
SELF_ENTRY_CLASSES = {"PROTOTYPE_RESULT", "LEDGER_SALIENCE_REPRODUCIBILITY_DEFECT"}  # this prototype's own appends

_prim_calls = Counter()

# --- data extraction / normalization contract (mechanical only) ---
def load_stream(field):
    rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
    # input pin: every entry BEYOND the sealed snapshot must be one of THIS prototype's own appends
    # (self-reference guard); a real research entry appended later trips this and forces a pin review.
    for r in rows[N_SEALED:]:
        ec = (r.get("evidence_class") or "").strip().upper()
        assert ec in SELF_ENTRY_CLASSES, f"non-self entry beyond sealed snapshot: {r.get('design_evidence_id')} [{ec}] — pin needs review"
    rows = rows[:N_SEALED]
    out = []
    for r in rows:
        if field == "evidence_class":
            v = r.get("evidence_class")
            sym = (v if v is not None else "MISSING")
        elif field == "decision_head":
            v = r.get("decision")
            sym = ((v if v is not None else "MISSING").split("_")[0])
        else:
            raise ValueError(field)
        out.append(str(sym).strip().upper())   # verbatim -> strip -> upper. NO semantic merge.
    if field == "evidence_class":              # verify pinned stream matches the sealed hash
        h = hashlib.sha256("\n".join(out).encode()).hexdigest()
        assert h == STREAM_SHA256, f"sealed stream hash mismatch: {h}"
    return out

# --- representations (structural on symbols; never a value on a category) ---
def runs_of(seq, cat):
    _prim_calls["runs"] += 1
    r, cur = [], 0
    for s in seq:
        if s == cat: cur += 1
        elif cur: r.append(cur); cur = 0
    if cur: r.append(cur)
    return r

def all_runs(seq):
    return [ln for cat in set(seq) for ln in runs_of(seq, cat)]

def recurrence_intervals(seq, cat):
    _prim_calls["recurrence"] += 1
    idx = [i for i, s in enumerate(seq) if s == cat]
    return [b - a for a, b in zip(idx, idx[1:])]

def window_entropy_series(seq, w=W):
    _prim_calls["window_entropy"] += 1
    out = []
    for t in range(len(seq) - w + 1):
        c = Counter(seq[t:t + w]); n = sum(c.values())
        h = -sum((k / n) * math.log(k / n, ENT_BASE) for k in c.values())
        out.append(h)
    return out

# --- salience primitives (FROZEN; ESDE math unchanged) ---
def causal_ewma_z(series, alpha=EWMA_ALPHA, warmup=WARMUP):
    """A: self-history deviation, PAST-ONLY (index<t). No future leakage."""
    _prim_calls["ewma_z"] += 1
    mean = var = None; zs = []
    for i, x in enumerate(series):
        if i < warmup or mean is None:
            zs.append(0.0)
            if mean is None: mean, var = x, 0.0
            else:
                d = x - mean; mean += d / (i + 1); var = (1 - alpha) * (var + alpha * d * d)
            continue
        std = math.sqrt(var) if var > 1e-9 else 1e-9
        zs.append((x - mean) / std)                 # z computed BEFORE updating with x_t
        d = x - mean; mean += alpha * d; var = (1 - alpha) * (var + alpha * d * d)
    return zs

def two_sided_rarity(vals):
    """B: two-sided percentile rarity, high AND low preserved."""
    _prim_calls["rarity"] += 1
    n = len(vals)
    if n == 0: return []
    order = sorted(range(n), key=lambda i: vals[i])
    pct = [0.0] * n
    for rank, i in enumerate(order): pct[i] = (rank + 0.5) / n
    return [-math.log10(max(2 * min(p, 1 - p), 1.0 / (2 * n))) for p in pct]

# --- primary metrics (pre-fixed) ---
def compute_metrics(seq):
    ar = all_runs(seq)
    max_run = max(ar) if ar else 0
    n_runs_ge3 = sum(1 for x in ar if x >= L0)
    ar_sorted = sorted(ar, reverse=True)
    top = ar_sorted[:max(1, len(ar_sorted) // 10)]
    uppertail_run_mass = sum(top)
    ent = window_entropy_series(seq)
    zc = causal_ewma_z(ent)
    max_causal_entropy_z = max((abs(z) for z in zc), default=0.0)
    return {"max_run": max_run, "n_runs_ge3": n_runs_ge3,
            "uppertail_run_mass": uppertail_run_mass, "max_causal_entropy_z": max_causal_entropy_z}

# --- power / censoring pre-audit (deliverable 6) ---
def power_audit(field):
    seq = load_stream(field); N = len(seq); c = Counter(seq); V = len(c)
    ge3 = [k for k, n in c.items() if n >= 3]
    singles = [k for k, n in c.items() if n == 1]
    eff_hist = {k: {"count": n, "run_computable": n >= 2, "recurrence_computable": n >= 2,
                    "persistence_ge3_possible": n >= 3} for k, n in c.most_common()}
    return {"field": field, "total_length": N, "vocab": V,
            "singletons": len(singles), "rare_le2_cats": sum(1 for k, n in c.items() if n <= 2),
            "rare_le2_share_of_stream": round(sum(n for k, n in c.items() if n <= 2) / N, 3),
            "cats_with_power_ge3": len(ge3), "cats_ge3": sorted(ge3, key=lambda k: -c[k]),
            "dominant_share": round(c.most_common(1)[0][1] / N, 3),
            "missing": c.get("MISSING", 0),
            "window_series_len": max(0, N - W + 1),
            "early_sequence_censoring": f"causal EWMA-z silent for first {WARMUP} window-points (z=0)",
            "recurrence_right_censoring": "final occurrence of each category has no closing interval (dropped)",
            "signal0_vs_nopower_rule": {
                "run/persistence": "count<2 => NO POWER (not 'normal'); count>=3 required for persistence_ge3",
                "recurrence": "count<2 => NO POWER; right-censored last interval excluded",
                "self_history_z": "first WARMUP points => NO POWER (z=0 by construction)"},
            "effective_history_per_category": eff_hist}

def empirical_p(real, nulls):   # one-sided upper: fraction of null >= real
    return (1 + sum(1 for x in nulls if x >= real)) / (1 + len(nulls))

def secondary_report(seq):
    """REPORTED-ONLY (not in the decision). Wires R2 recurrence-interval + B two-sided rarity (both tails)
    for the powered categories (count>=3), plus premise-drift (window-entropy trend). Prereg measurement audit."""
    c = Counter(seq)
    powered = [k for k, n in c.most_common() if n >= 3]
    rec = {}
    for cat in powered:
        iv = recurrence_intervals(seq, cat)          # R2 (last occurrence right-censored)
        rar = two_sided_rarity(iv)                    # B (both tails)
        med = sorted(iv)[len(iv) // 2] if iv else None
        hi = [r for r, x in zip(rar, iv) if med is not None and x > med]   # long-gap (upper) tail
        lo = [r for r, x in zip(rar, iv) if med is not None and x < med]   # short-gap (lower) tail
        rec[cat] = {"n_intervals": len(iv), "intervals": iv, "median_interval": med,
                    "rarity_high_tail_max": round(max(hi), 4) if hi else None,   # unusually long gaps
                    "rarity_low_tail_max": round(max(lo), 4) if lo else None,    # unusually short gaps
                    "rarity": [round(x, 4) for x in rar]}
    ent = window_entropy_series(seq)
    half = len(ent) // 2
    drift = {"premise_drift": "window-entropy mean, first vs second half (reported, not decided)",
             "entropy_mean_first_half": round(sum(ent[:half]) / half, 4) if half else None,
             "entropy_mean_second_half": round(sum(ent[half:]) / (len(ent) - half), 4) if len(ent) - half else None}
    return {"note": "REPORTED-ONLY, NOT in H_salience_structure decision", "powered_categories": powered,
            "recurrence_rarity_two_sided": rec, "entropy_drift": drift}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["power_audit", "run"], required=True)
    a = ap.parse_args()
    t0 = time.time()
    if a.mode == "power_audit":
        out = {"object": "LEDGER_SALIENCE_POWER_AUDIT", "version": "v0.1", "params": {"W": W, "WARMUP": WARMUP, "L0": L0},
               "primary": power_audit(PRIMARY_STREAM), "secondary": power_audit("decision_head")}
        open(f"{EXP}/ledger_salience_power_audit_v0.1.json", "w").write(json.dumps(out, indent=2))
        print("power_audit -> ledger_salience_power_audit_v0.1.json")
        print(f"  primary({PRIMARY_STREAM}): N={out['primary']['total_length']} vocab={out['primary']['vocab']} "
              f"cats_ge3={out['primary']['cats_with_power_ge3']} rare_share={out['primary']['rare_le2_share_of_stream']}")
        return
    # mode == run (HELD until independent construct audit passes)
    seq = load_stream(PRIMARY_STREAM)
    real = compute_metrics(seq)
    rng = random.Random(SEED)
    null_dists = {m: [] for m in PRIMARY_METRICS}
    for _ in range(N_NULL):
        sh = seq[:]; rng.shuffle(sh)               # count-preserving order shuffle
        m = compute_metrics(sh)
        for k in PRIMARY_METRICS: null_dists[k].append(m[k])
    a_corr = ALPHA / len(PRIMARY_METRICS)
    rows = {}
    for m in PRIMARY_METRICS:
        p = empirical_p(real[m], null_dists[m])
        rows[m] = {"real": real[m], "null_mean": round(sum(null_dists[m]) / N_NULL, 4),
                   "null_p95": sorted(null_dists[m])[int(0.95 * N_NULL)], "p_one_sided": round(p, 5),
                   "sig_bonf": p < a_corr}
    confirmed = any(r["sig_bonf"] for r in rows.values())
    dt = time.time() - t0
    out = {"object": "LEDGER_SALIENCE_RESULT", "version": "v0.1", "primary_stream": PRIMARY_STREAM,
           "params": {"W": W, "EWMA_ALPHA": EWMA_ALPHA, "WARMUP": WARMUP, "L0": L0, "N_NULL": N_NULL,
                      "SEED": SEED, "alpha": ALPHA, "bonferroni_alpha": a_corr, "null": "count-preserving order-shuffle"},
           "H_salience_structure": {"confirmed": confirmed, "per_metric": rows,
               "claim_if_positive": "ledger stream contains non-random temporal salience structure detectable by reused ESDE primitives",
               "claim_if_negative": "A-adapter / current ledger stream did NOT detect useful temporal salience structure"},
           "measurement_audit_secondary": secondary_report(seq),
           "process": {"wall_seconds": round(dt, 2), "n_null": N_NULL, "primitive_calls": dict(_prim_calls),
                       "note": "PROCESS-01: derived from primitives"}}
    open(f"{EXP}/ledger_salience_result_v0.1.json", "w").write(json.dumps(out, indent=2))
    print("H_salience_structure confirmed:", confirmed)
    for m, r in rows.items():
        print(f"  {m}: real={r['real']} null_mean={r['null_mean']} p={r['p_one_sided']} sig={r['sig_bonf']}")
    print(f"process: wall={dt:.1f}s n_null={N_NULL} calls={dict(_prim_calls)}")

if __name__ == "__main__":
    main()
