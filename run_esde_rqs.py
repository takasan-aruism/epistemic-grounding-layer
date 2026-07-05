#!/usr/bin/env python3
"""ESDE Operational Stream — full RQ batch(RQ1-10)。PRE_ADJUDICATION(DE-0047 taxonomy 裁定前)。
各 RQ を EGL 通常経路へ流し、observation/inference/current/historical/open-gap を分離、metrics 測定、
contract problems を operational finding として集約。結果を esde_operational_run.json に保存。
"""
import json, datetime
from collections import Counter
from egl import esde_stream as ES, self_grounding as SG

recs = ES.load_esde_corpus()
sup = SG.detect_supersession(recs)
ids = [r["record_id"] for r in recs]

print(f"### ESDE Operational Stream — RQ1-10 (corpus={len(recs)}, PRE_ADJUDICATION) ###\n")
out, finding_kinds = [], Counter()
for qid, q in ES.ESDE_RQS:
    ans, hits, raw = ES.answer_esde(q, recs, sup)
    m = ES.measure(ans, ids) if ans else {"contract_ok": False, "problems": [raw[:80]], "source_trace_completeness": 0}
    ac = (ans.get("answer_claims") or []) if ans else []
    hc = (ans.get("historical_claims") or []) if ans else []
    print(f"── {qid}: {q}")
    print(f"   retrieved={hits[:4]}  claims={len(ac)} hist={len(hc)} obs={m.get('n_observation')} inf={m.get('n_inference')} "
          f"gaps={len((ans or {}).get('open_gaps') or [])} src_trace={m.get('source_trace_completeness',0):.2f} contract_ok={m['contract_ok']}")
    for p in (m.get("problems") or []):
        # operational finding の型を集約
        k = ("superseded_by_bare_string" if "not a list" in p and "superseded_by" in p else
             "superseded_by_ref_invalid" if "superseded_by ref" in p else
             "currentness_misplacement" if "currentness=HISTORICAL" in p else
             "unsupported_or_forged_cite" if ("unsupported" in p or "unknown record" in p) else "other")
        finding_kinds[k] += 1
        print(f"   ⚠ {p[:110]}")
    print()
    out.append({"rq": qid, "question": q, "retrieved": hits, "answer": ans, "metrics": m})

print("========== operational findings(型別集約)==========")
for k, n in finding_kinds.most_common():
    print(f"  {k}: {n}")
avg = sum(o["metrics"].get("source_trace_completeness", 0) for o in out) / len(out)
ok = sum(1 for o in out if o["metrics"].get("contract_ok"))
print(f"  contract_ok = {ok}/{len(out)}   avg source_trace_completeness = {avg:.2f}")

json.dump({"stream": "ESDE #1 full RQ batch", "taxonomy_status": "PRE_ADJUDICATION (DE-0047)",
           "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "corpus_size": len(recs), "finding_kinds": dict(finding_kinds), "results": out},
          open("esde_operational_run.json", "w"), ensure_ascii=False, indent=2)
print("→ esde_operational_run.json 保存(gold key は独立 adjudication 後)。自律 RD は未有効(directive §9)。")
