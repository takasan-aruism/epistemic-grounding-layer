# Answer Evidence Contract — Walking-Slice Report

Narrow implementation report (Taka AEC directive §22). Date 2026-07-07.
Not a re-summary of 2DER. Scope: the first AEC walking slice on the GPU/vLLM model-switch question.

Core question (§23): can 2DER expose whether a substantive statement is AI inference / external
research / official spec / local observation / local measurement / reproduction / human declaration /
unresolved — preserving source scope and refusing evidence-strength inflation? **Yes, for this slice.**

---

## A. Existing EGL objects reused (no second SoR — AC-2)

`ANSWER_CLAIM_PACKET` is a **derived rendering artifact** that references EGL records; it admits no
knowledge and creates no ledger. Evidence refs used are real EGL DEs: **DE-0073** (co-serve MEASURED
impossible), **DE-0074** (swap latency MEASURED), **DE-0080** (batching INFERENCE / COUNTERFACTUAL),
plus primitive artifacts (`run_sor/events.jsonl`, `process_aggregate.json`). Claim classes / validation
modes reuse the EGL vocabulary (FACT/INFERENCE/HYPOTHESIS/DESIGN_CHOICE; DECLARED/SPECIFIED/OBSERVED/
MEASURED/REPRODUCED/UNRESOLVED). `claim_registration_status` marks NOT_ADMITTED where the statement is
not an EGL claim (AC-2/3/4). `answer_evidence.py` has **no** admit/ledger-write function (SGQ-AEC-4).

## B. ANSWER_CLAIM_PACKET schema (§5)

`{answer_claim_id, statement, claim_class, basis_kind, validation_mode, egl_claim_ref, evidence_refs[],
source_policy, source_role, supports_dimension, unsupported_dimension, scope, currentness,
local_applicability, claim_registration_status, residuals[], component_bases[], discovered_by,
evidence_source}`. Required-property-driven, not literal-name-driven.

## C. Basis-kind validation rules (§7 — AC-3/4)

9 basis kinds. Ref requirements enforced by `validate_packet` (fail-closed):
LOCAL_MEASUREMENT / LOCAL_CODE_OBSERVATION / LOCAL_REPRODUCTION / EXTERNAL_RESEARCH /
EXTERNAL_SPECIFICATION → `evidence_refs` required; AI_INFERENCE → refs or `ungrounded_reasoning`;
HUMAN_DECLARATION → declaration_source/subject; MIXED_BASIS → ≥2 component_bases; UNRESOLVED → residuals.
`MEASURED` is **not** inferred from prose — only from record-backed fields.

## D. Claim-strength / scope guard (§14 — the anti-inflation gate, AC-5/6/7/8/9)

`strength_guard` (lexical + schema, **fail-conservative**, never claims full semantic entailment). Six
violation types, each blocks rendering:
- `INFERENCE_AS_FACT` — INFERENCE/HYPOTHESIS asserted without a hedge (AE-4)
- `SPECIFIED_IMPLIES_LOCAL` — SPECIFIED basis + a local-performance claim not MEASURED (AE-1, AE-5)
- `NARROW_TO_GENERAL` — narrow local scope but the statement carries no scope qualifier (AE-3)
- `ABSENCE_WITHOUT_BASIS` — absence/impossibility wording without negative_basis / coverage / measured root (AE-2)
- `MEASURED_WITHOUT_REF` — MEASURED wording/basis with empty evidence_refs (AE-6)
- `MIXED_FLATTENED` — ≥2 component bases rendered under one basis_kind (AE-7)

## E. GPU/vLLM walking-slice packets (§16 — AC-1..4 + measured support)

Built from true evidence state; **packet_validity_rate = 1.0**, strength_violations = 0.
- **AEC-AC-1** co-serve infeasible → LOCAL_MEASUREMENT (DE-0073), MEASURED, scope=current config, absence measured.
- **AEC-AC-2** "does vLLM have Sleep Mode?" → **UNRESOLVED / NOT_ADMITTED**. *We never researched it* (it was a
  forbidden pre-seed; the Optimizer emitted a RESEARCH_NEED). The contract therefore refuses to render it as
  SPECIFIED — this is the intended behaviour, and it corrects the directive's illustrative assumption that
  Sleep Mode was already SPECIFIED. Honest state = unresearched.
