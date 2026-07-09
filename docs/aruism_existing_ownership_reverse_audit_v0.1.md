# Aruism existing-ownership reverse audit — v0.1 (READ-ONLY)

**Purpose (Phase 1, Aruism re-confirmation):** determine how much of the Aruism-derived cognition is
*already* implemented / spec'd / experimented in 2DER-EGL, so that Phase-1 does not re-implement existing
research under a new name. **This is not an implementation proposal.** No commit, no code/spec change. Supporting
data: `experiments/aruism_ownership_audit_support_v0.1.json`.

**Method.** Four independent read-only passes: (1) the full ledger DE-0001..0130; (2) git history (123
commits) + narrative docs; (3) the actual `experiments/*` mechanisms read **by data-flow, not by name**;
(4) a hunt for broad→narrow transformations. Faithfulness rules honored: incidents are described first in the
repository's own words; the Aruism-5 labels are attached **only afterward** as *auxiliary* tags, with
`composite` and `none` allowed; no incident is force-fit; "already owned" is judged by data flow, never by name
similarity.

---

## 0. Headline finding (the thing that changes Phase-1 scope)

**The Aruism-5 viewpoints are already compiled into the AFE operator family, already sealed, and already
experimented — with a hedged/negative capability result.** The five viewpoints map almost 1:1 onto the AFE
`ADMITTED` operators:

| Aruism viewpoint | Existing owner (implemented + sealed + scored) |
|---|---|
| 存在の階層性 (hierarchy; move scale/unit boundary) | `OP-HIERARCHY-001` (+ `FE-L-LIMITATION` unit/boundary, scheduler `LENS 'level'`) |
| 存在の連動性 (latent coupling) | `OP-INTERDEPENDENCE-001` (+ `FE-LINK` E×E, `FE-TERNARY`) |
| 存在の対称性 (structural inversion, not mere negation) | `OP-SYMMETRY-001` (+ afe B-arm skeptic, scheduler `LENS 'inversion'`) |
| 存在の対等性 (common unit so A+B is treatable) | `OP-EQUALITY-001` (+ `aggregate.norm()`, `mask_v2()`, `signature_call()`) |
| 軸 (assume axis exists; find the background structure) | `OP-AXIS-001` (+ `FE-AXIS-VARIABLE`, `DETECTION_RECONSTRUCTION_SPLIT`) |
| (存在の創造, adjacent) | `OP-CREATION-001` (scale-transfer *forbidden*) |
| (存在の了解 / understanding) | `OP-UNDERSTANDING-000` **REJECTED** — "duplicates AXIS" |

So the operator-level compilation of Aruism is **done** (arm C/D, sealed `afe_operator_seal.json`, scored
`afe_axis_dimensions.json`). Crucially, **that capability already tested out weak**: `H_primary NOT_CONFIRMED`
→ later `WEAKLY CONFIRMED, margin=1, hint-assisted (H1), not autonomous (H0)`; `C-unique = D-unique = 0` across
three scorers — i.e. the axiomatic engine does **not** uniquely beat generic skepticism. Re-implementing the
5 viewpoints as "new" operators would duplicate AFE *and* ignore that its capability claim already failed to
separate from skepticism.

---

## 1. Taka-breakthrough incident catalogue (facts first, Aruism label after)

Fifteen strongest incidents across all of 2DER-EGL (not just the scheduler branch). Full per-field detail in
the support JSON; here each row is: incident → where it was stuck / dominant frame → Taka move → what changed →
surviving mechanism → evidence → *auxiliary* Aruism label.

1. **DE-0004** — 4 design layers, 0 operational evidence; frame = design completeness. Taka: *"design overtakes
   implementation; drive by operational evidence."* → **Amendment Moratorium MOR-1..4**. *aux: none
   (operational-evidence discipline).*
2. **DE-0011** — verify "recover id from log" using tests that write the log (circular). Taka: *test isolation
   must precede SoR changes.* → `EGL_DATA_DIR` isolation ordering. *aux: coupling (test↔SoR) + none (ordering).*
3. **DE-0018 → DE-0029 (R5→R7)** — `ABSENCE→SPECIFIED`; validation_mode derived from claim polarity. Taka:
   adopt orthogonalization — epistemic-kind orthogonal to polarity; **R5 withdrawn**. → orthogonal
   `validation_mode` + separate `negative_basis` axis. *aux: **axis** (separate two conflated axes) + none
   (author≠adjudicator).*
