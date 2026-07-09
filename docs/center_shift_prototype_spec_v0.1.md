# Center-shift effect — construct-test spec v0.1

**One question (construct test, NOT a selector test):**
> Does local observation-center recentering — **without** changing the reasoning system, task, source, or
> evidence policy, and **without** adding task-relevant information — alter the set of discriminating
> observations a model produces?

This tests the **CENTER-SHIFT EFFECT** only. Whether *salience* can predict/select a productive center is a
**separate second stage** (deferred). Adopted per Taka after the ledger-salience branch (DE-0133: selector role
retained, predictive value unverified).

## Benchmark
- **Primary incident: HBB-30** (baseline repeated failure: consensus R0 0/10, R2 0/10; fixation is *in the
  frame*: "treat the 6x as a result whose derivation should be recoverable"). HBB-08 = optional secondary
  (weaker: base partial 3/10). HBB-10 excluded (base succeeds 9/10).
- **Source = `hbb_sealed_t0.json` HBB-30 `t0_stuck_frame`** (408 chars) — the exact frame the base model saw.
- **Rubric discriminating observation (scorer-only, NEVER to generator):** evidence-status of the 6x claim /
  provenance unrecovered / DECLARED-historical-claim / later evidence as SUPERSESSION (from
  `breakthrough_structure`).

## Mechanical region rule (target-blind, no answer, no human pick)
Regions = **regex sentence split** of `t0_stuck_frame` (boundary `(?<=\.)\s+`), verbatim, no field labels.
HBB-30 → **4 regions R0–R3** (claim-assertion / "treat as recoverable" / explain-reconstruct / identify-derivation).
**SWEEP covers ALL regions; no selection.**

## Conditions (minimal)
- **CONTROL:** system + source + task. No center line.
- **ATTENTION-SWEEP (4 sub-conditions):** identical, **+** one appended line per region Rk:
  `"OBSERVATION CENTER (verbatim, already in the source above): <Rk>. Keep the same task and the same rules."`
  (suffix carries **no** rubric-family token — the word "evidence" is deliberately excluded, N1 fix.)
- **ATTENTION-RANDOM (4 sub-conditions):** identical center line, but the span is a **random contiguous
  substring matched to R0–R3's lengths** (seed-fixed offsets) — the repetition/emphasis control.

The **only** variable across conditions is the presence/content of that one center line. CONTROL isolates
line-presence; RANDOM isolates repetition/emphasis; **SWEEP vs RANDOM isolates center-coherence** (load-bearing).

## Same-system invariant (strict)
Identical across ALL conditions: model (Qwen local :8005) · system prompt · task · source packet · evidence
policy · authority policy · decoding params (temp, seed, max_tokens) · context budget. Any difference beyond the
one center line ⇒ construct INVALID.

## Outcome
**Primary = NEW_DISCRIMINATING_OBSERVATION** (0 none / 1 partial / 2 decisive): each output scored for presence
of a rubric discriminating observation, **condition-blind**, by a non-author scorer (Qwen local; Claude
excluded; GPT handoff optional secondary). Generator blind to the rubric. Effect = ATTENTION > CONTROL.

## Parameters (to be frozen in prereg)
M = 10 seeds per (condition, region); temp fixed; matched max_tokens. Total ≈ CONTROL 10 + SWEEP 40 + RANDOM 40
= 90 generations + scoring. HBB-30 primary.

## Claim ceiling
Positive ⇒ **"observation-center shift can alter produced discriminating observations under a preserved
reasoning system."** Nothing more. **Forbidden:** Attention-Center-selector validated · salience selected the
right region · HBB-30 generally solved · fixation mechanism proven · SHAKE solved · Aruism regime solved.
If positive → next branch asks "can salience predict/select the productive center?".