- **AEC-AC-3** batching may reduce overhead → AI_INFERENCE (DE-0074+DE-0080), UNRESOLVED (B not measured), hedged.
- **AEC-AC-4** local wake latency / TP=2·NVFP4 applicability → UNRESOLVED → routes to concurrent_task_dispatch RESEARCH_NEED.
- **AEC-AC-5** swap ≈174.5s/swap → LOCAL_MEASUREMENT (DE-0074), MEASURED.

## F. Compact Japanese rendering (§9 L1 — AC-10)

No raw ledger IDs in the default surface. Example (AC-1):
```
現在の構成では Qwen3.6 と Coder-Next の co-serve はできません。
[実測]  根拠: 実測(weights 36.5 > 31.8 GiB/GPU)  範囲: 現在の2×RTX5090 serving config
```
AC-2: `[未解決] 不足: vLLM 公式ドキュメントを未調査(EGL 未admit)`. AC-3: `[AI推論] … 実測: 未`.

## G. Expanded evidence trace (§9 L2 — AC-11)

`render_expanded` returns statement, claim_class, basis_kind, validation_mode, source_policy/role,
supports/unsupported_dimension, scope, currentness, evidence_refs, egl_claim_ref, discovered_by vs
evidence_source, claim_registration_status, local_applicability, residuals, component_bases — shown only
on explicit request (根拠は? / どこを調べた? / それはAIの推論?).

## H. Adversarial results (§17 — AE-1..7)

All 7 rejected: AE-1 SPECIFIED→MEASURED, AE-2 NOT_FOUND→nonexistence, AE-3 narrow→global,
AE-4 INFERENCE→FACT, AE-5 source-authority overreach, AE-6 MEASURED-without-ref, AE-7 mixed flattened.
`test_answer_evidence.py` 15/15.

## I. SGQ-AEC results (§18 — AC-15)

- SGQ-AEC-1 "Sleep Mode reduces our swap time" decomposes into 4 distinct bases
  (SPECIFIED existence / MEASURED swap cost / INFERENCE local reduction / UNRESOLVED wake latency) ✓
- SGQ-AEC-2 SPECIFIED does not establish local applicability → guard rejects ✓
- SGQ-AEC-3 NOT_FOUND is not nonexistence by itself → guard rejects ✓
- SGQ-AEC-4 AES is a derived rendering over EGL, not a new SoR → self-grounding reconstructs this,
  sourced to DE-0083 (not prompt memory) ✓

## J. Open gaps

- **Semantic entailment beyond lexical/schema**: the strength guard is fail-conservative lexical+schema;
  it does not do full NLI. It can over-flag (fixed one case: unresolved-framing initially read as
  INFERENCE_AS_FACT) and could miss paraphrases its cue lists don't cover. Not a semantic prover.
- **Claim selection completeness (§10)**: which sentences are "substantive" is not yet automated; the
  slice used a hand-authored claim inventory. A renderer must not silently drop a load-bearing claim.
- **UI integration**: no chat-surface integration; this is the contract + renderer only.
- **Stale/currentness rendering (§12)**: `currentness`/`version_scope` fields exist but the surface only
  shows them for measured/local claims; software version-scope rendering is minimal.
- **Discovery-vs-evidence source (§4)**: fields exist (`discovered_by`/`evidence_source`) but the slice's
  packets are local/measured, so the search-engine-vs-primary-source distinction isn't exercised here.

---

### Acceptance criteria
AC-1✓ AC-2✓ AC-3✓ AC-4✓ AC-5✓ AC-6✓ AC-7✓ AC-8✓ AC-9✓ AC-10✓ AC-11✓ AC-12✓ AC-13✓ AC-14✓ AC-15✓

### Naming (§20, EGL DE-0083 / DD-ARCH-5)
AEC / AES are 2DER answer-layer contracts/roles, **not** responsibility systems. EGL remains the
epistemic responsibility system; RRI remains research-need/design. The answer layer absorbs neither.
