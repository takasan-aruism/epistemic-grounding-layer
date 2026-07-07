# AFE (Axiomatic Frame Engine) — Implementation / Experiment Plan v0.1

Status: **PLAN — pre-implementation, for review (spec v0.2 §33).** Not implemented. Grounded in the actual
registered sources. Date 2026-07-08. Producing this plan is not evidence AFE works.

## A. Aruism source registration path
Registered **SRC-ARUISM-ORIGINAL** (EGL ontology_sources.jsonl): `/home/takasan/Aruism-AI-Local/Docs/Aruism
Original Text 改訂版１.txt`, 792 lines, author Taka, sha256 `60fda1d0513e4b849ac9…`, tier ARUISM_CORE.
Source-verified concept spans: 対称性 ×26, 対等性 ×20, 軸 ×31, 階層 ×19, 創造 ×29 (第二章七節 存在の創造 =
共鳴/resonance), 存在の了解 ×5 (第二章 = 対立二項を内包する新軸の創造 + 体験的), 相互依存 ×1 (mostly
連動性/響き合い). Registration ≠ validation of operator utility.

## B. ESDE-derived ontology source inventory / gaps
- **known/unknown frontier** — `SCATTERED_GROUNDED`: present in esde_unified_inventory / ESDE_Developmental_Report
  / ESDE_技術仕様書 / 概念理解.md, no single authoritative file → **span-level manifest required** before compile.
- **existence defense (存在防衛)** — **SOURCE_GAP**: no authoritative written definition found in docs.
- **destructive / constructive creation (破壊的創造)** — **SOURCE_GAP**: no authoritative definition found.
→ existence-defense and destructive-creation **cannot be admitted as operator sources** until Taka authors a
definition note (§32.2). The 8-operator set is **NOT source-complete**; only Aruism-core + known/unknown are grounded.

## C. Source-to-concept extraction method
Deterministic: for each registered concept, fixed source-span refs selected at registration (chapter/section
anchors, e.g. 存在の創造 = 第二章七節). Serialize the span set → SHA-256 seal **before** operator finalization.
No LLM reconstruction of authoritative definitions from memory (AC-2). Extraction produces a
`CONCEPT_SPAN_SET` per concept, not a paraphrase.

## D. Operator compiler schema
`source concept → source spans → structural-function extraction → COMPILABLE? → operator candidate → external-
weight source-fidelity audit → operator-admission incident test → admit / narrow / reject`. Compiler outcomes
(AC-3): `COMPILED_CANDIDATE | NOT_COMPILABLE | SOURCE_INSUFFICIENT | DUPLICATES_EXISTING_OPERATOR`. Origin-
laundering check: does the structural function import a later ESDE/2DER/Meta-Frame lesson into an earlier Aruism
concept? (AFE-R4/R19). NOT_COMPILABLE is a first-class, non-failure outcome; operator count is an outcome, not a
target.

## E. Initial operator candidates (source-grounded dispositions)
| operator | source basis | disposition (pre-audit) |
|---|---|---|
| SYMMETRY | 存在の対称性 (×26) | COMPILED_CANDIDATE |
| EQUALITY / EQUAL-STANDING | 存在の対等性 (×20) | COMPILED_CANDIDATE |
| INTERDEPENDENCE | 連動性 / 響き合い (相互依存 literal ×1) | COMPILED_CANDIDATE — note: source wording is 連動性, not 相互依存; audit for over-specificity |
| HIERARCHY | 階層 (×19), 部分と全体, 階層の創造・再編成 (l.691) | COMPILED_CANDIDATE — sealed probe must NOT name incident-derived levels (mechanism/impl/config) |
| AXIS | 軸 (×31), 新たな軸の創造 (l.505/508) | COMPILED_CANDIDATE — **must include axis non-totality / structural-exclusion** (l.691 grounds "既存構造に留まらず"); AXIS v0.1 completeness negative test (AC-34) |
| 存在の了解 (UNDERSTANDING) | l.499-541: = 対立二項を内包する新軸の創造 + 体験的 | **COMPILATION_UNRESOLVED** — source defines it AS new-axis creation → **high risk DUPLICATES_EXISTING_OPERATOR(AXIS)**; experiential content may be NOT_COMPILABLE. No runtime operator until a *distinct* function is source-demonstrated (AC-35) |
| CREATION | 第二章七節 存在の創造: 存在同士の共鳴; 根源的創造は直接扱えない (l.732) | COMPILED_CANDIDATE around **resonance-generates-new-structure** (operational layer only). **v0.1 (discard-concrete/preserve-invariant/transfer) = origin-laundering, explicit negative test** (AC-33): it is a TIER-C abstraction lesson, not the source definition |
| KNOWN/UNKNOWN | TIER B, scattered | HOLD — compile only after B's span manifest exists |

