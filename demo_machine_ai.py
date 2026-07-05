#!/usr/bin/env python3
"""JREV-0003 実弾デモ — このマシンで稼働中の AI を EGL の grounding にかける(AB-0013)。

取得境界(retrieval / LegIntent)は未実装ゆえ、証拠は *このセッションで Claude Code が
実機観測した一次事実* を手で流し込む(nvidia-smi / ps)。捏造しない。EGL_DATA_DIR を
専用 stream に向け canonical data/ を汚さない(DE-0011)。

実演する差別化機構:
  (1) evidence→claim: 観測に裏打ちされた claim だけが立つ
  (2) R6/DE-0026: MEASUREMENT 観測は status=VERIFIED(entailment 成立)でも
      validation_mode=UNRESOLVED。DECLARED は PRIMARY+DECLARATION 観測を要する——
      手元に公式 model card(declaration)が無いので、正しく mode を名乗らない
  (3) GC-7: 稼働構成の観測から『持続負荷でも安定』への scope 飛躍を遮断
  (4) ABSENCE: 公式安定性ベンチの不在は NOT_FOUND であって『不安定』ではない
"""
import os
from pathlib import Path
os.environ["EGL_DATA_DIR"] = str(Path(__file__).resolve().parent / "data_jrev0003")
for f in ["events.jsonl", "state.sqlite"]:          # demo は自分の stream を持つ(reset)
    p = Path(os.environ["EGL_DATA_DIR"]) / f
    if p.exists():
        p.unlink()

from egl import core, judge, gates, curator, pipeline as P
def line(s=""): print(s)

# ---- 実機観測(2026-07-05, Claude Code が nvidia-smi / ps で取得した一次事実)----
VLLM_PROC = [
    "USER runs on this host (observed via ps):",
    "vllm serve --served-model-name Qwen3.6-35B-A3B --tensor-parallel-size 2 "
    "--enable-expert-parallel --kv-cache-dtype fp8 --max-num-batched-tokens 8192 "
    "--max-num-seqs 4 --max-model-len 32768 --enable-prefix-caching --gpu-memory-utilization 0.92",
    "PID 138021; LISTEN 0.0.0.0:8005 (ss -tlnp).",
]
NVIDIA_SMI = [
    "nvidia-smi --query-gpu (observed):",
    "0, NVIDIA GeForce RTX 5090, 580.173.02, 32607 MiB / 1, NVIDIA GeForce RTX 5090, 580.173.02, 32607 MiB",
    "(driver 580.173.02, 2x 32GB Blackwell)",
]

line("########## JREV-0003 実弾デモ: このマシンの AI を grounding ##########")

# =====================================================================
# (A) MEASUREMENT claim — 実プロセス観測から。R6: status=VERIFIED でも mode=UNRESOLVED
# =====================================================================
r = core.run_start("rd", "CURATION", task_id="TASK-HOST-QWEN")
G = P.mk_gap(r, "Qwen3.6-35B-A3B はこのホストで現在どの vLLM 構成で serve されているか",
             required_for=["REQ-HOST-01"], profile="EP-TECH-STANDARD")
plan = P.mk_search_plan(r, G, "COV-TECH-STANDARD")
core.run_end(r, [G, plan])

r = core.run_start("rd", "SEARCH", task_id="TASK-HOST-QWEN", inputs=[plan])
S1 = P.mk_source(r, "host process table (ps/ss)", "PRIMARY", "proc:pid=138021")
# observation_kind=MEASUREMENT: 稼働状態の直接観測であって公式宣言ではない
N1 = P.mk_observation(r, S1, "vllm serve process", VLLM_PROC, observation_kind="MEASUREMENT")
F1 = P.mk_fragment(r, N1, 1, VLLM_PROC[1], mentions=["ENT-qwen36", "ENT-vllm"])
scon = P.mk_search_conclusion(r, plan, "COMPLETED", "POSITIVE_EVIDENCE")
core.run_end(r, [S1, N1, F1, scon])
line(f"[OBS]   {S1}(PRIMARY, MEASUREMENT) → {N1} → {F1}")

r = core.run_start("rd", "EXTRACTION", task_id="TASK-HOST-QWEN")
rel1 = P.mk_relation(r, F1, None, "SUPPORTS",
                     {"question": "現在の serve 構成", "scope": {"host": "this"}})
C1 = P.mk_candidate(r, {
    "object_kind": "CandidateClaim", "claim_type": "MEASUREMENT", "predicate": "served_with",
    "polarity": "POSITIVE", "task_id": "TASK-HOST-QWEN",
    # 主張は adjudicated fragment(VLLM_PROC[1]=serve 引数行)が支持する範囲に限定する。
    # port 8005 は別 block(ss 観測)由来ゆえ、この fragment だけでは主張しない(過大主張の回避)。
    "statement": "Qwen3.6-35B-A3B はこのホストで vLLM により tensor-parallel=2 / kv-cache-dtype=fp8 / "
                 "max-model-len=32768 で serve されている",
    "scope": {"host": "this", "runtime": "vllm", "tensor_parallel": "2",
              "kv_cache_dtype": "fp8", "max_model_len": "32768"},
    "evidence_relations": [rel1], "resolves_gap": G, "validation_mode": None,
    "representation_residual": {"known_omissions": ["operational_stability", "throughput_tok_s"],
                                "scope_uncertainty": "LOW"}})
