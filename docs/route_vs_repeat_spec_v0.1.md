# Route-vs-repeat construct validation — spec v0.1

**One construct question (NOT solving HBB-30):**
> Does re-rooting the COMPARE stage on a selected center signature (delta origin = that signature) produce a
> **structured intermediate change (the delta-set)** that **matched text repetition/emphasis cannot reproduce**?

This validates whether "center" can be a genuine **pipeline stage variable** (verdict B prerequisite, DE-trace
audit) — distinct from the DE-0134/0135 echo/anchoring defect. It is **not** an answer selector, salience
mechanism, SHAKE detector, or Aruism mode switch.

## Machinery (reused, unchanged logic)
Scheduler reconstruction pipeline: `view_call(fr,lens)` → `signature_call(view)` → `compare_call(sigs)` →
`rebuild_call(deltas, fr)`. A **fixed signature pool** is generated once (V signatures on HBB-30's
`t0_stuck_frame`, frozen seed) and reused by all conditions. Compare runs **deterministically (temp=0, fixed
seed)** so delta-sets are hashable.

## Conditions
- **CONTROL:** `compare_call(sigs)` (current all-pairs) → `deltas_ctrl` → `rebuild_call(deltas_ctrl, fr)`.
- **REPEAT:** compare **unchanged** (`center_ref=None`) → **reuses `deltas_ctrl` verbatim** → `rebuild_call(
  deltas_ctrl, fr, repeat_text=<center signature text>)` — the center text is added as **matched repetition at
  the rebuild input only**. Pre-rebuild delta-set is **byte-identical to CONTROL** by construction.
- **ROUTE:** `compare_call(sigs, center_ref=i)` — deltas computed **relative to the reference signature
  `sigs[i]`** (star-from-reference vs all-pairs) → `deltas_route_i` (≠ `deltas_ctrl`) → `rebuild_call(
  deltas_route_i, fr)`. The center enters at COMPARE, **before rebuild prompt assembly**.

The **only** difference: REPEAT = center text at rebuild; ROUTE = center reference at compare. Same signature
pool, full context, task, model, policies, decoding.

## Center selection (target-blind, no answer)
Center ∈ the **existing signature pool only**. **ALL-SIGNATURE SWEEP** (each signature is `center_ref` once) —
no human pick, no answer-aware selection, no arbitrary external-object injection, no HBB-30 correct-object use.

## Primary construct outcome — DELTA_SET_STRUCTURAL_DIVERGENCE (mechanical, no LLM judgment)
1. `hash(REPEAT deltas) == hash(CONTROL deltas)` (definitional: REPEAT reuses `deltas_ctrl`).
2. `hash(ROUTE deltas_i) != hash(CONTROL deltas)` for eligible nontrivial centers.
3. signature/context multiset hash **identical** across all conditions.
4. source/task/policy/model/decoding identical (recorded + asserted).
5. the ROUTE change occurs **before rebuild prompt assembly**.
6. center text repetition alone (REPEAT) does **not** reproduce the ROUTE delta structure (definitional: REPEAT
   deltas == CONTROL).

## Secondary exploratory outcome
Is the ROUTE **reconstruction output** distinguishable from the REPEAT output (beyond CONTROL)? Measured
per-center, seed-matched. **HBB-30 NDO/REC is NOT the primary** — kept exploratory only.

## Post-run verdict rule (frozen)
- **INVALID** if any invariant (1,3,4,5) is violated, REPEAT deltas ≠ CONTROL, or a forbidden token appears.
- **TEXT EMPHASIS ONLY** if requirement 2 fails (ROUTE deltas == CONTROL for the eligible centers) → the
  re-rooting is inert; center matters only if injected at rebuild = emphasis.
- Given req 2 holds (structural divergence at the intermediate):
  - **STRUCTURAL ROUTING CONSTRUCT VALID** if the ROUTE reconstruction output is distinguishable from REPEAT
    (routing propagates a difference beyond emphasis).
  - **AMBIGUOUS** if ROUTE deltas differ but the ROUTE output is not distinguishable from REPEAT.

## Claim ceiling
Positive ⇒ "compare-stage re-rooting produces a structured intermediate change not reproducible by matched text
repetition." Nothing more. **Forbidden:** HBB-30 solved · Attention-Center validated · salience selector
validated · object-mobility solves fixation · breakthrough reproduced · Aruism regime implemented · fixation
mechanism proven. C≠H. Applicability to *arbitrary external detected objects* is explicitly out of scope (this
validates only re-rooting among the pipeline's own signatures).
