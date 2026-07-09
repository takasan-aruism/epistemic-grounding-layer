# PREREG — Center-shift effect construct test v0.1 (to be FROZEN/HASHED)

Freezes spec `center_shift_prototype_spec_v0.1.md` + binding `center_shift_construct_binding_v0.1.json`.
CONSTRUCT TEST of the CENTER-SHIFT EFFECT only. Not a selector test. Target-blind; C≠H.

## Frozen primary question
Does local observation-center recentering — preserving model/task/source/evidence-policy/authority/decoding/
context-budget, adding no task-relevant information — alter the set of discriminating observations produced?

## Frozen hypothesis
**H_center_shift**: on HBB-30, ATTENTION-SWEEP produces NEW_DISCRIMINATING_OBSERVATION at a higher rate than
CONTROL **AND** ≥ ATTENTION-RANDOM (so the effect is center-coherence, not repetition/emphasis).

## Frozen design
- Incident: **HBB-30** (source = `t0_stuck_frame`, 408 chars). Regions = **4 mechanical sentence spans** (regex
  `(?<=\.)\s+`), verbatim, no field labels, no human pick.
- Conditions: **CONTROL** (no center line) · **ATTENTION-SWEEP** (one line per region, all 4) ·
  **ATTENTION-RANDOM** (one line per 4 length-matched random spans, seed-fixed).
- Center-line template (frozen): `OBSERVATION CENTER (verbatim, already in the source above): <span>. Keep the
  same task and the same rules.` — no rubric-family token (the word "evidence" is **excluded**, N1 fix), no
  "question/reframe/challenge/premise/audit", no answer vocabulary (must violate none of the HBB-30 packet
  `exclusions`).
- Same-system invariant (binding I1–I6, C1): only variable = the center line.
- M = 10 seeds per (condition, region); temp = 0.8; seed = frozen scheme; max_tokens matched. Model = Qwen local.

## Frozen scoring
- **NEW_DISCRIMINATING_OBSERVATION** 0/1/2 per output, **condition-blind**, by a non-author scorer (Qwen local;
  Claude excluded). Generator NEVER sees the rubric. Rubric (scorer-only) = evidence-status / provenance-
  unrecovered / DECLARED-historical / SUPERSESSION. GPT external handoff = optional secondary confirmation.
- Per condition: `p_disc` = fraction of outputs scoring ≥ 1. `p_dec` = fraction scoring 2 (secondary).

## Frozen decision rule
- **Primary effect (does recentering do anything):** SWEEP `p_disc` > CONTROL `p_disc` by one-sided binomial
  (null p = CONTROL `p_disc`), α = 0.05.
- **Confound control (load-bearing):** SWEEP `p_disc` ≥ RANDOM `p_disc` (else the effect is repetition/emphasis,
  not center-shift).
- **H_center_shift CONFIRMED iff both hold.** Per-region SWEEP rates reported descriptively (which region, if
  any, drove it) — **NOT** used to claim salience or selection.
- **R0 interpretive pre-commitment (frozen):** R0 is the most evidentially-loaded of the four regions. If the
  per-region breakdown shows the effect is driven by **R0 alone** (R1–R3 not > RANDOM), the result is read as
  "attention to the pre-existing attribution sentence," **NOT** as "center-coherence in general" and **NOT** as
  "salience selected the productive region." Centering on R0 adds no new information (the attribution is already
  in every condition's full source) — it is an attention re-weighting, the intended IV.
- **RANDOM cleanliness pre-check (frozen, auditable — seeds fixed):** before scoring, report whether any RANDOM
  span overlaps R0 or the "6x" token, to keep RANDOM a clean incoherence control.
- Power/censoring reported (M small; single scorer; single incident). A null reported with its power.

## Frozen claim ceiling
positive ⇒ "observation-center shift **can** alter produced discriminating observations under a preserved
reasoning system." negative ⇒ "no center-shift effect detected on HBB-30 under this design." **NOT claimed
under any outcome:** Attention-Center-selector validated · salience selected the right region · HBB-30 generally
solved · fixation mechanism proven · SHAKE solved · Aruism regime solved.

## Run order (gated)
freeze/hash (this doc) → **independent construct audit** (binding I1–I6/C1/R1/N1–N2/O1/K1: same-system invariant,
mechanical target-blind region rule, no answer injection, confound controls) → **STOP + report** (no
implementation, no run this round). Implementation + run are a later, separately-gated step.