4. **DE-0032** — "planned source-kind = OFFICIAL_DOCS" would mint a COMPLETED official leg on fetch. Taka:
   *"planned≠acquired≠observed≠searched; look at the primitive that happened, not the upstream name/summary."*
   → ACQ-3b/4b/4c required-vs-observed splits. *aux: **hierarchy** (levels of a claim) + none (derive-from-
   primitive).*
5. **DE-0048** — validator fired on real ESDE inline-corrections. Taka: *"not a format bug — which is right,
   the validator's premise or the world?"* → supersession types `RECORD`/`INLINE` (world-model widened). *aux:
   **composite** (axis: question the frame + hierarchy: boundary).*
6. **DE-0049/0050** — `contract_ok=0/10` masked `grounding=1.00`. Taka: split one metric into M1 grounding /
   M2 placement / M3 format. → 3-axis metric split. *aux: **axis** (latent axes behind one number).*
7. **DE-0072/0073** — Claude recommended its own preference for the GPU co-serve decision. Taka: route the
   decision through the system, seal Claude's preference; "impossible" was **declared, not measured.** → system-
   formed decision packet; `blockage=measurement`; co-serve MEASURED impossible. *aux: composite (symmetry:
   invert the assumption + axis: make it a measurement) + none (author≠adjudicator).*
8. **DE-0090** — meta-frame "cluster instability" read as intrinsic. Taka (mini-C): it's a **procedural** error
   (batch hard single-cluster), not intrinsic; use incremental multi-membership. → DD-ARCH-7. *aux: composite
   (parity: multi-membership + coupling).*
9. **DE-0104** — B-vs-D recorded as an unresolved tie. Taka: scorer-granularity fix — whole-condition scoring
   hid the axis-level difference. → axis-level blind rescore → **precision–recall tradeoff**. *aux: **axis** +
   none (instrument repair).*
10. **DE-0107** — program success = capability-metric improvement. Taka: redefine success = **FORCED_OUT_OF_
    SCOPE intervention frequency → 0** (a system to free the Aruism owner). → DD-ARCH-8 + AA/FOS split. *aux:
    **axis** (reframe the objective) + objective-anchor.*
11. **DE-0113** — SEALED "engine no added value / weaker than skepticism" (over-negative). Taka: *skeptically
    re-check.* → **scorer-reliability crisis** exposed; framing retracted; **MULTI_SCORER_CONSENSUS** permanent.
    *aux: symmetry (opposite scorer → opposite verdict) + none (instrument repair).*
12. **DE-0115** — single-axis reach verdict; scheduler about to be built. Taka: **fix hard-core BEFORE the
    scheduler** (overfit guard — *"same as the Formal-compiler origin-laundering accident"*). → hard-core
    {08,10,30} fixed; single-axis verdict reversed under the 2-axis instrument. *aux: coupling (isomorphism to a
    prior accident) + axis.*
13. **DE-0119..0122** — audit rounds 2–5, the **same** target-aware-authorship DOF hops routing→selection→
    generation→criterion; each patch reopens it. Claude escalates (pre-commitment) rather than patch; Taka
    (terminator): **downgrade to capability-exhibit; generalization → FUTURE-SEALED** — drop the claim, don't
    patch the knob. → round-6 VALIDITY-CLEAN; *"a DOF cannot hop into a claim that no longer exists."* *aux:
    composite (coupling: same signature across rounds + hierarchy).*
14. **DE-0126 (PROCESS-01)** — serial generation, GPU ~96% read as throughput; six audit rounds + an impl
    auditor all missed it. Taka: *independently doubted the speed, asked about effective batch size — changed
    the observation frame from validity to throughput.* → `TASK_VALIDITY_MONITORING ≠ PROCESS_EFFICIENCY_
    MONITORING`; live `PROCESS_OBSERVATION` channel proposed (not built). *aux: **axis** (introduce a missing
    observation axis) + none (missing live channel).*
15. **DE-0128/0130** — "R4 = 0" read as the scheduling-hypothesis being negative. Taka/GPT: audit whether R4 is
    a valid instrument — it was **never even run** (default-fill). → faithful scheduler built; compare→rebuild
    isolated; branch closed NEGATIVE at bar. *aux: composite (construct-validity + symmetry).*

