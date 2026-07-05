#!/usr/bin/env python3
"""SELF_GROUNDING_CHALLENGE_SET_V1 runner(CI 締め)。live Qwen で意味トラックを再走し、metrics を
drift_baseline と比較して challenge_baseline.json に config fingerprint 付きで記録する。
test_self_grounding の drift-gate が、fingerprint 変化(rerun_on_change_of の surface が変わった)を
検出したら FAIL する → この runner を回して baseline を更新する運用(=変更時 自動再走の強制)。
"""
import json, datetime
from pathlib import Path
from egl import self_grounding as SG, review_mechanisms as RM

BASE = Path(__file__).resolve().parent
recs = SG.load_corpus()
sup = SG.detect_supersession(recs)
corpus_ids = [r["record_id"] for r in recs]
ASK = {qid: q for qid, q in SG.BENCHMARK}
PICK = ["Q3", "Q7", "Q8", "Q16"]        # baseline 代表問(意味トラック live)

print("### SELF_GROUNDING_CHALLENGE_SET_V1 rerun (live) ###")
print(f"config_fingerprint = {RM.config_fingerprint()}\n")

completeness, contract_ok, results = [], 0, {}
for qid in PICK:
    ans, hits, raw = SG.answer_question(ASK[qid], recs, sup)
    v = SG.validate_answer(ans, corpus_ids)
    completeness.append(v["metrics"].get("source_trace_completeness", 0.0))
    contract_ok += 1 if v["ok"] else 0
    results[qid] = {"contract_ok": v["ok"], "metrics": v["metrics"], "problems": v["problems"][:3]}
    print(f"{qid}: contract_ok={v['ok']} source_trace_completeness={v['metrics'].get('source_trace_completeness'):.2f}")

avg = sum(completeness) / len(completeness) if completeness else 0.0
metrics = {"questions": PICK, "contract_ok": f"{contract_ok}/{len(PICK)}",
           "avg_source_trace_completeness": round(avg, 3), "per_question": results}

stamp = {"version": RM.SELF_GROUNDING_CHALLENGE_SET_V1["version"],
         "config_fingerprint": RM.config_fingerprint(),
         "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "drift_baseline": RM.SELF_GROUNDING_CHALLENGE_SET_V1["drift_baseline"],
         "rerun_metrics": metrics}
(BASE / "challenge_baseline.json").write_text(json.dumps(stamp, ensure_ascii=False, indent=2))

print(f"\navg source_trace_completeness = {avg:.2f}  contract_ok = {contract_ok}/{len(PICK)}")
print("→ challenge_baseline.json 更新(fingerprint stamp 済)。drift-gate は fingerprint 変化で再走要求。")
print("※ 完全な SG-A..I 9-trap live 再構成は MOR-2 backlog(baseline 締めは代表問+構造トラックで確立)。")
