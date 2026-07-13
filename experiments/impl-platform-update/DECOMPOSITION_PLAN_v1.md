# Impl-Platform-Update — Decomposition Plan v1 (§19.7–10 + Addendum §10 deliverable)

> This is the ONE decomposition deliverable for ITEM-2DER-IMPL-PLATFORM. It does NOT issue child ITEM ids,
> implement code, or touch GPU/:8005. Parents: 2DER_IMPL_PLATFORM_UPDATE_SPEC.md + _AUDIT_ADDENDUM.md.
> Self-audit is NON-INDEPENDENT (single Claude context authored both parents' ingest and this plan → WEIGHT_INDEPENDENT=false, CORRELATED_BLIND_SPOT_RISK=ACCEPTED). Child-id issuance requires Taka approval.

## 1. Relationship to the existing parallel-ops spec (PHASE-2DER-EVO-09)

PHASE-09 built the **independence + evidence core of a single task's pipeline**: role separation, procedure
audit, independent judge, evidence-class promotion, fixed router. This update is **strictly wider**: it adds
(a) a *process×domain* two-axis split, (b) *change-class-scaled* two-level audit, (c) a *resource/economy*
layer that governs how LLM work is served, and (d) a *failure-classification + escalation* layer that decides
where a bad result goes. PHASE-09 is a **proper substrate** of this update, not a competitor.

| This update's need | PHASE-09 asset | Verdict |
|---|---|---|
| Role/context separation across process stages | `role_schema.py` (ROLE_OUTPUT_SCHEMA, new_context, assert_separation) | **EXTEND** (add process×domain roles: DESIGN-AUDIT-L2, DOMAIN-*, INTERFACE-CONTRACT, ECONOMY-OPERATOR, DISSENT) |
| L2 audit = separate context reviews creator | `independent_judge.py` (executor≠judge, forbidden leading fields) | **EXTEND → triad** (Creator/Adversarial/Adjudicator; addendum §5.3) |
| Did execution follow the plan | `procedure_audit.py` | **REUSE as-is** (feeds L2 + failure classifier) |
| Evidence class + no executor self-promotion | `egl_integration.py` (EXECUTOR_MAX_CLASS=OBSERVED, promotion_decision) | **REUSE + EXTEND** (benchmark MEASURED gate = raw-artifact required; addendum §1.4) |
| Fixed state machine / no shortcut transitions | `parallel_router.py` (STATES, ALLOWED, FORBIDDEN_DIRECT) | **EXTEND** (add §17 process states + MODEL_BENCHMARK_* substates + CHANGE_CLASSIFIED gate) |

## 2. Integration / Extension / New classification of the 20 parent candidates (§18)

- **REUSE (already exists, wire only):** none are complete, but 3/5/9 lean on existing modules.
- **EXTEND existing PHASE-09 module:** 5 TWO-LEVEL-AUDIT-POLICY (→independent_judge triad), 6 CLAUDE-L2-AUDITOR (→independent_judge), 9 FAILURE-CLASSIFIER (new but consumes procedure_audit), 18 DOMAIN-EGL-INTEGRATION + 19 AUDIT-EGL-INTEGRATION (→egl_integration + de_admission), 20 END-TO-END-ACCEPTANCE-HARNESS (→parallel_router).
- **NEW schema/policy (no live compute):** 1 DOMAIN-SPECIALIZATION-SCHEMA, 2 KNOWLEDGE-PACKET-SCHEMA, 3 INTERFACE-CONTRACT-SCHEMA, 4 CHANGE-CLASSIFIER, 7 DISSENT-WORKER (schema+prompt only), 8 ASSUMPTION-EXTRACTOR, 10 ESCALATION-ROUTER, 11 HUMAN-ESCALATION-PACKET, 12 ECONOMY-OPERATOR (allocation policy, deterministic), 17 MODEL-ROUTING-TABLE.
- **NEW + requires live GPU/vLLM (GATED, later, approval-token bound):** 13 VLLM-RUNTIME-PROFILER, 14 QWEN35-A3B-CONCURRENCY-BENCHMARK, 15 QWEN27-CONCURRENCY-BENCHMARK, 16 MODEL-SELECTION-TEST. **None run in this decomposition.**

## 3. Addendum §8 priority items — the audit gates that must precede live routing

These 11 (addendum §8) are **schema/ledger/policy only** (no live compute) and are the *safety envelope* for the
GPU items above. Classification:
- **EXTEND egl_integration/de_admission:** BENCHMARK-CLAIM-SCOPE (→claim scope + representation_residual), KNOWLEDGE-PACKET-PROVENANCE + STALE-PACKET-GATE (→artifact_registry content_hash + de_admission evidence_refs), WEIGHT-INDEPENDENCE-POLICY (→independent_judge context check), CLASS-NH-TRIAD-AUDIT (→independent_judge triad).
- **NEW append-only ledger:** BENCHMARK-RUN-LEDGER, ECONOMY-DECISION-LEDGER, HUMAN-ESCALATION-LEDGER (all follow the existing append-only jsonl + sole-writer discipline; route to existing EGL/DS SoR, no new SoR class unless justified).
- **NEW schema/guard:** FAILURE-CLASSIFIER-SCHEMA, FAILURE-CLASSIFIER-RETRY-GUARD, FAILURE-RESOURCE-PRECHECK (deterministic Python precheck BEFORE any LLM classification; addendum §3.2).

## 4. Connection points to existing DONE modules (§19.9 + addendum §10.3 — reference, don't reimplement)

| New mechanism | Existing EGL/2DER asset reused | How it connects (no reimpl) |
|---|---|---|
| Benchmark claim scope + no over-generalization | **de_admission claim ceiling** (HARD_REJECT) + **representation_residual** (egl `run.py`/`test_etb.py`) | benchmark claim carries `scope{}` + `representation_residual[]`; de_admission downgrades unscoped→REPORTED |
| Benchmark MEASURED promotion | **egl_integration.promotion_decision** (EXECUTOR_MAX_CLASS=OBSERVED) | executor/profiler cannot self-promote; MEASURED needs raw_benchmark_artifact_id + non-executor context |
| Packet provenance / stale gate | **artifact_registry** (content_hash, git_blob_sha, supersedes) | packet_id/version/content_hash are artifact_registry rows; stale gate = hash/supersedes mismatch |
| Failure classifier independence | **independent_judge** (Classifier A/B + adjudication) | reuse the executor≠judge context check + forbidden leading fields |
| L2 triad adjudication | **independent_judge.judge** + role_schema.assert_separation | Adjudicator = separate context; verdict states already defined |
| Economy decision ledger, human-escalation ledger | **intervention.py** (append-only on DS event stream) + **authority** scoped tokens | append-only pattern; CLASS-H economy changes need scoped approval token (no bare boolean) |
| Procedure conformance in failure routing | **procedure_audit.py** | FAILURE-EXECUTION vs FAILURE-DESIGN split reads procedure_audit.conformant |

**EGL reuse candidates (addendum §10.2), all confirmed present:** representation_residual ✓ (egl run.py/demo_acquisition_task.py/test_etb.py), claim scope / ceiling ✓ (de_admission HARD_REJECT + BEHAVIORAL→REPORTED downgrade), packet-ID binding ✓ (artifact_registry content_hash+supersedes), evidence-class gate ✓ (egl_integration promotion_decision), independent adjudication ✓ (independent_judge). → **No re-implementation of these; the new items are thin adapters that call them.**

## 5. Three decomposition proposals (≥3 per §19.10)

**Proposal A — Audit-envelope-first (RECOMMENDED).** Issue the addendum §8 gates *before* any parent §18 item,
in this order: FAILURE-RESOURCE-PRECHECK → FAILURE-CLASSIFIER-SCHEMA+RETRY-GUARD → BENCHMARK-CLAIM-SCOPE +
BENCHMARK-RUN-LEDGER → KNOWLEDGE-PACKET-PROVENANCE + STALE-PACKET-GATE → ECONOMY-DECISION-LEDGER →
WEIGHT-INDEPENDENCE-POLICY + CLASS-NH-TRIAD-AUDIT → HUMAN-ESCALATION-LEDGER. Only then CHANGE-CLASSIFIER,
DOMAIN/KNOWLEDGE/INTERFACE schemas, ECONOMY-OPERATOR (policy), then the GATED GPU benchmark items last.
*Rationale:* the addendum explicitly says these must exist before MODEL_ROUTING_READY / DOMAIN-SPECIALIZATION /
ECONOMY-OPERATOR go live; building them first means no routing/economy artifact is ever minted un-provenanced,
so nothing has to be re-rooted later (Taka's stated concern).

**Proposal B — Vertical thin-slice.** One end-to-end path first (CHANGE-CLASSIFIER → one DOMAIN schema →
KNOWLEDGE-PACKET provenance → triad L2 → FAILURE-CLASSIFIER → ESCALATION-ROUTER → HUMAN-ESCALATION-LEDGER) on a
single CLASS-S change, then widen. *Rationale:* proves the §17 state machine end-to-end fastest; *risk:* the
benchmark/economy gates lag, so any early live measurement would be un-scoped — contradicts addendum §1.

**Proposal C — Layer-parallel.** Three independent tracks (Serving/Economy, Audit/Escalation, Domain/Interface)
each to schema-complete, converge at END-TO-END-ACCEPTANCE-HARNESS. *Rationale:* maximal parallelism; *risk:*
cross-track interface drift and duplicated ledger conventions; needs an INTERFACE-CONTRACT owner up front.

**Selection rule (not yet executed):** default to **A** unless Taka prioritizes a demonstrable end-to-end path,
in which case **B** with the §8 benchmark/economy gates pinned as blockers on any live step.

## 6. Precise evidence class of the current benchmark claims (addendum §10.4)

- "35B-A3B 単発~200 tok/s / 30並列~3,000 tok/s" → **REPORTED**. Self-reported in prose; no machine-generated raw
  benchmark artifact conforming to VLLM-RUNTIME-PROFILER schema exists. Under addendum §1.1 it cannot exceed REPORTED.
- ITEM-0015 A/B pilot (Coder-27B Pass@1 1.0 vs Qwen 0.667, 27B ~2.3× slower, n=3) → **limited-scope MEASURED**,
  raw artifacts present under `egl/experiments/ITEM-0015-ab/` (DE-0241), but **underpowered (n=3)** → the *switch
  decision* stays KEEP_INCUMBENT / provisional; the *superiority* claim stays REPORTED (per prior discipline).
- Net: **no benchmark currently qualifies to lift MODEL_ROUTING_READY.** default_model stays 35B-A3B by §10 rule,
  NOT by a measured routing decision.

## 7. Unresolved weight-separation conditions (addendum §10.6)

- Every L2 audit performed so far in 2DER is **same-weight** (Claude reviews Claude, or Qwen reviews Qwen) →
  `WEIGHT_INDEPENDENT=false`. The triad (Creator/Adversarial/Adjudicator) reduces but does not remove correlated
  blind spots while all three share weights.
- **Open, needs Taka decision at child-issuance time:** (a) whether an external adjudicator (GPT or a non-Qwen
  model) is available/authorized for CLASS-N/CLASS-H; (b) if only same-weight is available, the addendum requires
  *stricter human-approval conditions* — that threshold is not yet defined; (c) this decomposition plan itself is
  single-context self-audited → an independent (ideally different-weight) review of THIS plan is not yet done.

## 8. Not done in this slice (explicit)
Child ITEM id issuance; any code; any GPU/vLLM/:8005 op; any live benchmark; MODEL_ROUTING_READY change;
absorbing either parent into existing items; independent (different-weight) review of this plan.