**Reading of the labels.** The recurring auxiliary tags are **axis** (reframe/split the latent structure) and
**none (author≠adjudicator / operational-evidence discipline)**. Many of Taka's highest-signal moves
(DE-0004, 0011, 0072, 0113) are *not* Aruism-5 cognitive operations at all — they are **discipline installs**
(operational-evidence gating, test isolation, route-through-the-system, instrument self-repair). Forcing those
into the 5 viewpoints would be exactly the prohibited move. The genuinely Aruism-flavored moves cluster on
**axis** and **coupling** (isomorphism to prior failures), with **symmetry** (invert the assumption / opposite
scorer) third.

**Attribution honesty.** DE-0005, DE-0028/0036/0043/0065, DE-0111 breakthroughs were driven by an *independent
agent or GPT audit*, not Taka — excluded from the Taka list. DE-0018/0048 insight detection was often GPT;
Taka's move was the ruling/reframe. DE-0072/0073 and DE-0090: Taka *set up* the correction (reframe as
experiment / fix procedure first), the corrective insight was then produced by the system. Not retro-fitted as
"all Aruism."

---

## 2. Ownership hunt — by data-flow (not name)

Verdicts: OWNED (implemented, function cited) · OWNED(exhibit) (implemented inside a capability-exhibit
experiment whose generalization is FUTURE-SEALED — real code, not production wiring) · SPEC-ONLY · PARTIAL ·
ABSENT.

| Capability | Verdict | Owner (file · function) — data-flow |
|---|---|---|
| scale shift | **ABSENT** | scale-*transfer* explicitly **forbidden** (`afe_operators.json` OP-CREATION-001 forbidden_expansions) |
| unit / boundary change | OWNED(exhibit) | `formal_esde_operators.json` FE-L-LIMITATION; scheduler LENS boundary/kind |
| cross-level comparison | OWNED(exhibit) | OP-HIERARCHY-001; scheduler LENS 'level' |
| latent coupling detection | OWNED(exhibit) | FE-LINK (E×E) / FE-TERNARY / OP-INTERDEPENDENCE-001 |
| cross-incident linkage | **OWNED** (retrieval) / ISOMORPHISM **ABSENT** | `run_hbb_F_originloo.retrieve_originloo` — token-overlap retrieval over the ESDE failure/concept corpus, origin-ID leave-one-out + 5-gram leak guard. *Ranks by token overlap, not by structural isomorphism.* |
| inversion / counter-hypothesis | OWNED(exhibit) | afe B-arm; scheduler 'inversion' lens; P_SKEPTIC |
| opposite model | OWNED(exhibit) | OP-SYMMETRY-001 (structural symmetric alternative, not generic negation) |
| common representation / normalization | **OWNED** | `run_afe_walking.aggregate.norm()`; `metaframe_mask.mask_v2()`; `signature_call()` |
| equivalence grouping | OWNED(exhibit) | `run_afe_walking.aggregate()` group-by-normalized-structure (+ support/provenance) |
| latent structure / hidden construct / axis | OWNED(exhibit) | OP-AXIS-001 / FE-AXIS-VARIABLE / `DETECTION_RECONSTRUCTION_SPLIT` |
| compare → rebuild | OWNED(exhibit) | scheduler `compare_call → rebuild_call` (see §3 T1; branch CLOSED NEGATIVE at bar) |
| scheduler routing | **OWNED**(process) + OWNED(exhibit) | `process_aggregate` + `run_process_optimizer` (route to Optimizer only when a deterministic trigger fires); scheduler `rs_run` SELECT/HOLD/SHIFT-AGAIN |
| multi-view | OWNED(exhibit) | scheduler `sample_lenses`/`view_call`; afe D-arm; MULTI_SCORER_CONSENSUS |
| failure-weighted search | **ABSENT** | originloo ranks by token overlap, not failure magnitude; process triggers on cost but weight no search |
| attention mobility | OWNED(exhibit) | scheduler `sample_lenses(seed, attempt, V)` varies lenses by seed AND attempt; HOLD→SHIFT-AGAIN re-points |
| RETURN / DOWNSCALE | OWNED(exhibit) | `run_recon_exhibit.lossy` L1→L2→L3 ladder (mask_v2 → token-mask → skeleton); scheduler 'substrate' lens |
| objective anchor | OWNED(exhibit) | FE-CREATIVITY-ORTHOGONAL (C⊥∇F); rebuild T0-anchor-only; `orchestrate` decision_relevance gate |
| residual / regime detection | **PARTIAL** | residual = FE-EPSILON-RESIDUAL (PROVISIONAL/NARROW); regime = `process_aggregate` `model_switch_overhead_ratio` → DOMINANT_OVERHEAD. No general regime/residual detector over experiment data. |

