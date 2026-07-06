# Process Optimizer — Walking-Slice Implementation Plan v0.1

Status: **PLAN — pre-implementation, subject to independent review** (per Taka directive).
Date: 2026-07-07. Author: Claude (Manager). Reviewer: independent (GPT).
Scope: the *first* Process Optimizer walking slice only. Not the full role.

Authority basis: DD-ARCH-4 Naming (EGL DE-0077). The Process Optimizer is a **2DER role, not a fifth
responsibility system**. It observes execution traces and forms *property-preserving simplification
candidates*. It SHALL NOT (a) conduct research, (b) admit knowledge, (c) adjudicate its own proposal,
(d) automatically apply process changes.

---

## 0. What is already closed (prerequisites)

- **F-1 (DW DE-0006, done, tested):** DW live-run primitives persist to an append-only run SoR
  (`run_sor/events.jsonl`), no longer discarded in a TemporaryDirectory. Model-switch and run-boundary
  events are recorded as `PROCESS_EVENT` primitives with real wall-clock timestamps in the *same* log.
  `derive_state` ignores them; `derive_process_trace` derives the trace from primitive timestamps.
  Trial JSON summary is demoted to `BOOTSTRAP_REPORTED`.
- **Why this had to come first:** building the Optimizer on the summary JSON would re-implement the
  `upstream summary self-report → downstream decision` antipattern EGL already killed at the knowledge
  layer — now at the process layer. The Optimizer must read *primitives*, derive its own trace.

This plan covers steps 3–8 of the directive (3, 4, 5, 6, 7, 8), building on 1–2 (done) and 9–10 (done:
DE-0077 naming + SGQ + heuristics ledger).

---

## 1. Data flow (fixed order — do not reorder)

```
DW primitive persistence (F-1 ✓)
  → PROCESS_EVENT primitives (timestamped, authoritative)   ✓ workcell.derive_process_trace
    → derived PROCESS_TRACE (per run / per slice)            ← step 2 ✓
      → PROCESS_PROPERTY_SET (versioned ledger object)       ← step 4  [this slice]
        → deterministic cost trigger (versioned config)      ← step 5  [this slice]
          → Process Optimizer candidate formation            ← step 3,6 [this slice]
            → (if research needed) RESEARCH_NEED → RRI Need Validation → Research Design → EGL
```

The Optimizer sits at the end. It never reaches back up the chain (no research, no acquisition).

## 2. PROCESS_TRACE input (step 2 — done, consumed read-only here)

`dw.workcell.derive_process_trace(task_id)` over `run_sor/events.jsonl`. Yields: model_switches (with
per-switch seconds from SWAP_START/END timestamps), switch_count, switch_failures, total/avg switch
seconds, run_seconds, and the state-phase timeline (CREATE/PLAN/GENERATE/AUDIT/REGENERATE/UPPER_REVIEW).
The Optimizer reads this; it does **not** read trial JSON metrics.

## 3. PROCESS_PROPERTY_SET as a versioned ledger object (step 4)

New artifact: `process_property_set.jsonl` (append-only, versioned). v1 fixes the load-bearing process
properties currently believed to define "same quality":

| id | property | source of truth (how a candidate is checked against it) |
|----|----------|--------------------------------------------------------|
| P1 | generator ≠ auditor | DW independence invariant (identity check) |
| P2 | mandatory independent audit before COMPLETE | DW gate |
| P3 | load-bearing test pass | DW F3/F5 |
| P4 | finding disposition before COMPLETE | DW gate |
| P5 | rework on failing test/finding | DW derive_state |
| P6 | upper review | DW gate |
| P7 | reconstructability from append-only SoR | events.jsonl replay |

**Versioning rule.** Every optimization candidate and every adoption records
`preserved_against_property_set_version`. When a new load-bearing property is later discovered
(e.g. `P8 cross-item audit context isolation`), it is appended as v2, and a deterministic query lists
every past optimization whose `preserved_against` < v2 as `REVIEW_REQUIRED` — "these were judged
'same quality' under a definition that did not yet include P8." This is the process-layer analog of
EGL's current/superseded: we retain *what counted as equivalent quality at that time*, not just the
optimization. **No optimization is preservation-reviewed against a property set it predates.**

## 4. Optimization trigger thresholds as versioned config (step 5)

