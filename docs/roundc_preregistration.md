# Round C — Value-Axis Experiment Preregistration

Fixed BEFORE the run (outcome-neutral). Date 2026-07-08. Main unresolved question is now **value, not
literal safety** (literal safety settled: concrete 22 → abstract_v2 0, DE-0092/0093).

## Arms (3)
- **A0** — NULL / ordinary (base first-pass, no memory).
- **A1** — ABSTRACT_V2 incident (MASK_PIPELINE v2, sealed 2bfd70f9).
- **A2** — FULL-PREDICATE META-FRAME (MF-002 applicability predicate + suggested axes; no incident, no domain nouns).

CONCRETE incident is retained as a **historical/reference** literal-transfer safety condition (DE-0092), **removed
from the Round C value comparison** — value only.

## Primary stratification (decided pre-hoc, not changed by outcomes)
- `BASE_HAS_TARGET = TRUE` — base first-pass already contains the target axis (N=5: B01/B03/B06/B07/B11).
- `BASE_HAS_TARGET = FALSE` — base misses it (N=10). Both strata ≥5.
Source: gate_pilot.json base_has_target (from ordinary first-pass coverage), fixed before Round C.

## Primary questions
- **RQ-C1** (TRUE stratum): does memory injection improve HIT/USEFUL over NULL, or increase IRRELEVANT?
- **RQ-C2** (FALSE stratum): does FULL-PREDICATE META-FRAME improve historical missing-axis recovery / useful-axis
  generation over NULL *and* ABSTRACT_V2?
- **RQ-C3**: does FULL-PREDICATE preserve structural information vs ABSTRACT_V2 without re-introducing concrete
  domain terms, and reduce IRRELEVANT_AXIS?

## Metrics
Primary value: `HIT`, `USEFUL_AXIS`, `IRRELEVANT_AXIS`, `PARTIAL`, `MISS`, `OVER_TRIGGER` (raw, no composite).
Safety sanity: `XDOMAIN_LITERAL` (sealed XDOMAIN_LITERAL_POLICY_v1, sha 396977dc) — sanity only, not primary.
Current Qwen XDOMAIN semantic flag is NOT a primary metric.

## Scoring
All arms mixed into one anonymous shuffled batch; condition labels removed; fixed rubric.
**External-weight scorer (Claude) required** for load-bearing HIT/USEFUL/IRRELEVANT judgment. Qwen scoring retained
as secondary comparison only.

## N and balance
N ≥ 15. Both BASE_HAS_TARGET strata must have ≥5 cases (satisfied: 5 / 10).

## Preregistered interpretation (fixed before run)
- **TRUE stratum: NULL > memory arms** → redundancy/dilution signal supported.
- **FALSE stratum: FULL META > NULL and ≥ ABSTRACT on useful recovery, without higher irrelevant cost** →
  full-predicate frame has provisional value on subtle missing-axis tasks.
- **ABSTRACT ≈ FULL** → full meta-frame structure adds no demonstrated value beyond abstract incident representation.
- **NULL ≥ all in both strata** → memory injection value not demonstrated; retain safety-only policy (DE-0096/0098).
- **memory arm improves HIT but greatly increases IRRELEVANT/OVER_TRIGGER** → value/safety trade-off, no general
  adoption.

## Carried references (must be in the record)
- MF-002 membership: core_members INC-02/11/16, candidate_members INC-07/13/17 + selection_basis (metaframe_ledger
  META_FRAME_ANNOTATION).
- MF-001 REVIEW_REQUIRED: revision_basis_refs → Round1 HO-4/HO-5 over-trigger + blind rescore (metaframe_ledger
  META_FRAME_REVIEW_NEED_UPDATE).
- XDOMAIN_LITERAL_POLICY seal 396977dc; MASK_PIPELINE v2 seal 2bfd70f9.

## Scope guards
No new meta-frame induction before Round C. No pre-injection LLM gate work before Round C. Value is the question.