**Only 3 of 18 are genuinely ABSENT**: `scale shift` (deliberately forbidden), `failure-weighted search`,
`cross-incident **isomorphism** linkage` (retrieval exists, isomorphism does not). Everything else has a
concrete owner.

---

## 3. Transformation cases (broad → narrow surviving mechanism)

- **T1 · multi-view → COMPARE→REBUILD — CONFIRMED (flag).** R4 was a "deterministic cumulative multi-operator
  cascade," audited 0/10 faithful and never run. Rebuilt into the scheduler with ablations; under GPT-strict∧
  Qwen, `RS_flat = 0` on all incidents vs `RS = 4` → compare→rebuild looks **necessary**. *Flag:* the scheduler
  branch **CLOSED NEGATIVE at the bar** — compare→rebuild survived only as the strongest *directional* (not
  confirmed) component. (DE-0128/0129/0130.)
- **T2 · philosophical axis-injection → DETECTION/RECONSTRUCTION latent-construct split — CONFIRMED as pivot /
  PARTIAL as mechanism.** The axiomatic-axis *operators as a capability* were downgraded (no unique reach,
  hint-assisted, fragile). What survived is the **measurement decomposition** `DETECTION_RECONSTRUCTION_SPLIT`
  (permanent instrument #5, robust across 3 scorers: *"B is a strong detection gate but does not substitute for
  reconstruction"*) plus a narrower **precision–recall complementarity** (DE-0104). (DE-0104/0112/0113/0114.)
- **T3 · generalization → capability-exhibit → FUTURE-SEALED — CONFIRMED.** The 6-round downgrade: autonomy
  stripped, then transfer stripped; *"a DOF cannot hop into a claim that no longer exists."* (DE-0120/0122.)
- **T4 · failure-lessons → instrument-self-repair discipline — CONFIRMED.** MASK v2 → XDOMAIN_LITERAL →
  ORIGIN_ID_LEAVE_ONE_OUT → MULTI_SCORER_CONSENSUS → DETECTION_RECONSTRUCTION_SPLIT ("計器の故障を計器で直した";
  a blind spot is caught by an *orthogonal* instrument). A measurement discipline, **not** a data detector.
- **T5 · UNDERSTANDING operator → REJECTED (duplicates AXIS) — CONFIRMED.**
- **H3 · failure-lesson → regime/residual detection — DENIED.** No regime detector, no residual detector exist;
  "regime"/"residual" appear only as domain data or bookkeeping fields. The failure-lessons became **T4**, not a
  detector.

---

## 4. A / B / C classification

### A. ALREADY OWNED — do **not** add as new Aruism functions
The five viewpoints themselves, plus their scheduler/recon relatives, are owned and (mostly) already
experimented:
- 階層性 → `OP-HIERARCHY-001`; 連動性 → `OP-INTERDEPENDENCE-001`+`FE-LINK`; 対称性 → `OP-SYMMETRY-001`;
  対等性 → `OP-EQUALITY-001`+`norm()`/`mask_v2()`; 軸 → `OP-AXIS-001`+`DETECTION_RECONSTRUCTION_SPLIT`.
- inversion/counter-hypothesis, opposite-model, multi-view, attention-mobility, RETURN/DOWNSCALE,
  objective-anchor, equivalence-grouping, cross-level-comparison, unit/boundary-change, common-representation,
  scheduler-routing (process), cross-incident **retrieval** (originloo).
- **Load-bearing caveat:** the AFE-operator capability result is hedged/negative (no unique reach vs
  skepticism). Owned ≠ proven-useful.

### B. TRANSFORMED — Aruism-origin, survived as a different concept/mechanism
- multi-view → **compare→rebuild** (necessary-looking but branch negative at bar).
- axis-injection *capability* → **DETECTION/RECONSTRUCTION measurement split** + **precision–recall
  complementarity**.
- generalization → **capability-exhibit → FUTURE-SEALED**.
- failure-lessons → **instrument-self-repair discipline** (ORIGIN_ID / MULTI_SCORER_CONSENSUS / DET-RECON).
- UNDERSTANDING → **REJECTED (dup AXIS)**.

### C. UNOWNED CANDIDATE — recurs in Taka-breakthroughs, no clear 2DER owner
1. **Meta-instrument doubt** — when a validator/metric/instrument fires or looks bad, ask "is the *instrument's
   premise* wrong, not the data/world?" Recurs at DE-0048 (validator vs world), DE-0113 (scorer vs verdict),
   DE-0126 (util vs throughput). Today handled ad hoc by Taka; no mechanism raises it.
2. **Structural-isomorphism linkage to prior failures** — "this current stall is the *same shape* as past
   accident X" (DE-0115 origin-laundering isomorphism; DE-0122 same-signature-across-rounds; DE-0126 = the EGL
   antipattern at a new layer). `originloo` does *token-overlap* retrieval, **not** isomorphism matching.
