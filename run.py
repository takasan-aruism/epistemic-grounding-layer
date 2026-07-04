#!/usr/bin/env python3
"""Walking skeleton — Drop 1: EVIDENCE_INSUFFICIENT 経路(証拠が claim に足りない不足の型)。
RQ: 「NVFP4 は dual RTX5090 の持続 agent 負荷で安定か」
  C1(sm120で動く)→ ACCEPT(残差 operational_stability)
  C2(持続負荷で安定)→ EVIDENCE_INSUFFICIENT → gap 残存 → SOLVED 封鎖(DF-4)
  GC-7: 受理 C1 から「stable」への飛躍を遮断
このrunは stream をリセットする(Drop 1)。Drop 2 は run2.py が append する。
"""
from pathlib import Path
DATA = Path(__file__).resolve().parent / "data"
for f in ["events.jsonl", "state.sqlite"]:   # DE-0006: counters.json は廃止(単一 SoR)
    p = DATA / f
    if p.exists():
        p.unlink()

from egl import core, judge, gates, curator, pipeline as P
def line(s=""): print(s)

r = core.run_start("rd", "CURATION", task_id="TASK-NVFP4-STAB")
G = P.mk_gap(r, "NVFP4 は dual RTX5090 の持続(48h)agent 負荷で安定に動作するか",
             required_for=["REQ-005"], profile="EP-TECH-STANDARD")
plan = P.mk_search_plan(r, G, "COV-TECH-STANDARD")
core.run_end(r, [G, plan])
line(f"[GAP]   {G} 登録 (required_for=REQ-005 → REQUIRED_FOR_RESOLUTION)")

r = core.run_start("rd", "SEARCH", task_id="TASK-NVFP4-STAB", inputs=[plan])
S1 = P.mk_source(r, "RedHatAI/Qwen3.6-35B-A3B-NVFP4 model card", "PRIMARY",
                 "https://huggingface.co/RedHatAI/Qwen3.6-35B-A3B-NVFP4")
blocks = ["This checkpoint is quantized to NVFP4 with linear_attn kept in bf16.",
          "Supported Hardware: NVIDIA Hopper, NVIDIA Blackwell.",
          "To serve with vLLM, start vllm/vllm-openai:nightly and run: vllm serve ..."]
N1 = P.mk_observation(r, S1, "Model Card / Deployment", blocks)
F1 = P.mk_fragment(r, N1, 1, blocks[1], mentions=["ENT-nvfp4", "ENT-blackwell"])
scon = P.mk_search_conclusion(r, plan, "COMPLETED", "POSITIVE_EVIDENCE")
core.run_end(r, [S1, N1, F1, scon])
line(f"[OBS]   {S1}(PRIMARY) → {N1} → {F1}: {blocks[1]!r}")

r = core.run_start("rd", "EXTRACTION", task_id="TASK-NVFP4-STAB")
# DE-0006: id-in-append。relation を candidate 生成前に to=None で先行生成し相互参照を断つ。
rel1 = P.mk_relation(r, F1, None, "SUPPORTS", {"question": "runs on sm120", "scope": {"gpu_arch": "sm120"}})
C1 = core.append_event(r, "CREATE", "CandidateClaim", None, {
    "id": core.SELF, "object_kind": "CandidateClaim", "claim_type": "CAPABILITY", "predicate": "runs_on",
    "polarity": "POSITIVE", "task_id": "TASK-NVFP4-STAB",
    "statement": "NVFP4量子化チェックポイントはBlackwell(sm120)上でvLLMにより推論実行できる",
    "scope": {"runtime": "vllm", "gpu_arch": "sm120", "quant": "nvfp4"},
    "evidence_relations": [rel1], "resolves_gap": None, "validation_mode": "DECLARED",
    "representation_residual": {"known_omissions": ["operational_stability", "kernel_backend"],
                                "scope_uncertainty": "LOW"}}, new_prefix="CC")
rel2 = P.mk_relation(r, F1, None, "SUPPORTS", {"question": "stable under sustained load", "scope": {"gpu_arch": "sm120"}})
C2 = core.append_event(r, "CREATE", "CandidateClaim", None, {
    "id": core.SELF, "object_kind": "CandidateClaim", "claim_type": "MEASUREMENT", "predicate": "stable_under",
    "polarity": "POSITIVE", "task_id": "TASK-NVFP4-STAB",
    "statement": "NVFP4はdual RTX5090の持続(48h)agent負荷で安定動作する",
    "scope": {"runtime": "vllm", "gpu_arch": "sm120", "quant": "nvfp4", "load": "sustained_48h_agent"},
    "evidence_relations": [rel2], "resolves_gap": G, "validation_mode": "REPRODUCED",
    "representation_residual": {"known_omissions": [], "scope_uncertainty": "HIGH"}}, new_prefix="CC")
core.run_end(r, [C1, C2])
line(f"[CAND]  {C1}(背景) / {C2}(gap回答, resolves {G})")

CLAUDE_FINDINGS = {
    C1: {"f1": "SUPPORTED", "f2": "WITHIN", "fragment_sufficient": True,
         "rationale": "『Supported Hardware: Blackwell』は sm120 での runs_on を直接支持。scope 内。安定性は残差。"},
    C2: {"f1": "NOT_SUPPORTED", "f2": "UNRESOLVED", "fragment_sufficient": False,
         "rationale": "fragment は HW 対応の宣言で持続負荷安定性を一切述べない(EI-6 FRAGMENT_INSUFFICIENT)。"}}
adj = judge.ClaudeAdjudicator(CLAUDE_FINDINGS)

line("\n[CURATE C1]"); curator.curate(C1, adj, log=line)
line("[CURATE C2]"); curator.curate(C2, adj, log=line)

con = core.build_view()
open_req = [g for g in core.by_type(con, "KnowledgeGap") if g["status"] == "OPEN" and g.get("required_for")]
line("\n[RESOLUTION]")
line(f"        required gap OPEN → ACTIONABLE(SOLVED封鎖 DF-4) blocked={[g['gap_id'] for g in open_req]}"
     if open_req else "        SOLVED 可")

line("\n[GC-7 lint]  受理 C1 を根拠に『NVFP4はRTX5090で安定』と主張:")
c1g = [c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == C1][0]
bad = {"assertion_id": "A-TEST", "class": "FACT", "text": "NVFP4はRTX5090で安定動作する",
       "scope_echo": {"gpu_arch": "sm120", "operational_stability": "sustained"}, "residual_ack": []}
ok, msg = gates.gc7_lint(con, bad, c1g)
line(f"        {'BLOCKED ✋' if not ok else 'passed'}: {msg}")
line("\n=== Drop 1 完了 ===")
