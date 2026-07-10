# PREREG — Route-vs-repeat construct validation v0.2 (to be FROZEN/HASHED)

Supersedes **v0.1 (construct-audit REJECTED)**. Freezes spec `route_vs_repeat_spec_v0.2.md`, binding
`route_vs_repeat_construct_binding_v0.2.json`, hash contract `route_vs_repeat_hash_contract_v0.2.json`. CONSTRUCT
VALIDATION of compare-stage re-rooting. **Not solving HBB-30.** Target-blind (center ∈ existing signature pool,
all-sweep); C≠H.

## Why v0.2 (what the audit forced)
v0.1's primary (delta-set hash divergence) was near-tautological — a compare prompt swap trivially changes the
text; the mechanical hash shows "different text", not "structure", and req6 was true by construction. The real
routing-vs-emphasis discrimination lived entirely in an **un-preregistered secondary**, and there was **no
compare-stage emphasis control**. v0.2: (1) delta divergence demoted to a mechanical **GATE**; (2) the **output
test elevated to a preregistered co-primary (PRIMARY-B)**; (3) a **fourth arm EMPHASIS-COMPARE** added so a
ROUTE effect isolates topology re-rooting from mere compare-stage repetition; (4) **determinism self-check**
made load-bearing; (5) SYS_CMP_ROOTED + EMPHASIS-COMPARE prompts instantiated and hashed.

## Frozen construct question
Does re-rooting COMPARE on a selected center signature (delta origin = that signature) produce a reconstruction
change **not reproducible by matched text repetition at compare (EMPHASIS-COMPARE) or at rebuild (REPEAT)**?

## Frozen design (4 arms)
- Machinery = scheduler pipeline (view→signature→compare→rebuild), logic unchanged.
- **Fixed signature pool**: V=6 signatures generated once on HBB-30 `t0_stuck_frame` (frozen lens set + seed),
  persisted, reused by all 4 arms.
- **CONTROL** compare all-pairs (temp=0, seed s0) → `deltas_ctrl` → rebuild.
- **REPEAT-REBUILD** reuse `deltas_ctrl` verbatim → rebuild(`deltas_ctrl`, fr, `repeat_text=sigs[i]`).
- **EMPHASIS-COMPARE** compare all-pairs, SYS_CMP UNCHANGED, `sigs[i]` repeated in the compare INPUT (temp=0,
  seed s0) → `deltas_emph_i` → rebuild. [compare-stage repetition, NO re-root]
- **ROUTE** compare(`sigs`, `center_ref=i`, SYS_CMP_ROOTED star-from-reference, temp=0, seed s0) →
  `deltas_route_i` → rebuild. [re-root at compare, before rebuild assembly]
- **ALL-SIGNATURE SWEEP** over i ∈ [0,V); attempts + seed-scheme matched across all 4 arms.
- Compare temp=0, concurrency=1, greedy (deterministic delta hashing); rebuild temp=0.8, M=5 seeds/(arm,center).
- SYS_CMP_ROOTED = topology change (all-pairs → star-from-reference), marks one signature REFERENCE; EMPHASIS-
  COMPARE = SYS_CMP unchanged, `sigs[i]` repeated in input; **neither** contains
  focus/central/reframe/premise/provenance/challenge/question **nor** HBB-30 answer vocabulary.

## Frozen PRIMARY-A — DELTA_SET DIVERGENCE (mechanical GATE, necessary not sufficient)
1. `hash(REPEAT deltas) == hash(CONTROL deltas)` (definitional).
2. `hash(ROUTE deltas_i) != hash(CONTROL deltas)` for eligible nontrivial centers (report the fraction).
3. signature-pool multiset hash identical across all 4 arms.
4. source/system/decoding hash identical across all 4 arms.
5. ROUTE change is at compare (center_ref set, rebuild repeat_text absent).
6. REPEAT deltas == CONTROL (rebuild-stage repetition cannot reproduce ROUTE delta structure).
(EMPHASIS-COMPARE deltas MAY differ from CONTROL — expected; it is the compare-repetition control.)

## Frozen PRIMARY-B — ROUTE_OUTPUT_BEYOND_COMPARE_EMPHASIS (decisive)
- **Metric (mechanical, no LLM judgment):** per (center i, rebuild seed m), content-word Jaccard distance
  `d_route = jaccard_dist(cw(ROUTE_i_m), cw(EMPH_i_m))`, `d_emph = jaccard_dist(cw(EMPH_i_m), cw(CONTROL_m))`,
  where `cw` = lowercased alphanumeric tokens minus a frozen English stoplist (stoplist committed with the impl).
- **Test:** paired one-sided sign test H1 `d_route > d_emph` over all (i,m), α = 0.05.
- **Power:** V=6 centers × M=5 seeds = 30 paired points (report exact binomial power; underpowered → AMBIGUOUS,
  never silently "null").
- **Confirmation (non-decisive):** blind, condition-withheld Qwen judge scores structural-subject difference
  0/1/2 for (ROUTE_i,EMPH_i) and (EMPH_i,CONTROL); **Claude excluded**; reported only.

## Frozen determinism self-check (load-bearing, pre-run)
Compare temp=0, concurrency=1, greedy, seed s0. Before the measured run: CONTROL compare **twice** + one ROUTE
center **twice**; **assert byte-identical delta hashes**. Any mismatch ⇒ **abort, verdict INVALID (determinism
failure)** — the delta-hash gates are meaningless without it.

## Frozen verdict rule (post-run)
- **INVALID** if any gate (req 1,3,4,5,6) fails, the determinism self-check fails, or a forbidden token /
  answer-aware center appears (anti-fake list).
- **TEXT EMPHASIS ONLY** if gates pass (incl. req 2) but **PRIMARY-B fails** (`d_route` not > `d_emph`): ROUTE
  output not distinguishable from compare-stage emphasis → re-rooting adds nothing beyond naming/repetition.
- **STRUCTURAL ROUTING CONSTRUCT VALID** if req 1–6 hold AND **PRIMARY-B passes**.
- **AMBIGUOUS** if gates pass but PRIMARY-B is underpowered / mixed / inconclusive.

## Frozen claim ceiling
positive ⇒ "compare-stage re-rooting produces a reconstruction change not reproducible by matched compare- or
rebuild-stage repetition." **NOT:** HBB-30 solved · Attention-Center validated · selector validated · mobility
solves fixation · breakthrough reproduced · Aruism implemented · fixation mechanism proven. Arbitrary external
detected-object injection is OUT OF SCOPE. C≠H.

## Run order (gated)
freeze/hash (this doc) → **independent construct audit** (F1/C-*/SWEEP/P1/PB/D1 + invariants + hash contract +
anti-fake + PRIMARY-B preregistration + determinism self-check) → **STOP + report** (no implementation, no run
this round). Implementation + run separately gated on audit PASS + user go.
