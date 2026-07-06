#!/usr/bin/env python3
"""Registration Acceptance Test — SGQ-R1..R6(Directive v0.3 §7)。登録後の SELF_GROUNDING live path で
EGL の CURRENT 状態を再構成させ、期待(supersession target 精度 / SPECIFIED≠IMPLEMENTED / DW 未証明 /
JREV-0007 narrow / open gaps / ACQ-10 no-regression・no-overclaim)と照合する fresh current/superseded case。"""
import json, datetime
from egl import self_grounding as SG

# AB-0023: 全 domain(design+review+audit_backlog)を id universe に(validate 用)
_all = SG.load_corpus(domains=("DESIGN_EVIDENCE", "REVIEW", "AUDIT_BACKLOG"))
ids = [r["record_id"] for r in _all]
SGQ = [
    ("SGQ-R1", "現在の bootstrap 順序は?(何が current で、SRC-A §4 の bootstrap-order proposition は historical/superseded か)"),
    ("SGQ-R2", "RRI は実装済みか?"),
    ("SGQ-R3", "DW の有効性は証明されているか?"),
    ("SGQ-R4", "JREV-0007 で何が発見されたか?(実在 record ID 付き、捏造ゼロ)"),
    ("SGQ-R5", "RRI 実装前または初期 Task 群で扱うべき open gaps は?"),
    ("SGQ-R6", "自律 RD(LLM-agentic RD)は現在有効化できるか?(A/B/C/D の分解、旧状態へ巻き戻さない、over-claim しない)"),
]
print(f"### Registration Acceptance Test SGQ-R1..R6 (AB-0023 coverage, id_universe={len(ids)}) ###\n")
out = []
for qid, q in SGQ:
    ans, hits, raw, cov = SG.answer_with_coverage(q, k=10, record_char_limit=1800, max_tokens=1400)
    v = SG.validate_answer(ans, ids)
    print(f"── {qid}: {q}")
    print(f"   class={cov['query_class']} domains={cov['loaded_domains']} force_include={cov['force_include']}")
    print(f"   retrieved={hits[:8]}")
    if ans:
        for c in (ans.get("answer_claims") or [])[:5]:
            print(f"   [CURRENT] {c.get('text','')[:150]}  <- {c.get('record_ids')}")
        for h in (ans.get("historical_claims") or [])[:2]:
            print(f"   [HIST] {h.get('text','')[:120]}  (superseded_by={h.get('superseded_by')})")
        for g in (ans.get("open_gaps") or [])[:5]:
            print(f"   [GAP] {g[:110]}")
        m = v["metrics"]
        print(f"   M1_grounding={m['m1_grounding_integrity_pass']} M2_placement={m['m2_semantic_placement_pass']} "
              f"M3_format={m['m3_format_adherence_pass']} src_trace={m['source_trace_completeness']:.2f}")
        if v["problems"]:
            print(f"   problems: {v['problems'][:2]}")
    else:
        print(f"   (no answer: {raw[:100]})")
    print()
    out.append({"sgq": qid, "question": q, "coverage": cov, "answer": ans, "validate": {k: v[k] for k in ("ok", "problems", "coercions")}, "metrics": v["metrics"]})
json.dump({"test": "SGQ-R1..R6 registration acceptance", "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "results": out}, open("registration_sgq_run.json", "w"), ensure_ascii=False, indent=2)
print("→ registration_sgq_run.json 保存。registration report で期待と照合。")
