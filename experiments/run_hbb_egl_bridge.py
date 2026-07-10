"""HBB-EXHIBIT -> EGL UNRESOLVED BRIDGE (offline replay) — implements sealed design v0.2.

Seal: docs/hbb_egl_bridge_prereg_v0.2.md sha256 c9fedde054898acfc3fcaa55653e5545523bcf36bfee8f23db507a029d50a72d

Hands frozen HBB-30 exhibit rebuild-candidate text to the EXISTING live EGL answer contract
(egl.self_grounding.answer_question + validate_answer) so an answer candidate + unresolved material
are co-exposed. Format+provenance wiring only. Creates NO Claim; calls NO admission gate; adds NO
always-on observer. Attention Center / same-object binding / Aruism / structural re-centering = UNOWNED, not built.

FIX-1 force_include=[all ids] + coverage assert (no silent drop).  FIX-2 records non-empty (no load_corpus self-ref).
FIX-3 open_gaps NOT claimed grounded.  FIX-4 superseded={} (no supersession bleed).  FIX-5 batch if ctx<~64K, logged.
record_char_limit set >= longest candidate so the prompt view is not truncated (re-audit residual fix).
"""
import sys, os, json, hashlib, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from egl.self_grounding import answer_question, validate_answer

EXP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(EXP)

# --- pinned inputs (offline replay contract v0.2; DE-0132 no self-reference) ---
PIN_CANDIDATES = "b7c98296a3249ec86a73d9341a1975e863dfa800ec735b5d8672d4a4d032c74b"
PIN_SUBSET     = "9e1ca25b1f060109b9b340b008056e99f87822cc6015a1334487737b9a4f49d2"
PIN_T0FRAME    = "bc09d36ddfbcdb99fdc38adfa61477e33a7a489b88d64c3c4dc5c5f466db7ea0"
INCIDENT = "HBB-30"
SOURCE_CLASS = "HBB_EXHIBIT_INTERMEDIATE"   # contextual, non-authoritative
ORIGIN_STAGE = "rebuild_out"
CTX_MIN_SINGLE_CALL = 64000                 # FIX-5 threshold