core.run_end(r, [C1])
line(f"[CAND]  {C1}(実プロセス観測 → 現構成 claim)")

# Gate4: プロセス行は tp/kv-cache/model 名を直接述べる → SUPPORTED・WITHIN
adj = judge.ClaudeAdjudicator({
    C1: {"f1": "SUPPORTED", "f2": "WITHIN", "fragment_sufficient": True,
         "rationale": "観測プロセス行が served-model-name/tp/kv-cache/port を直接記述。scope 内。"}})
line("\n[CURATE C1]"); res1 = curator.curate(C1, adj, log=line)

con = core.build_view()
c1_claim = [c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == C1][0]
line(f"\n[R6 デモ] C1 claim: status={c1_claim['status']}  validation_mode={c1_claim.get('validation_mode')}")
line("        → 直接観測ゆえ entailment(status)は VERIFIED。しかし MEASUREMENT 観測なので")
line("          validation_mode は UNRESOLVED(DECLARED は PRIMARY+DECLARATION=公式宣言を要する)。")
line("          手元に公式 model card(declaration)が無いので、mode を騙らないのが正しい。")

# =====================================================================
# (B) GC-7 — 稼働構成の観測から『持続負荷でも安定』への飛躍を遮断
# =====================================================================
line("\n[GC-7 lint]  受理 C1(現構成)を根拠に『持続負荷でも安定稼働する』と主張:")
bad = {"assertion_id": "A-STAB", "class": "FACT",
       "text": "Qwen3.6-35B-A3B はこのマシンで持続(48h)agent 負荷でも安定稼働する",
       "scope_echo": {"operational_stability": "sustained_48h"}, "residual_ack": []}
ok, msg = gates.gc7_lint(con, bad, c1_claim)
line(f"        {'BLOCKED ✋' if not ok else 'passed'}: {msg}")
line("        → 現構成を観測しても『持続負荷で安定』は別次元(C1 の known_omissions)。飛躍を遮断。")

# =====================================================================
# (C) ABSENCE — 公式 48h 安定性ベンチの不在は NOT_FOUND であって『不安定』ではない
# =====================================================================
line("\n########## ABSENCE: 公式安定性ベンチは存在するか ##########")
REQUIRED_KINDS = ["official_documentation", "release_notes", "official_repository"]
task = "TASK-HOST-QWEN-STAB"
r = core.run_start("rd", "CURATION", task_id=task)
G2 = P.mk_gap(r, "Qwen3.6-35B-A3B の dual RTX5090・持続48h 安定性を示す公式ベンチは存在するか",
              required_for=["REQ-HOST-02"], profile="EP-TECH-STANDARD")
plan2 = P.mk_search_plan(r, G2, "COV-TECH-STANDARD")
core.run_end(r, [G2, plan2])

checked = []
for kind in REQUIRED_KINDS:
    rid, k, okleg = P.mk_search_leg(task, plan2, kind, simulate_fail=False)
    checked.append(k)
    line(f"   leg {kind:22s}: COMPLETED(該当記述なし)")
status, cov = gates.evaluate_coverage("COV-TECH-STANDARD", checked, incomplete_reason=None)
r2 = core.run_start("rd", "SEARCH", task_id=task, inputs=[plan2])
scon2 = P.mk_search_conclusion(r2, plan2, status, "NO_POSITIVE_EVIDENCE", coverage_result=cov)
core.run_end(r2, [scon2])
line(f"   SearchConclusion: status={status}  coverage={cov}")

r3 = core.run_start("rd", "EXTRACTION", task_id=task)
CA = P.mk_candidate(r3, {
    "object_kind": "CandidateClaim", "claim_type": "ABSENCE", "predicate": "documents",
    "polarity": "ABSENCE", "task_id": task,
    "statement": "COV-TECH-STANDARD の範囲(公式doc+release notes+公式repo)で、Qwen3.6-35B-A3B の "
                 "dual RTX5090・持続48h 安定性を示す公式ベンチ記述は見つからなかった",
    "scope": {"subject": "qwen3.6-35b-a3b", "topic": "sustained_48h_stability_benchmark",
              "coverage_profile": "COV-TECH-STANDARD"},
    "evidence_relations": [], "resolves_gap": G2, "search_conclusion": scon2})
core.run_end(r3, [CA])
line(f"   ABSENCE candidate {CA}")
line("   [CURATE]"); resA = curator.curate(CA, adjudicator=None, log=line)
con = core.build_view()
ca_claim = [c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == CA]
if ca_claim:
    cc = ca_claim[0]
    line(f"\n        → status={cc['status']}(NOT_FOUND)。absence_validation={cc.get('absence_validation')}")
    line("          『見つからなかった』は『不安定』でも『存在しない』でもない。短TTL で再調査対象。")

line("\n=== JREV-0003 デモ完了 — 実機観測を grounding に通した(取得境界は未実装のため手投入)===")
