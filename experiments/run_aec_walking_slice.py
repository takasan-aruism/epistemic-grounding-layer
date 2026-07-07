#!/usr/bin/env python3
"""§16 AEC walking slice — GPU/vLLM model-switch question(mixed evidence classes)。
AC-1..4(+実測 support)を実 EGL refs から derive、validate、compact JP + expanded render、adversarial、metrics。
answer renderer は research/admission しない。missing evidence は UNRESOLVED/RESEARCH_NEED へ。"""
import json, sys
sys.path.insert(0, "/home/takasan/egl")
import answer_evidence as AE
from pathlib import Path

EGL = Path("/home/takasan/egl")

# ── AC-1..4 packets(実 EGL evidence から。Sleep Mode は未調査=正直に UNRESOLVED)──
PACKETS = [
 {"answer_claim_id": "AEC-AC-1",
  "statement": "現在の構成では Qwen3.6 と Coder-Next の co-serve はできません。",
  "claim_class": "FACT", "basis_kind": "LOCAL_MEASUREMENT", "validation_mode": "MEASURED",
  "egl_claim_ref": "DE-0073", "evidence_refs": ["DE-0073", "gpu_conflict_measured.json"],
  "evidence_summary": "実測: weights 36.5 > 31.8 GiB/GPU(KV 前に超過)",
  "source_policy": "LOCAL_OPERATIONAL", "source_role": "LOCAL_MEASUREMENT",
  "supports_dimension": "current-config co-serve feasibility",
  "unsupported_dimension": "general co-serve across other model formats / hardware",
  "scope": "現在の2×RTX5090 / current Qwen3.6+Coder-Next serving config",
  "currentness": "2026-07-07", "local_applicability": "MEASURED",
  "claim_registration_status": "ADMITTED",
  "residuals": ["別 model format / 別 config では未測"]},

 {"answer_claim_id": "AEC-AC-2",
  "statement": "vLLM は公式ドキュメントで Sleep Mode(level 1: weights を CPU にオフロードし KV cache を破棄)を記述しています。",
  "claim_class": "FACT", "basis_kind": "EXTERNAL_SPECIFICATION", "validation_mode": "DECLARED",
  "egl_claim_ref": None,
  "evidence_refs": ["AcquisitionRun docs.vllm.ai/.../sleep_mode (SUCCESS/OBSERVED, http 200)",
                    "Observation OFFICIAL_DOCS/PRIMARY (leg satisfied)", "DE-0085"],
  "evidence_summary": "vLLM 公式ドキュメント(docs.vllm.ai, OFFICIAL_DOCS, PRIMARY)を実取得・OBSERVED・qualify",
  "source_policy": "SOFTWARE_TECHNICAL", "source_role": "PRIMARY_OFFICIAL",
  "supports_dimension": "documented capability existence + semantics",
  "unsupported_dimension": "local wake latency / current-config swap-cost reduction",
  "scope": "vLLM documented capability", "currentness": "docs.vllm.ai latest (fetched 2026-07-07)",
  "local_applicability": "NOT_MEASURED",
  "claim_registration_status": "DEFERRED_AT_ETB (Gate1 GC-8 HIDDEN_HTML — 正式 admission は clearance 待ち)",
  "residuals": ["formal Claim admission は Gate1 GC-8(HIDDEN_HTML taint)で DEFERRED(ETB clearance 未実装=gap)",
                "docs は latency 数値を示さない → local wake latency は依然 MEASUREMENT need(§5)"]},

 {"answer_claim_id": "AEC-AC-3",
  "statement": "phase batching で現在の model-switch overhead が下がる可能性が高いです。",
  "claim_class": "INFERENCE", "basis_kind": "AI_INFERENCE", "validation_mode": "UNRESOLVED",
  "egl_claim_ref": None, "evidence_refs": ["DE-0074", "DE-0080", "process_aggregate.json"],
  "evidence_summary": "実測 swap ~174.5s・18 swaps・独立 slice 群からの推論",
  "source_policy": "LOCAL_OPERATIONAL", "source_role": "LOCAL_MEASUREMENT+INFERENCE",
  "supports_dimension": "direction of change (overhead reduction)",
  "unsupported_dimension": "measured B-mode performance",
  "scope": "current RRI deterministic-core workload / serving config",
  "currentness": "2026-07-07", "local_applicability": "PARTIALLY_GROUNDED",
  "claim_registration_status": "NOT_ADMITTED",
  "residuals": ["B-mode 未実測(COUNTERFACTUAL_ESTIMATE, DE-0080)",
                "batching の property preservation review vs 将来 P8 未完"]},

 {"answer_claim_id": "AEC-AC-4",
  "statement": "現在の TP=2 / NVFP4 構成での local wake latency と適用性は、まだ確立していません。",
  "claim_class": "HYPOTHESIS", "basis_kind": "UNRESOLVED", "validation_mode": "UNRESOLVED",
  "egl_claim_ref": None, "evidence_refs": [],
  "evidence_summary": "local 適用性は未測(概念のみ)",
  "source_policy": "LOCAL_OPERATIONAL", "source_role": None,
  "scope": "現在の TP=2 / NVFP4 serving config", "currentness": None,
  "claim_registration_status": "NOT_ADMITTED",
  "residuals": ["local wake latency 未測", "TP=2 / NVFP4 での適用性未確立",
                "→ concurrent_task_dispatch RESEARCH_NEED(DE-0080)へ route"]},

 {"answer_claim_id": "AEC-AC-5",
  "statement": "現在、model の切替(swap)は約174.5秒/回です。",
  "claim_class": "FACT", "basis_kind": "LOCAL_MEASUREMENT", "validation_mode": "MEASURED",
  "egl_claim_ref": "DE-0074", "evidence_refs": ["DE-0074", "run_sor/events.jsonl"],
  "evidence_summary": "実測(SWAP_START/END primitive の timestamp 差)",
  "source_policy": "LOCAL_OPERATIONAL", "source_role": "LOCAL_MEASUREMENT",
  "supports_dimension": "current swap latency", "unsupported_dimension": "other hardware/config",
  "scope": "現在の2×RTX5090 A-mode serving config", "currentness": "2026-07-07",
  "local_applicability": "MEASURED", "claim_registration_status": "ADMITTED",
  "residuals": ["別 config では未測"]},
]