New artifact: `optimization_triggers.jsonl` (versioned, append-only). Thresholds live here, **not in any
prompt**. v1 (illustrative — reviewer to confirm values): dominant-cost share ≥ 0.5 of run_seconds;
component recurrence ≥ N runs. A deterministic pass over PROCESS_TRACE evaluates the triggers; only a
fired trigger admits a candidate. Rationale: a threshold embedded in a prompt is unversioned, unauditable,
and silently drifts — the same reason EGL keeps gates in code, not in model instructions.

## 5. Walking-slice workflow (steps 3 + 6)

**First workload = the current RRI deterministic-core execution trace** (the rda/rdec/needval/transform/
axis/rqgate runs now persisted in `run_sor/events.jsonl`). The Optimizer is a fresh-context agent given:
- the derived PROCESS_TRACE(s),
- the PROCESS_PROPERTY_SET v1,
- the fired triggers.

It must produce an `OPTIMIZATION_CANDIDATE` with: dominant_cost, current_component,
native_capability_coverage (established | not_established), property_preservation_argument (per P1–P7),
research_required (bool). **It is NOT pre-given** any of: "model switching dominates", "batching /
parallelization", "vLLM native-capability check". Self-formation is measured (§7).

**Role boundary in the flow (step 3).** If the candidate sets `research_required = true` (e.g. native
capability coverage not established), the Optimizer emits a `RESEARCH_NEED` and **stops** — it does not
investigate, fix RQs, acquire sources, or admit knowledge. The need flows:
`RESEARCH_NEED → RRI Need Validation (validate_research_need) → Research Design → EGL acquisition`.
The Optimizer also does not adjudicate its own candidate and does not apply any process change; adoption
is a separate human/independent decision.

## 6. Self-formation vs human-taught measurement (steps 7–8)

`optimization_heuristics.jsonl` (done) separates:
- **SELF_FORMED** (H-SELF-01..03): formed by the system in the GPU co-serve experiment (measurement-
  required, assertion-must-be-measured, swaps/item-is-decision-relevant).
- **HUMAN_TAUGHT / PROVISIONAL** (H-OPS-01 dependency→parallelization/batching; H-OPS-02 native-capability-
  coverage before workaround).

**Walking-slice self-formation check:** run the Optimizer on the RRI trace *without* the H-OPS heuristics
in context. Record which axes it forms alone. Axes it fails to form are logged as needing H-OPS.

**Transfer measurement (step 8, later, separate workload):** on the *next unrelated* operational workload
(e.g. "PDF processing is slow, serial"), observe whether H-OPS-01/02 fire **without a human prompt** and
**change the decision path**. Only then append `transfer_evidence` with `H3=0, heuristic=H-OPS-0x,
decision_changed=true`. This is the first concrete measurement of 2DER **educability** — a human-added
viewpoint transferring to an unrelated problem, which normal "the LLM learned it" claims cannot verify.

## 7. Deliverables of the walking slice

1. `process_property_set.jsonl` v1 (P1–P7) + versioning/review-candidate query.
2. `optimization_triggers.jsonl` v1 (values reviewer-confirmed).
3. Process Optimizer agent (fresh-context) producing one `OPTIMIZATION_CANDIDATE` from the RRI trace,
   pre-seed-free, with property-preservation argument and RESEARCH_NEED emission path.
4. `optimization_candidates.jsonl` (append-only) recording the candidate + `preserved_against` version.
5. Self-formation record (what it formed alone vs needed H-OPS).
6. No process change applied; candidate routed to independent decision.

## 8. Explicitly out of scope for this slice

- Any automatic application of a process change (forbidden by DD-ARCH-4).
- The Optimizer conducting research or touching EGL acquisition.
- The transfer measurement itself (needs a future unrelated workload).
- Tuning DW's auditor (the axis over-flag regression is a DW-effectiveness issue, tracked separately).

## 9. Open questions for the independent reviewer

1. Trigger v1 threshold values (§4) — confirm or set.
2. Is `native_capability_coverage` a field the Optimizer asserts, or must it *always* be `not_established`
   until EGL has admitted coverage evidence? (Leaning: Optimizer may only mark it `established` if it can
   cite an EGL record; otherwise `not_established` → RESEARCH_NEED. This keeps it from self-absorbing the
   research role.)
3. Property-preservation argument granularity — free-text per property, or a structured checklist gate?
4. Should the walking slice run the Optimizer on a *single* slice's trace first, or the whole 6-slice set?
   (Leaning: single trace first, to keep the first candidate small and reviewable.)

---

**Recommendation:** approve/adjust §3–§5 artifacts and §9 questions before I implement the walking slice.
Nothing here is built yet beyond F-1 and the heuristics/naming ledgers.
