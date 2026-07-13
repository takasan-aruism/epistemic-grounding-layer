# Impl-Platform-Update — Child ITEM issuance v1 (Proposal A adopted, Taka-approved)

> Decomposition Proposal A (audit-envelope-first) approved. This manifest issues the child ITEM ids under
> PHASE-2DER-EVO-10. Issuance ≠ implementation: each item is still implemented one slice at a time under
> per-slice approval. GPU/vLLM items are REQUIRES_APPROVAL and blocked on the audit envelope.

## Dedup (role-overlap resolution — 31 raw candidates → 28 issued)
The parent §18 (20) and addendum §8 (11) overlap. Three are subsumed, not issued standalone:
- **KNOWLEDGE-PACKET-SCHEMA (§18.2)** → subsumed by **KNOWLEDGE-PACKET-PROVENANCE (§8)** (provenance-complete schema; issuing a bare schema first would mint un-provenanced packets — contradicts A).
- **FAILURE-CLASSIFIER (§18.9)** → = **FAILURE-CLASSIFIER-SCHEMA + FAILURE-CLASSIFIER-RETRY-GUARD (§8)** (the §8 pair *is* the classifier; the discrete-finding schema + retry guard replace a free-text classifier).
- **CLAUDE-L2-AUDITOR (§18.6)** → subsumed by **TWO-LEVEL-AUDIT-POLICY + CLASS-NH-TRIAD-AUDIT** (Claude is the Adjudicator *role* inside the triad, not a separate mechanism).

## Tier 0 — Audit envelope (§8 gates, PLANNED, deterministic/hermetic, must precede any live routing)
Sequence per A: (0)→(1,2)→(3,4)→(5,6)→(7)→(8,9)→(10).
0. **FAILURE-RESOURCE-PRECHECK** — deterministic Python precheck (timeout/OOM/truncation/…) BEFORE any LLM classification; adds FAILURE-RESOURCE class (addendum §3.1–3.2). *First to implement.*
1. **FAILURE-CLASSIFIER-SCHEMA** — discrete evidence-referenced finding schema (§2.2), no free-text verdict.
2. **FAILURE-CLASSIFIER-RETRY-GUARD** — same_class/signature retry counters → CHALLENGED→UNKNOWN→RECLASSIFICATION (§2.3).
3. **BENCHMARK-CLAIM-SCOPE** — scope{} + representation_residual on every perf claim; reuses de_admission claim ceiling (§1.3).
4. **BENCHMARK-RUN-LEDGER** — append-only VLLM-RUNTIME-PROFILER-schema raw benchmark rows (§1.2).
5. **KNOWLEDGE-PACKET-PROVENANCE** — packet id/version/hash/provenance + downstream binding + no-free-text (§4).
6. **STALE-PACKET-GATE** — version/superseded/hash/expiry mismatch → STALE_KNOWLEDGE_PACKET/REBIND_REQUIRED (§4.4).
7. **ECONOMY-DECISION-LEDGER** — append-only economy_decision rows; artifacts reference economy_decision_id (§3.3); CLASS-H.
8. **WEIGHT-INDEPENDENCE-POLICY** — CONTEXT_INDEPENDENT vs WEIGHT_INDEPENDENT recording; reuses independent_judge context check (§5.1–5.2).
9. **CLASS-NH-TRIAD-AUDIT** — Creator/Adversarial Reviewer/Independent Adjudicator inside L2 for CLASS-N/H (§5.3).
10. **HUMAN-ESCALATION-LEDGER** — append-only human_escalation rows + per-ITEM/domain/failure-class aggregation (§7).

## Tier 1 — Core schema/policy (§18 new, PROPOSED, deterministic)
11. **CHANGE-CLASSIFIER** — request → CLASS-N/H/M/S/T (§7); gates audit depth. 12. **DOMAIN-SPECIALIZATION-SCHEMA** (§2.2/3). 13. **INTERFACE-CONTRACT-SCHEMA** (§5). 14. **TWO-LEVEL-AUDIT-POLICY** — class→audit-depth map (§6/§7). 15. **DISSENT-WORKER** (§16.1). 16. **ASSUMPTION-EXTRACTOR** (§16.2). 17. **ESCALATION-ROUTER** — consumes failure-classifier + writes HUMAN-ESCALATION-LEDGER (§13/§15). 18. **HUMAN-ESCALATION-PACKET** — one-decision packet (§15). 19. **ECONOMY-OPERATOR** — allocation policy module (deterministic); live routing changes are CLASS-H + scoped token (§9/§3.4). 20. **MODEL-ROUTING-TABLE** (§10/§17). 21. **DOMAIN-EGL-INTEGRATION** (§18.18). 22. **AUDIT-EGL-INTEGRATION** (§18.19).

## Tier 2 — GATED GPU/vLLM (PROPOSED + REQUIRES_APPROVAL; blocked on Tier 0)
23. **VLLM-RUNTIME-PROFILER** — the live profiler emitting BENCHMARK-RUN-LEDGER rows. 24. **QWEN35-A3B-CONCURRENCY-BENCHMARK**. 25. **QWEN27-CONCURRENCY-BENCHMARK**. 26. **MODEL-SELECTION-TEST** — same-input/condition/rubric compare; only its raw output can lift MODEL_ROUTING_READY (§10/§12). *No live run without a scoped ITEM-bound approval token.*

## Tier 3 — Convergence
27. **END-TO-END-ACCEPTANCE-HARNESS** — hermetic AC-01..AC-14 + AC-BENCH/FAIL/KP/WEIGHT/ECON/HUMAN (§9 addendum).

## Gating invariants (encoded as dependencies)
- Every Tier-2 GPU item depends_on {FAILURE-RESOURCE-PRECHECK, BENCHMARK-CLAIM-SCOPE, BENCHMARK-RUN-LEDGER}.
- MODEL-ROUTING-TABLE depends_on {MODEL-SELECTION-TEST, ECONOMY-DECISION-LEDGER, BENCHMARK-CLAIM-SCOPE}.
- MODEL_ROUTING_READY cannot be set until Tier-0 §8 gates are DONE (addendum §8).
- ECONOMY-OPERATOR live routing / GPU allocation changes = CLASS-H, scoped approval token, no bare boolean.