def metrics(results):
    n = len(results)
    valid = [r for r in results if r["compose"]["renderable"]]
    from collections import Counter
    dist = Counter(p["basis_kind"] for p, _ in [(r["packet"], r) for r in results])
    return {
        "answer_claim_count": n,
        "packet_validity_rate": round(len(valid) / n, 2) if n else None,
        "basis_kind_distribution": dict(dist),
        "claims_with_source_or_evidence_refs": sum(1 for r in results if r["packet"].get("evidence_refs")),
        "claims_with_measurement_refs": sum(1 for r in results if r["packet"]["basis_kind"] == "LOCAL_MEASUREMENT" and r["packet"].get("evidence_refs")),
        "claims_with_residuals": sum(1 for r in results if r["packet"].get("residuals")),
        "unresolved_claims": sum(1 for r in results if r["packet"]["basis_kind"] == "UNRESOLVED"),
        "strength_violations": sum(len(r["compose"]["strength"]["violations"]) for r in results),
        "not_admitted": sum(1 for r in results if r["packet"].get("claim_registration_status") == "NOT_ADMITTED"),
        "note": "composite 'trust score' は作らない(§19)。dimension は raw のまま。",
    }


def main():
    out = {"question": "GPU/vLLM model-switch — mixed evidence classes", "claims": []}
    print("### AEC walking slice — GPU/vLLM model-switch question ###\n")
    results = []
    for p in PACKETS:
        comp = AE.compose_ok(p)
        results.append({"packet": p, "compose": comp})
        print(f"── {p['answer_claim_id']}  basis={p['basis_kind']} renderable={comp['renderable']}")
        print("  [compact]")
        for ln in AE.render_compact(p).splitlines():
            print("   " + ln)
        if not comp["renderable"]:
            print(f"  ⚠ NOT renderable: validate={comp['validate']['problems']} strength={[v['type'] for v in comp['strength']['violations']]}")
        out["claims"].append({"packet": p, "compact": AE.render_compact(p), "expanded": AE.render_expanded(p),
                              "compose": comp})
        print()
    m = metrics(results)
    out["metrics"] = m
    print("=== metrics (§19, no composite score) ===")
    for k, v in m.items():
        print(f"  {k}: {v}")
    (EGL / "experiments" / "aec_walking_slice.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n-> aec_walking_slice.json 保存。renderer は research/admission しない(missing→UNRESOLVED/RESEARCH_NEED)。")


if __name__ == "__main__":
    main()
