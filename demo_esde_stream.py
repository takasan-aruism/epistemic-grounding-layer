#!/usr/bin/env python3
"""Operational Stream #1 — ESDE。実 RQ を EGL 通常経路(retrieval → Qwen 構造化 answer → validate)へ
流し、observation/inference/current/historical/open-gap を分離。結果を operational data として保存
(benchmark B / ACQ-10 C 完全充足材料の候補。**gold key はここで作らない**=独立 adjudication 確定後)。
"""
import json, datetime
from pathlib import Path
from egl import esde_stream as ES, self_grounding as SG

recs = ES.load_esde_corpus()
sup = SG.detect_supersession(recs)
ids = [r["record_id"] for r in recs]
ASK = {qid: q for qid, q in ES.ESDE_RQS}
PICK = ["RQ2", "RQ8"]        # observation/inference 分離 と failure-pattern retrieval を先に

print(f"### ESDE Operational Stream (corpus={len(recs)} records) ###\n")
out = []
for qid in PICK:
    q = ASK[qid]
    ans, hits, raw = ES.answer_esde(q, recs, sup)
    m = ES.measure(ans, ids) if ans else {"contract_ok": False, "problems": [raw[:80]]}
    print(f"── {qid}: {q}")
    print(f"   retrieved: {hits[:5]}")
    if ans:
        for c in (ans.get("answer_claims") or [])[:5]:
            print(f"   [{c.get('epistemic_kind','?'):12s}|{c.get('currentness','?')}] {c.get('text','')[:120]}")
        for h in (ans.get("historical_claims") or [])[:2]:
            print(f"   [HISTORICAL] {h.get('text','')[:110]}")
        for g in (ans.get("open_gaps") or [])[:3]:
            print(f"   [GAP] {g[:110]}")
        print(f"   metrics: contract_ok={m['contract_ok']} obs={m.get('n_observation')} inf={m.get('n_inference')} "
              f"src_trace={m.get('source_trace_completeness',0):.2f}")
        if m.get("problems"):
            print(f"   contract problems (operational finding): {m['problems']}")
    print()
    out.append({"rq": qid, "question": q, "retrieved": hits, "answer": ans, "metrics": m})

Path("esde_operational_run.json").write_text(json.dumps(
    {"stream": "ESDE #1", "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
     "corpus_size": len(recs), "results": out}, ensure_ascii=False, indent=2))
print("→ esde_operational_run.json 保存(operational data。gold key は独立 adjudication 後)。")
print("※ directive §9: 自律 RD はまだ有効化しない。実運用の失敗モードを EGL 開発入力にする。")