## F. External-weight operator audit arrangement
Each COMPILED_CANDIDATE gets a Claude external-weight source-fidelity audit (§7.9) with disposition
`SOURCE_FAITHFUL | NARROW | ORIGIN_LAUNDERING | DUPLICATE | NOT_COMPILABLE | SOURCE_INSUFFICIENT`. Two mandatory
negative test cases must be caught: CREATION-v0.1 (origin laundering) and AXIS-v0.1 (missing non-totality). The
auditor is not the same context that authored the operator.

## G. Operator-admission incident manifest
`OPERATOR_ADMISSION_INCIDENT_SET`: incidents used to compile/narrow/merge/reject/admit operators. Candidate
source: a bounded subset of 2DER operational incidents (Sleep-Mode wake, disposition-before-rework, batch-re-
induction, memory-injection) + ESDE_失敗の記録.md entries. Record IDs + source refs + sha256 + sealed_at + role.

## H. Held-out incident set construction
`AFE_HELDOUT_INCIDENT_SET`: 20–30 reconstructable H3/H4 incidents with (pre-intervention frame / later Taka or
audit intervention / post-intervention decision effect). Held-out INPUT = pre-intervention frame only; exclude
later intervention, final lesson, post test, accepted claim (§24). **Disjointness proof**: `ADMISSION ∩ HELDOUT
= ∅`, both manifests hashed (AC-8, AFE-R16). Sources: ESDE_失敗の記録.md + verified frame-delta corpus (概念理解.md)
+ 2DER incidents NOT in G.

## I. Concurrent request architecture
Actual admitted operator count = **compiler outcome** (likely 5–7, not a hard 8 — 存在の了解 may drop, ESDE ones
gated by source). Concurrent independent calls to the one Qwen3.6 server, each in its own context, no operator
sees another's output (AFE-R6). Matched CONTROL F placebo ensemble uses the **same call count** as admitted D.
Independence guarantee: separate requests, no shared conversation state.

## J. Deterministic aggregation design
schema validation → invalid-SIGNAL rejection → basis-ref existence check → exact-duplicate removal → normalized
relation formatting → same-basis grouping → provenance preserved (§13). Raw signals retained (AC-13). Any LLM-
assisted clustering keeps raw signals + membership + clusterer identity; aggregation is never a silent admission
authority (AC-14). Convergence recorded, never treated as truth-by-vote (AC-15).

## K. Orchestrator contract
Input: current-frame summary + normalized convergence candidates + provenance + basis refs. **Operator identities
anonymized in condition 1** (AFE-R8: prevent "AXIS sounds important" bias). Output: ≤3 FRAME_EXPANSION_CANDIDATE
(AC-16). Evaluates candidates on decision-relevance, not support count.

## L. RRI handoff packet
AFE emits FRAME_EXPANSION_CANDIDATE → RRI (intent/premise/current-decision → Research-Axis candidate → need-
validation / research-design → EGL acquisition or DW experiment). AFE does not finalize axes, does not research,
does not browse (AC-17/18).

## M. Experiment controls
- **A** ordinary Qwen3.6. **B** generic skepticism. **C** bounded admitted Meta-frame predicate library — model
  sees predicates + operations, may self-select none/one/bounded-multiple (§25.1; NOT a production selector).
