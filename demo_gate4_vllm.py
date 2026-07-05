#!/usr/bin/env python3
"""Phase 1b — real Gate4 の実モデル敵対ラウンド(JREV-0005 gate: 自律 RD 前に最低1回)。

同一の *実* fragment(vLLM README の一行)に対し3つの claim を、ローカル Qwen3.6-35B(vLLM:8005)を
Gate4 judge にして裁定させる。焦点は **world-knowledge trap**: fragment が establish しない claim を、
Qwen が『世界的に真だから』で SUPPORTED にしてしまわないか。境界が保てば trap は EVIDENCE_INSUFFICIENT。
"""
import os
from pathlib import Path
os.environ["EGL_DATA_DIR"] = str(Path(__file__).resolve().parent / "data_gate4")
for f in ["events.jsonl", "state.sqlite", ".idlock"]:
    p = Path(os.environ["EGL_DATA_DIR"]) / f
    if p.exists():
        p.unlink()

from egl import core, pipeline as P, curator, judge_vllm
def line(s=""): print(s)

FRAG = "vLLM is a fast and easy-to-use library for LLM inference and serving."   # 実 README の一行
CASES = [
    ("positive", "vLLM は LLM 推論・serving のための高速で使いやすいライブラリである",
     "fragment が直接記述 → SUPPORTED を期待"),
    ("world-knowledge trap", "vLLM は NVIDIA Blackwell GPU 上で NVFP4 量子化をサポートする",
     "fragment はこれを述べない。世界的に真でも fragment 未支持 → NOT_SUPPORTED を期待(trap)"),
    ("scope-exceed", "vLLM は全ての代替を上回る世界最速の LLM 推論エンジンである",
     "fragment は『fast』のみ。『最速・全代替超え』は scope 超過 → EXCEEDS を期待"),
]

line("########## real Gate4(Qwen3.6-35B @ vLLM)敵対ラウンド ##########")
line(f"fragment(実 README): {FRAG!r}\n")

adj = judge_vllm.VLLMAdjudicator()
r = core.run_start("rd", "CURATION", task_id="TASK-GATE4")
S = P.mk_source(r, "vLLM README", "PRIMARY", "https://github.com/vllm-project/vllm")
N = P.mk_observation(r, S, "README / Overview", [FRAG], observation_kind="DECLARATION")
F = P.mk_fragment(r, N, 0, FRAG, mentions=["ENT-vllm"])
core.run_end(r, [S, N, F])

results = []
for name, statement, expect in CASES:
    rc = core.run_start("rd", "EXTRACTION", task_id="TASK-GATE4")
    rel = P.mk_relation(rc, F, None, "SUPPORTS", {"scope": {"entity": "vllm"}})
    C = P.mk_candidate(rc, {
        "object_kind": "CandidateClaim", "claim_type": "DESCRIPTION", "predicate": "is_described_as",
        "polarity": "POSITIVE", "task_id": "TASK-GATE4", "statement": statement,
        "scope": {"entity": "vllm", "aspect": "definition"}, "evidence_relations": [rel],
        "resolves_gap": None, "representation_residual": {"known_omissions": [], "scope_uncertainty": "LOW"}})
    core.run_end(rc, [])
    line(f"── {name} ──")
    line(f"   claim: {statement}")
    line(f"   期待: {expect}")
    res = curator.curate(C, adj, log=lambda s: None)
    con = core.build_view()
    claim = next((c for c in core.by_type(con, "Claim") if c.get("origin_candidate") == C), None)
    dec = core.get(con, res.get("decision_id")) if res.get("decision_id") else None
    finding = dec.get("finding") if dec else None
    f1 = finding.get("f1_entailment") if finding else None
    f2 = finding.get("f2_scope") if finding else None
    line(f"   Qwen finding: f1={f1} f2={f2} frag_sufficient={finding.get('fragment_sufficient') if finding else None}")
    line(f"   rationale: {(finding.get('rationale') if finding else '')!r}")
    line(f"   → OUTCOME: {res.get('outcome')}   Claim 生成={'あり '+str(res.get('global_claim')) if claim else 'なし'}")
    line("")
    results.append((name, res.get("outcome"), claim is not None, f1, f2))

line("========== まとめ ==========")
trap = next(x for x in results if x[0] == "world-knowledge trap")
pos = next(x for x in results if x[0] == "positive")
line(f"positive:          outcome={pos[1]} Claim={'あり' if pos[2] else 'なし'}  (期待: ACCEPT/あり)")
line(f"world-knowledge trap: outcome={trap[1]} Claim={'あり' if trap[2] else 'なし'}  (境界が保てば: 不受理/なし)")
scope = next(x for x in results if x[0] == "scope-exceed")
line(f"scope-exceed:      outcome={scope[1]} Claim={'あり' if scope[2] else 'なし'}  (期待: SCOPE_REDUCTION/なし)")
held = (not trap[2]) and (not scope[2])
line(f"\n境界判定: real judge が fragment 未支持/scope 超過を止めたか = {'HELD ✅' if held else 'BREACHED ❌(要 prompt 硬化 or 非保証宣言)'}")
line("※ これは実モデル敵対ラウンド1回。teacher_signal であって ground truth ではない(CB-5)。")