# neutral system prompt — NO rubric vocabulary (no DETECTION/RECONSTRUCTION/6x-correct/REC2), NO correctness scoring
SYS_NEUTRAL = (
    "You are given RECORDS: generated intermediate reconstruction texts produced by a processing run over ONE "
    "situation, each with a record_id. Using ONLY the provided records (no outside knowledge), return a structured "
    "answer to the QUESTION. Produce two things clearly separated: (a) the answer candidate(s) the records support, "
    "and (b) the considerations that remain UNRESOLVED / not settled by the records. Do NOT collapse the unresolved "
    "considerations into the answer. Return ONLY a JSON object with keys: "
    "answer_claims (list of {text, record_ids, currentness:CURRENT|HISTORICAL}) — every entry MUST cite >=1 record_id; "
    "historical_claims (list of {text, record_ids, superseded_by}); "
    "open_gaps (list of strings) — the unresolved considerations; "
    "source_trace (list of record_id). Cite only provided record_ids."
)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def load_pinned():
    craw = open(f"{EXP}/scheduler_exhibit_candidates.json", "rb").read()
    assert sha256_bytes(craw) == PIN_CANDIDATES, "PIN FAIL: scheduler_exhibit_candidates.json"
    cand = json.loads(craw)
    recs = [r for r in cand["records"] if r.get("incident") == INCIDENT]
    canon = json.dumps(recs, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert sha256_bytes(canon) == PIN_SUBSET, "PIN FAIL: HBB-30 subset"
    t0 = json.load(open(f"{EXP}/hbb_sealed_t0.json"))["packets"][INCIDENT]["t0_stuck_frame"]
    assert sha256_bytes(t0.encode()) == PIN_T0FRAME, "PIN FAIL: t0_stuck_frame"
    return recs, t0


def adapt(recs):
    """format+provenance ONLY. No semantic verdict. text byte-identical."""
    out = []
    for r in recs:
        iid, cond, seed = r["incident"], r["condition"], r["seed"]
        for cand_idx, text in enumerate(r["candidates"]):
            mid = hashlib.sha256(f"{iid}|{cond}|{seed}|{cand_idx}".encode()).hexdigest()[:14]
            out.append({
                "record_id": mid, "source_class": SOURCE_CLASS, "ordinal": len(out),
                "text": text,   # byte-identical
                "provenance": {"artifact": "scheduler_exhibit_candidates.json", "incident": iid,
                               "condition": cond, "seed": seed, "cand_idx": cand_idx,
                               "origin_stage": ORIGIN_STAGE, "run_ref": PIN_CANDIDATES},
                # parent_ref intentionally OMITTED (compare-stage deltas ephemeral)
            })
    return out


def run_batch(question, records, tag):
    """One existing-mechanism answer_question call + FIX-1 coverage assert + validate_answer."""
    assert isinstance(records, list) and len(records) > 0, "FIX-2: records must be a non-empty list"
    all_ids = [r["record_id"] for r in records]
    rcl = max(len(r["text"]) for r in records) + 16   # residual fix: no prompt-layer truncation
    ans, retrieved_ids, raw = answer_question(
        question, records=records, superseded={},        # FIX-4
        system=SYS_NEUTRAL, k=len(records),               # feed all
        force_include=all_ids,                            # FIX-1: defeat retrieve() score>0 drop
        record_char_limit=rcl, max_tokens=6000)
    dropped = sorted(set(all_ids) - set(retrieved_ids))   # FIX-1: coverage assert, logged
    coverage_ok = (set(retrieved_ids) == set(all_ids))
    val = validate_answer(ans, all_ids) if isinstance(ans, dict) else None
    print(f"[{tag}] fed={len(all_ids)} retrieved={len(set(retrieved_ids))} coverage_ok={coverage_ok} "
          f"dropped={len(dropped)} rcl={rcl} "
          f"answer_dict={'ok' if isinstance(ans, dict) else 'NONE('+str(raw)[:60]+')'}", flush=True)
    if not coverage_ok:
        print(f"[{tag}] !! COVERAGE SHORTFALL dropped_ids={dropped}", flush=True)
    return {"tag": tag, "n_fed": len(all_ids), "n_retrieved": len(set(retrieved_ids)),
            "coverage_ok": coverage_ok, "dropped_ids": dropped, "record_char_limit": rcl,
            "answer": ans, "validate": val, "raw_present": bool(raw), "record_ids": all_ids}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{EXP}/hbb_egl_bridge_replay_result.json")
    ap.add_argument("--ctx", type=int, default=32768, help="served max_model_len (probed)")
    a = ap.parse_args()

    recs, t0 = load_pinned()
    records = adapt(recs)
    conditions = sorted({r["condition"] for r in recs})
    total_chars = sum(len(r["text"]) for r in records)
    approx_tokens = total_chars // 4
    single_call = a.ctx >= CTX_MIN_SINGLE_CALL and approx_tokens < a.ctx
    print(f"pins OK | HBB-30 records={len(recs)} candidates={len(records)} chars={total_chars} "
          f"~tokens={approx_tokens} ctx={a.ctx} conditions={conditions}", flush=True)

    batches = []
    if single_call:
        print("FIX-5: single call (ctx sufficient)", flush=True)
        batches.append(("ALL", records))
    else:
        print(f"FIX-5: LOGGED per-condition batching (ctx {a.ctx} < {CTX_MIN_SINGLE_CALL} or ~tokens>{a.ctx}); "
              f"{len(conditions)} calls", flush=True)
        for c in conditions:
            batches.append((c, [r for r in records if r["provenance"]["condition"] == c]))

    results = [run_batch(t0, recs_b, tag) for tag, recs_b in batches]

    # aggregate dual render (union; provenance kept per-condition in JSON)
    ans_claims, open_gaps = [], []
    for res in results:
        a2 = res["answer"] if isinstance(res["answer"], dict) else {}
        for c in (a2.get("answer_claims") or []):
            if isinstance(c, dict) and c.get("text"):
                ans_claims.append({"text": c["text"], "record_ids": c.get("record_ids"), "batch": res["tag"]})
        for g in (a2.get("open_gaps") or []):
            if g:
                open_gaps.append({"gap": g, "batch": res["tag"]})

    out = {"object": "HBB_EGL_BRIDGE_REPLAY_RESULT", "design_seal": "c9fedde0...v0.2",
           "pins": {"candidates": PIN_CANDIDATES, "subset": PIN_SUBSET, "t0_frame": PIN_T0FRAME},
           "mode": "single_call" if single_call else "per_condition_batched",
           "ctx": a.ctx, "conditions": conditions,
           "coverage_all_ok": all(r["coverage_ok"] for r in results),
           "n_candidates": len(records), "batches": results,
           "aggregate_dual_output": {"answer_claims": ans_claims, "open_gaps": open_gaps},
           "claim_ceiling": "wiring feasibility only; NO HBB-30 solved / REC2 / Attention-Center / structural re-centering"}
    open(a.out, "w").write(json.dumps(out, ensure_ascii=False, indent=2))

    print("\n==================== USER-FACING DUAL OUTPUT (aggregate) ====================")
    print("ANSWER (candidate; not adjudicated — user is final authority):")
    for c in ans_claims[:8]:
        print(f"  - [{c['batch']}] {c['text'][:200]}")
    if len(ans_claims) > 8:
        print(f"    (+{len(ans_claims)-8} more answer_claims)")
    print("\nOPEN / UNRESOLVED (not merged into the answer; NOT mechanically grounded):")
    seen = set()
    for g in open_gaps:
        key = g["gap"][:80]
        if key in seen:
            continue
        seen.add(key)
        print(f"  - [{g['batch']}] {g['gap'][:200]}")
    print("============================================================================")
    print(f"\n-> {a.out} | mode={out['mode']} | coverage_all_ok={out['coverage_all_ok']} | "
          f"answer_claims={len(ans_claims)} open_gaps={len(open_gaps)}")


if __name__ == "__main__":
    main()