- **D (TREATMENT)** AFE operator ensemble + deterministic aggregation + orchestrator.
- **E** sealed direct-source excerpts (deterministic excerpt rule, e.g. first bounded paragraph under each
  registered concept heading, SHA-256 sealed before held-out eval — NOT a human summary; §25.2).
- **F** placebo ensemble: same call count / budget / SIGNAL schema / aggregation / orchestrator, but each pseudo-
  operator = a sealed generic-skepticism paraphrase (§25.3; separates operator-content value from ensemble-
  mechanism value, AFE-R17).

## N. Leak controls
Probe contracts frozen + serialized + SHA-256 sealed **before** held-out finalization (AC-5). Deterministic
`probe_target_overlap.json` (normalized 3/4/5-gram + key-phrase overlap) generated before answer scoring, not
altered by results (§5.3). Recovery scored as `RECOVERED_LOW_OVERLAP | RECOVERED_HIGH_OVERLAP | PROBE_HANDED`;
**PROBE_HANDED threshold preregistered** before evaluation. Admission/held-out disjoint (§5.4). Probes use source-
grounded structural language, avoid incident-derived examples.

## O. Evaluation metrics (no composite)
Primary: HISTORICAL_MISSING_AXIS_RECOVERY, RECOVERED_LOW/HIGH_OVERLAP, PROBE_HANDED, USEFUL_NOVEL_AXIS,
IRRELEVANT_AXIS, OVER_TRIGGER, DECISION_PATH_CHANGE. Operator-level: SIGNAL/NO_SIGNAL counts, VALID_SIGNAL_RATE,
UNIQUE_USEFUL_CONTRIBUTION, DUPLICATE_CONVERGENCE, H3_RECOVERY_CONTRIBUTION, IRRELEVANT_CONTRIBUTION. Orchestrator:
candidate count, compression ratio, useful retention, useful single-operator-signal loss, generic-convergence
acceptance. External-weight (Claude) required for load-bearing recovery/useful/irrelevant; Qwen secondary.

## P. Process-cost instrumentation
8-(or N-)request concurrent wall time, single-request latency distribution, queue behavior, tokens/operator,
orchestrator latency, total AFE wall time, error/timeout rate; sequential-subset comparison (§29). Do not assume
concurrency is faster — measure. Process trace available to Process Optimizer later.

## Q. EGL record types / ownership
EGL owns: ONTOLOGICAL_CONCEPT_SOURCE, AXIOMATIC_OPERATOR (+version/status), OPERATOR_SIGNAL observations,
OPERATOR_CONVERGENCE_CANDIDATE, FRAME_EXPANSION_CANDIDATE evidence, operator transfer/failure patterns.
Currentness authority = EGL. RRI consumes; DW revises but cannot self-admit current (AC-19/20); Director routes;
Meta-Frame Factory stays separate (AC-21). No independent AFE currentness store.

## R. Open gaps
1. **ESDE-derived tier incomplete**: existence-defense + destructive-creation = SOURCE_GAP → need Taka definition
   notes before those operators exist. known/unknown needs a span manifest. → first experiment runs **Aruism-core
   + (optionally) known/unknown** only, explicitly marked source-incomplete.
2. **存在の了解 disposition** likely DUPLICATE(AXIS)/NOT_COMPILABLE — decided by compiler+audit, not pre-judged.
3. Held-out corpus reconstructability: how many of the 20–30 have clean pre-frame / intervention / effect?
   (ESDE_失敗の記録.md = 163 lines; may need 2DER incidents to reach 20.)
4. Single external-weight scorer (Claude); Qwen secondary only. No GPT scorer available as a tool.
5. PROBE_HANDED threshold + excerpt-selection rule + placebo prompts must all be preregistered/sealed before eval.
6. Admission/held-out disjointness shrinks usable corpus — must confirm ≥20 held-out remain after removing
   admission incidents.

## Non-claims
No general "LLM acquired metacognition" claim (AC-29). A positive result is scoped to frame-expansion assistance
under tested incident classes (AC-30). Aruism = structural source material, not truth (AC-31). This plan is for
review; no operators compiled, no experiment run, until review.
