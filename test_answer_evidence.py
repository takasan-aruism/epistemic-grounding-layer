#!/usr/bin/env python3
"""AEC validate_packet / strength_guard / rendering + adversarial AE-1..7(§17）。
strength guard は fail-conservative: inflation を疑ったら flag。"""
import sys
import answer_evidence as AE

R = []
def ck(n, c): R.append((n, c)); print(f"  [{'PASS ✅' if c else 'FAIL ❌'}] {n}")

# ── basis validation (§7) ──
def basis():
    ok = {"answer_claim_id": "AC-x", "statement": "s", "claim_class": "FACT",
          "basis_kind": "LOCAL_MEASUREMENT", "validation_mode": "MEASURED", "evidence_refs": ["DE-0073"]}
    ck("§7 LOCAL_MEASUREMENT + ref → valid", AE.validate_packet(ok)["valid"])
    ck("§7 LOCAL_MEASUREMENT ref 無し → invalid", not AE.validate_packet({**ok, "evidence_refs": []})["valid"])
    ck("§7 UNRESOLVED は residuals 要", not AE.validate_packet({**ok, "basis_kind": "UNRESOLVED", "validation_mode": "UNRESOLVED", "evidence_refs": []})["valid"])
    ck("§7 MIXED_BASIS は component_bases>=2 要", not AE.validate_packet({**ok, "basis_kind": "MIXED_BASIS"})["valid"])
    ck("§7 不正 claim_class → fail-closed", not AE.validate_packet({**ok, "claim_class": "TRUE"})["valid"])
    ck("§7 non-dict → fail-closed", not AE.validate_packet(None)["valid"])

# ── adversarial AE-1..7 (§17): すべて reject/invalid されるべき ──
def adversarial():
    ae1 = {"answer_claim_id": "AE-1", "statement": "Sleep Mode will reduce our swap time.",
           "claim_class": "FACT", "basis_kind": "EXTERNAL_SPECIFICATION", "validation_mode": "SPECIFIED",
           "evidence_refs": ["SRC-vllm-docs"], "local_applicability": "NOT_MEASURED"}
    ck("AE-1 SPECIFIED→MEASURED inflation を reject", not AE.compose_ok(ae1)["renderable"])
    ae2 = {"answer_claim_id": "AE-2", "statement": "vLLM has no native capability.",
           "claim_class": "FACT", "basis_kind": "EXTERNAL_RESEARCH", "validation_mode": "OBSERVED",
           "evidence_refs": ["SR-1"]}  # coverage/negative_basis 無し
    ck("AE-2 NOT_FOUND→nonexistence を reject", not AE.compose_ok(ae2)["renderable"])
    ae3 = {"answer_claim_id": "AE-3", "statement": "Qwen3.6 and Coder-Next cannot be co-served.",
           "claim_class": "FACT", "basis_kind": "LOCAL_MEASUREMENT", "validation_mode": "MEASURED",
           "evidence_refs": ["DE-0073"], "scope": "current 2×RTX 5090 config"}  # statement に scope 限定無し
    ck("AE-3 narrow local→global を reject(scope 限定要)", not AE.compose_ok(ae3)["renderable"])
    ae4 = {"answer_claim_id": "AE-4", "statement": "Phase batching is faster.",
           "claim_class": "INFERENCE", "basis_kind": "AI_INFERENCE", "validation_mode": "UNRESOLVED",
           "evidence_refs": ["DE-0080"]}
    ck("AE-4 INFERENCE→FACT を reject(hedge 要)", not AE.compose_ok(ae4)["renderable"])
    ae5 = {"answer_claim_id": "AE-5", "statement": "The feature is stable and fast in our environment.",
           "claim_class": "FACT", "basis_kind": "EXTERNAL_SPECIFICATION", "validation_mode": "SPECIFIED",
           "evidence_refs": ["SRC-vllm-docs"], "source_role": "PRIMARY_OFFICIAL",
           "supports_dimension": "feature existence", "local_applicability": "NOT_MEASURED"}
    ck("AE-5 source authority overreach を reject", not AE.compose_ok(ae5)["renderable"])
    ae6 = {"answer_claim_id": "AE-6", "statement": "co-serve is not feasible.",
           "claim_class": "FACT", "basis_kind": "LOCAL_MEASUREMENT", "validation_mode": "MEASURED",
           "evidence_refs": []}
    ck("AE-6 MEASURED without ref を invalid", not AE.compose_ok(ae6)["renderable"])
    ae7 = {"answer_claim_id": "AE-7", "statement": "vLLM Sleep Mode may reduce swap cost locally.",
           "claim_class": "INFERENCE", "basis_kind": "EXTERNAL_SPECIFICATION", "validation_mode": "SPECIFIED",
           "evidence_refs": ["SRC-1"],
           "component_bases": [{"basis_kind": "EXTERNAL_SPECIFICATION"}, {"basis_kind": "LOCAL_MEASUREMENT"},
                               {"basis_kind": "AI_INFERENCE"}, {"basis_kind": "UNRESOLVED"}]}
    ck("AE-7 mixed-basis flattened を reject(split/MIXED 要)", not AE.compose_ok(ae7)["renderable"])

# ── a valid mixed-split claim renders OK ──
def valid_render():
    good = {"answer_claim_id": "AC-ok", "statement": "現在の構成では co-serve はできません。",
            "claim_class": "FACT", "basis_kind": "LOCAL_MEASUREMENT", "validation_mode": "MEASURED",
            "evidence_refs": ["DE-0073"], "scope": "現在の2×RTX5090 serving config",
            "evidence_summary": "実測(weights 36.5>31.8 GiB/GPU)"}
    r = AE.compose_ok(good)
    ck("valid MEASURED(scope 限定+ref+absence measured)→ renderable", r["renderable"])
    ck("render_compact は raw ID を出さない(実測 label)", "[実測]" in AE.render_compact(good) and "DE-0073" not in AE.render_compact(good))

if __name__ == "__main__":
    print("=== §7 basis validation ==="); basis()
    print("\n=== §17 adversarial AE-1..7 (all must reject) ==="); adversarial()
    print("\n=== valid render ==="); valid_render()
    f = [n for n, c in R if not c]
    print(f"\n=== {len(R) - len(f)}/{len(R)} PASS ===")
    sys.exit(1 if f else 0)
