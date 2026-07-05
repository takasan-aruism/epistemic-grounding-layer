#!/usr/bin/env python3
"""SELF_GROUNDING 意味トラック baseline(live Qwen)。EGL が自らの台帳から現 epistemic state を
再構築できるか。retrieval → Qwen が構造化 answer(answer_claims/historical_claims/open_gaps/
source_trace)を生成 → contract 検証 + metrics。判定は NL でなく構造化 answer(JREV-0006 §9)。

代表4問: Q3(DE-0005 failure)/ Q7(ABSENCE≠NEGATIVE≠SPECIFIED、R5→R7 supersession)/ Q8(R7 変更)/
Q16(現 unresolved 境界に最も似た過去 failure pattern= ESDE transfer の要)。
"""
from egl import self_grounding as SG

recs = SG.load_corpus()
sup = SG.detect_supersession(recs)
corpus_ids = [r["record_id"] for r in recs]
ASK = {qid: q for qid, q in SG.BENCHMARK}
PICK = ["Q3", "Q7", "Q8", "Q16"]

print("########## SELF_GROUNDING baseline(live Qwen)##########")
print(f"corpus: {len(recs)} records / superseded tokens: {sorted(sup)}\n")

for qid in PICK:
    q = ASK[qid]
    ans, hit_ids, raw = SG.answer_question(q, recs, sup)
    v = SG.validate_answer(ans, corpus_ids)
    print(f"── {qid}: {q}")
    print(f"   retrieved: {hit_ids}")
    if not ans:
        print(f"   (no structured answer: {raw[:120]})\n"); continue
    for c in (ans.get("answer_claims") or [])[:4]:
        print(f"   [CURRENT] {c.get('text','')[:140]}  ⟵ {c.get('record_ids')}")
    for h in (ans.get("historical_claims") or [])[:3]:
        print(f"   [HIST] {h.get('text','')[:120]}  (superseded_by={h.get('superseded_by')})")
    for g in (ans.get("open_gaps") or [])[:4]:
        print(f"   [GAP] {g[:120]}")
    m = v["metrics"]
    print(f"   contract ok={v['ok']} source_trace_completeness={m['source_trace_completeness']:.2f} "
          f"(claims={m['n_answer_claims']} hist={m['n_historical_claims']} gaps={m['n_open_gaps']})")
    if v["problems"]:
        print(f"   problems: {v['problems'][:3]}")
    print()

print("========== 評価観点(JREV-0006 §10 metrics の baseline)==========")
print("- source_trace_completeness: 各 answer claim が実在 record を引くか(捏造出典・無出典を弾く)")
print("- Q7 で R5(SPECIFIED=NEGATIVE専用)を CURRENT でなく HISTORICAL(superseded_by R7/DE-0029)に置けるか")
print("- Q16 で現 boundary(例: source authenticity leaf)を過去 pattern(信用の根が一段下る)へ関係付けられるか")
print("※ baseline = naive retrieval + 単一 Qwen。独立 attacker の SG-A..I mutation は次段(JREV-0007)。")
