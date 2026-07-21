#!/usr/bin/env python3
"""Stage 2b: 3-seed consensus. Spec §3.4 (replication gate).

Finding (I3): across seeds, PROSE agrees ~0.51 (Jaccard) but CITED LINE RANGES agree ~0.83.
=> the line range is the stable unit; prose is only a label. Consensus is therefore computed
over evidence line ranges, not over wording. An item survives only if >=2 of 3 seeds cite an
overlapping range in the same field. Non-corroborated items go to UNRESOLVED.jsonl.
"""
import json, collections
from pathlib import Path
S = Path("/home/takasan/egl/structure")
SEEDS = [("FILE_EXTRACTION.jsonl", 7), ("FILE_EXTRACTION_S23.jsonl", 23),
         ("FILE_EXTRACTION_S47.jsonl", 47)]
LISTS = ["actual_capabilities", "claimed_capabilities", "capability_gap",
         "authority_checks", "side_effects", "failure_modes", "limitations"]
KEYNAME = {"actual_capabilities": "capability", "claimed_capabilities": "claim",
           "capability_gap": "claimed", "authority_checks": "check",
           "side_effects": "effect", "failure_modes": "mode", "limitations": "limitation"}

runs = []
for fn, sd in SEEDS:
    runs.append({r["key"]: r for r in map(json.loads, open(S / fn))
                 if r.get("extract_status") == "OK"})

def ov(a, b):
    lo = max(a[0], b[0]); hi = min(a[1], b[1])
    if hi < lo: return 0.0
    return (hi - lo + 1) / max(a[1]-a[0]+1, b[1]-b[0]+1)

keys = sorted(set().union(*[set(r) for r in runs]))
out, unres = [], []
stat = collections.Counter()
for k in keys:
    present = [r[k] for r in runs if k in r]
    stat["files_seeds_%d" % len(present)] += 1
    if len(present) < 2:
        unres.append({"key": k, "reason": "extraction succeeded in <2 of 3 seeds",
                      "seeds_ok": len(present)}); continue
    rec = {"key": k, "seeds_ok": len(present), "trust_tier": "T3_DERIVED",
           "consensus_rule": ">=2/3 seeds cite an overlapping line range in the same field",
           "regenerable": True,
           "derived_from": "qwen3.6-35b-a3b 3-seed consensus over evidence line ranges"}
    for L in LISTS:
        kept = []
        base = present[0].get(L, [])
        others = [p.get(L, []) for p in present[1:]]
        for it in base:
            e = it.get("evidence") or {}
            r0 = (e.get("line_start"), e.get("line_end"))
            if not all(isinstance(x, int) for x in r0): continue
            votes, labels = 1, [it.get(KEYNAME[L], "")]
            for o in others:
                best = max((ov(r0, (x["evidence"]["line_start"], x["evidence"]["line_end"]))
                            for x in o if isinstance(x.get("evidence"), dict)
                            and isinstance(x["evidence"].get("line_start"), int)), default=0.0)
                if best >= 0.5:
                    votes += 1
                    labels.append(next(x.get(KEYNAME[L], "") for x in o
                                       if isinstance(x.get("evidence"), dict)
                                       and isinstance(x["evidence"].get("line_start"), int)
                                       and ov(r0, (x["evidence"]["line_start"],
                                                   x["evidence"]["line_end"])) == best))
            if votes >= 2:
                kept.append({"label": labels[0], "alt_labels": labels[1:],
                             "line_start": r0[0], "line_end": r0[1], "votes": votes})
                stat[L + "_kept"] += 1
            else:
                stat[L + "_dropped"] += 1
                unres.append({"key": k, "field": L, "label": it.get(KEYNAME[L], "")[:120],
                              "line_start": r0[0], "line_end": r0[1],
                              "reason": "no corroborating seed (votes=1)"})
        rec[L] = kept
    life = [p["lifecycle_signal"] for p in present]
    c = collections.Counter(life).most_common(1)[0]
    rec["lifecycle_signal_majority"] = c[0] if c[1] >= 2 else "NO_MAJORITY"
    rec["lifecycle_signal_votes"] = dict(collections.Counter(life))
    if c[1] < 2: stat["lifecycle_no_majority"] += 1
    rec["purpose_1line_variants"] = [p["purpose_1line"] for p in present]
    out.append(rec)

(S / "FILE_EXTRACTION_CONSENSUS.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
(S / "UNRESOLVED.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in unres) + "\n")
print(f"consensus files : {len(out)}")
print(f"UNRESOLVED rows : {len(unres)}")
tot_k = sum(v for k, v in stat.items() if k.endswith("_kept"))
tot_d = sum(v for k, v in stat.items() if k.endswith("_dropped"))
print(f"items kept      : {tot_k}")
print(f"items dropped   : {tot_d}  ({100*tot_d/max(tot_k+tot_d,1):.1f}% of candidates)")
print()
for L in LISTS:
    k_, d_ = stat[L+"_kept"], stat[L+"_dropped"]
    print(f"  {L:24s} kept {k_:5d}  dropped {d_:5d}  survival {100*k_/max(k_+d_,1):5.1f}%")
print()
print("lifecycle no-majority files:", stat["lifecycle_no_majority"], "/", len(out))
print("files by seed coverage:", {k: v for k, v in stat.items() if k.startswith("files_seeds")})