3. **Live cross-cutting PROCESS_OBSERVATION / expectation-residual channel** — DE-0126; explicitly proposal-only
   (`H-OPS-01` `transfer_evidence: []`, never fired). A channel that flags "busy-but-under-batched / actual ≫
   expected" on arbitrary runs.
4. **Loop / infinite-regress terminator** — "a defect signature is hopping across levels; escalate / drop the
   claim rather than patch the knob" (DE-0122). Currently a *discipline* honored by pre-commitment; no detector
   recognizes the loop.

Note that C-items 1, 3, 4 are **meta/observation disciplines**, not Aruism-5 cognitive operators; C-2 is the
one that is both Aruism-flavored (coupling) *and* genuinely unowned in its isomorphism form.

---

## 5. The three required answers

**Q1 · How far is "reverse-derive Taka's stalls into the Aruism-5" already done?**
Substantially, but **asymmetrically**. The *operator compilation* from the Aruism source is essentially
complete and already experimented: AFE `SYMMETRY/EQUALITY/INTERDEPENDENCE/HIERARCHY/AXIS(/CREATION)` are the
five viewpoints reified, sealed, scored — and returned a hedged/negative capability verdict. What has **not**
been done systematically is the *incident-side* reverse-derivation this audit performs: cataloguing the
DE-0004/0048/0107/0113/0122/0126-class "Taka unstuck the AI" events and asking which viewpoint (if any) each
instantiates. Those were each handled as one-off corrections + discipline installs, never rolled up. This
document is the first pass at that rollup — and it shows most of Taka's *highest-signal* moves are
**discipline** (author≠adjudicator, operational-evidence gating, instrument self-repair), not Aruism-5
cognition.

**Q2 · Danger of re-implementing while ignoring existing research — HIGH.**
Re-adding the 5 viewpoints as "new" operators would (a) **duplicate the AFE operator family** verbatim;
(b) **ignore that its capability claim already failed** to uniquely beat skepticism (`C-unique=D-unique=0`,
hint-assisted margin=1); (c) risk **reviving multi-view万能論** (explicitly forbidden) and the **primary-
capability claim** (forbidden); (d) re-import the **target-aware-authorship contamination** that took six audit
rounds to terminate. The right default is: treat 階層性/連動性/対称性/対等性/軸 as **ALREADY OWNED** and do not
re-scaffold them.

**Q3 · Minimum real residual after Phase-1 re-confirmation.**
Not the Aruism-5 operators (owned + tested). The genuine residual is the **C-list**, and within it the two that
are both recurrent *and* mechanizable:
- **(C-2) structural-isomorphism linkage** — an isomorphism (not token) matcher from a current stall to the
  ESDE/DE failure corpus. This is the one Aruism-flavored (coupling) unowned capability; `originloo` is the
  natural host but currently only does token overlap.
- **(C-1) meta-instrument doubt** — a check that, when an instrument/metric fires, surfaces "instrument-premise
  vs world" before "producer vs consumer." This is the single most repeated Taka move with no owner.
C-3 (live PROCESS_OBSERVATION) and C-4 (regress terminator) are already *specified* as proposals (PROCESS-01,
escalate-not-patch) and are process/observation disciplines rather than cognition — worth wiring, but they are
not new Aruism functions.

**Everything else is A (owned) or B (transformed). The minimum residual is small, and it is meta/coupling, not
a fresh set of viewpoint-operators.**

---

## 6. Prohibitions honored / what this is NOT
- No new architecture proposal (this catalogues existing ownership; the C-list names residuals, does not design
  them).
- No forced Aruism-5 classification (labels are auxiliary; `composite`/`none` used freely; discipline-installs
  labeled `none`).
- No retro-fitting Taka's words as "all Aruism" (his top moves are labeled discipline, not viewpoint).
- No ALREADY-OWNED verdict by name alone (every verdict cites a data flow / function).
- No revival of any primary-capability claim; no multi-view万能論 (T1 flagged NEGATIVE-at-bar).
- Read-only: no commit, no code/spec change. Deliverable = this doc + `experiments/aruism_ownership_audit_support_v0.1.json`.
