#!/usr/bin/env python3
"""Walking skeleton — Drop 2: ABSENCE 経路(調査を完遂したが世界に無い、不在の型)。
親文書の出発点(NOT_FOUND ≠ DOES_NOT_EXIST)を実データで通行試験する。
stream をリセットしない(Drop 1 に append。実行前に run.py を通しておくこと)。

  正: TRT-LLM は SM120 向け NVFP4 を公式明記しているか
       → 必須ソース全 check → COMPLETED → ABSENCE 正規生成(AB-2範囲参照・AB-3短TTL)
  負: repo leg を timeout 模擬 → SEARCH_INCOMPLETE → ABSENCE を SC-2 が構造ブロック
       (通らない試験: 偽の不在は作れない)
"""
from egl import core, curator, pipeline as P
def line(s=""): print(s)

REQUIRED_KINDS = ["official_documentation", "release_notes", "official_repository"]


def absence_slice(task, question, fail_repo):
    tag = "負(repo timeout)" if fail_repo else "正(全ソースcheck)"
    line(f"\n########## Drop2 {tag}: {task} ##########")
    r = core.run_start("rd", "CURATION", task_id=task)
    G = P.mk_gap(r, question, required_for=["REQ-009"], profile="EP-TECH-STANDARD")
    plan = P.mk_search_plan(r, G, "COV-TECH-STANDARD")
    core.run_end(r, [G, plan])

    # 必須 source kind ごとに search leg。負では repo を FAILED に。
    checked, legs = [], []
    for kind in REQUIRED_KINDS:
        rid, k, ok = P.mk_search_leg(task, plan, kind, simulate_fail=(fail_repo and kind == "official_repository"))
        legs.append(rid)
        line(f"   leg {kind:22s}: {'OK(記述なし)' if ok else 'FAILED(timeout模擬)'}")
        if ok:
            checked.append(k)

    reason = "official_repository leg FAILED" if fail_repo else None
    from egl import gates
    status, cov = gates.evaluate_coverage("COV-TECH-STANDARD", checked, incomplete_reason=reason)
    r2 = core.run_start("rd", "SEARCH", task_id=task, inputs=[plan])
    scon = P.mk_search_conclusion(r2, plan, status, "NO_POSITIVE_EVIDENCE", coverage_result=cov)
    core.run_end(r2, [scon])
    line(f"   SearchConclusion: status={status}  coverage={cov}")

    # ABSENCE candidate(AB-2: statement に調査範囲を参照)
    r3 = core.run_start("rd", "EXTRACTION", task_id=task)
    cov_ref = "COV-TECH-STANDARD(公式doc+release notes+公式repo, en)"
    CA = P.mk_candidate(r3, {
        "object_kind": "CandidateClaim", "claim_type": "ABSENCE", "predicate": "documents",
        "polarity": "ABSENCE", "task_id": task,
        "statement": f"{cov_ref}の範囲で、TensorRT-LLM が SM120 向け NVFP4 サポートを公式に明記した記述は見つからなかった",
        "scope": {"subject": "tensorrt-llm", "topic": "sm120_nvfp4_support",
                  "coverage_profile": "COV-TECH-STANDARD"},
        "evidence_relations": [], "resolves_gap": G, "search_conclusion": scon})
    core.run_end(r3, [CA])
    line(f"   ABSENCE candidate {CA}  (AB-2: statement に coverage 参照)")

    line("   [CURATE]")
    res = curator.curate(CA, adjudicator=None, log=line)
    return res


# 正: ABSENCE 成立
absence_slice("TASK-TRT-POS", "TensorRT-LLM は SM120 向け NVFP4 サポートを公式ドキュメントに明記しているか", fail_repo=False)
# 負: SC-2 ブロック
absence_slice("TASK-TRT-NEG", "TensorRT-LLM は SM120 向け NVFP4 サポートを公式ドキュメントに明記しているか", fail_repo=True)

line("\n=== Drop 2 完了(operational stream 2滴目を append)===")
