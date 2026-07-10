# PREREG — Route-vs-repeat construct validation v0.1 (to be FROZEN/HASHED)

Freezes spec `route_vs_repeat_spec_v0.1.md`, binding `route_vs_repeat_construct_binding_v0.1.json`, hash
contract `route_vs_repeat_hash_contract_v0.1.json`. CONSTRUCT VALIDATION of compare-stage re-rooting. **Not
solving HBB-30.** Target-blind (center ∈ existing signature pool, all-sweep); C≠H.

## Frozen construct question
Does re-rooting COMPARE on a selected center signature (delta origin = that signature) produce a structured
delta-set change that matched text repetition/emphasis cannot reproduce?

## Frozen design
- Machinery = scheduler pipeline (view→signature→compare→rebuild), logic unchanged.
- **Fixed signature pool**: V = 6 signatures generated once on HBB-30 `t0_stuck_frame` (frozen lens set + seed),
  persisted, reused by all conditions.
- **CONTROL** compare all-pairs (temp=0, seed s0) → `deltas_ctrl` → rebuild.
- **REPEAT** reuse `deltas_ctrl` verbatim → rebuild(`deltas_ctrl`, fr, `repeat_text=sigs[i]`). center text at
  rebuild only; pre-rebuild deltas byte-identical to CONTROL.
- **ROUTE** compare(`sigs`, `center_ref=i`, temp=0, seed s0) → `deltas_route_i` → rebuild(`deltas_route_i`, fr).
  center at compare, before rebuild assembly.
- **ALL-SIGNATURE SWEEP** over i ∈ [0,V); CONTROL/REPEAT attempt-count + seed-scheme matched to ROUTE.
- Compare temp=0 (deterministic delta hashing); rebuild temp = 0.8, M = 5 seeds/(condition,center) for the
  secondary output check.
- Rooted-compare prompt = topology change (all-pairs → star-from-reference); marks one signature REFERENCE;
  **no** "focus/central/reframe/premise/provenance/challenge/question" and **no** HBB-30 answer vocabulary.

## Frozen primary outcome — DELTA_SET_STRUCTURAL_DIVERGENCE (mechanical)
1. `hash(REPEAT deltas) == hash(CONTROL deltas)` (definitional).
2. `hash(ROUTE deltas_i) != hash(CONTROL deltas)` for eligible nontrivial centers (report the fraction).
3. signature-pool hash identical across all conditions.
4. source/system/decoding hash identical across all conditions.
5. ROUTE change is at compare (center_ref set, rebuild repeat_text absent); REPEAT is at rebuild (compare
   center_ref=None, rebuild repeat_text present).
6. REPEAT deltas == CONTROL (center repetition cannot reproduce ROUTE delta structure).

## Frozen secondary (exploratory)
Per center, seed-matched: is the ROUTE reconstruction output distinguishable from REPEAT beyond CONTROL?
(mechanical text/structure distance and/or a blind condition-withheld judge — reported, not decisive). **HBB-30
NDO/REC is NOT the primary.**

## Frozen verdict rule (post-run)
- **INVALID** if any of req 1,3,4,5 is violated, REPEAT deltas ≠ CONTROL, or a forbidden token / answer-aware
  center appears (anti-fake list).
- **TEXT EMPHASIS ONLY** if req 2 fails (ROUTE deltas == CONTROL for the eligible centers) — re-rooting inert.
- Given req 2 holds:
  - **STRUCTURAL ROUTING CONSTRUCT VALID** if the ROUTE output is distinguishable from REPEAT (routing
    propagates beyond emphasis).
  - **AMBIGUOUS** if ROUTE deltas differ but ROUTE output is not distinguishable from REPEAT.

## Frozen claim ceiling
positive ⇒ "compare-stage re-rooting produces a structured intermediate change not reproducible by matched text
repetition." **NOT:** HBB-30 solved · Attention-Center validated · selector validated · mobility solves
fixation · breakthrough reproduced · Aruism implemented · fixation mechanism proven. Applicability to arbitrary
external detected objects is OUT OF SCOPE. C≠H.

## Run order (gated)
freeze/hash (this doc) → **independent construct audit** (F1/C-*/SWEEP/P1/D1 + invariants + hash contract +
anti-fake) → **STOP + report** (no implementation, no run this round). Implementation + run separately gated.
