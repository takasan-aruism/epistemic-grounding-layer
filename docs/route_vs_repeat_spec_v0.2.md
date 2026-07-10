# Route-vs-repeat construct validation — spec v0.2 (supersedes v0.1)

**v0.1 was construct-audit-REJECTED**: its primary (delta-set hash divergence) is near-tautological (a compare
prompt swap trivially changes the text), and req6 was true by construction — so the real "routing vs emphasis"
verdict rested entirely on an un-preregistered secondary. v0.2 fixes this per the audit: (1) the output test is
elevated to a **preregistered co-primary**, and (2) a **compare-stage emphasis control arm** is added so a ROUTE
effect isolates topology re-rooting from mere emphasis-at-compare. All original constraints retained.

**Construct question (NOT solving HBB-30):** does re-rooting the COMPARE stage on a selected center signature
(delta origin = that signature) produce a change **not reproducible by matched text repetition/emphasis** — at
compare **or** at rebuild?

## Machinery (reused, logic unchanged)
Scheduler pipeline `view_call → signature_call → compare_call → rebuild_call`. A **fixed signature pool**
(V=6 signatures generated once on HBB-30 `t0_stuck_frame`, frozen lenses+seed, persisted) is reused by every
arm. Compare runs **deterministically** (temp=0, concurrency=1, fixed seed) — with a determinism self-check
(§Determinism) because delta hashing depends on it.

## Four arms (only the emphasis/rooting differs)
| arm | compare | rebuild | what it isolates |
|---|---|---|---|
| **CONTROL** | `SYS_CMP` all-pairs | `rebuild(deltas_ctrl)` | baseline |
| **REPEAT-REBUILD** | *reuses* `deltas_ctrl` | `rebuild(deltas_ctrl, repeat_text=sigs[i])` | emphasis at **rebuild** (deltas byte-identical to CONTROL) |
| **EMPHASIS-COMPARE** | `SYS_CMP` all-pairs, input has `sigs[i]` **repeated** (topology unchanged) | `rebuild(deltas_emph_i)` | emphasis at **compare**, NO re-root |
| **ROUTE** | `SYS_CMP_ROOTED` star-from-reference `sigs[i]` | `rebuild(deltas_route_i)` | **re-root** at compare |

**Load-bearing contrast = ROUTE vs EMPHASIS-COMPARE** (re-root vs repeat, both at compare). REPEAT-REBUILD is the
rebuild-stage repetition control.

## Center selection (target-blind)
Center ∈ the existing signature pool only; **ALL-SIGNATURE SWEEP** (each signature is `center_ref`/`repeat`
once). No human pick, no answer-aware selection, no external-object injection, no HBB-30 correct-object use.
Degenerate/duplicate signatures excluded from the eligible tally (reported).

## Primary-A — DELTA_SET DIVERGENCE (mechanical GATE, necessary-not-sufficient)
Renamed from "STRUCTURAL" (a hash evidences *different text*, not structure). Requirements (gates):
1. `hash(REPEAT-REBUILD deltas) == hash(CONTROL deltas)` (definitional).
2. `hash(ROUTE deltas_i) != hash(CONTROL deltas)` for eligible centers.
3. signature-pool multiset hash identical across all arms.
4. source/task/policy/model/decoding hash identical across all arms.
5. ROUTE change occurs **before** rebuild prompt assembly.
6. REPEAT-REBUILD deltas == CONTROL (repetition-at-rebuild cannot reproduce ROUTE deltas).
These are **gates**, not the verdict.

## Primary-B — ROUTE_OUTPUT_BEYOND_COMPARE_EMPHASIS (the decisive co-primary, preregistered)
Does the ROUTE **reconstruction output** differ from the emphasis arms **more than the emphasis arms differ
from CONTROL**? Preregistered:
- **Metric (mechanical, no LLM judgment):** per (center i, rebuild seed), content-word Jaccard *distance* d(·,·)
  between reconstruction outputs. Compute `d_route = d(ROUTE_i, EMPHASIS-COMPARE_i)` and
  `d_emph = d(EMPHASIS-COMPARE_i, CONTROL)`.
- **Test:** paired one-sided sign test of `d_route > d_emph` over all (i, seed), α=0.05.
- **Confirmation (secondary):** a blind, condition-withheld judge (Qwen; Claude excluded) scores structural-
  subject difference 0/1/2 for ROUTE-vs-EMPHASIS-COMPARE and EMPHASIS-COMPARE-vs-CONTROL; report, not decisive.
- Rebuild temp=0.8, M=5 seeds/(arm,center), opportunity-matched across arms.

## Determinism self-check (load-bearing)
Compare forced temp=0, concurrency=1, greedy, fixed seed. Before the run: run CONTROL compare **twice** and one
ROUTE center **twice**; **assert identical hashes**. If not reproducible, the whole primary-A is vacuous → the
run aborts and reports INVALID (determinism failure).

## Frozen verdict rule (post-run)
- **INVALID** if any gate (req 1,3,4,5,6) fails, or the determinism self-check fails, or a forbidden token /
  answer-aware center appears.
- **TEXT EMPHASIS ONLY** if req 2 holds but **Primary-B fails** (`d_route` not > `d_emph`): ROUTE output is not
  distinguishable from compare-stage emphasis → re-rooting adds nothing beyond naming.
- **STRUCTURAL ROUTING CONSTRUCT VALID** if req 1–6 hold AND Primary-B passes (ROUTE output distinguishable
  from EMPHASIS-COMPARE beyond CONTROL).
- **AMBIGUOUS** if req 2 holds, gates pass, but Primary-B is inconclusive (underpowered / mixed).

## Anti-fake-center invalidators
center label only / center text moved to front / center re-quoted / only rebuild prompt changed (= REPEAT, not
ROUTE) / task-evidence policy changed / ROUTE deltas == CONTROL / **ROUTE output reproduced by EMPHASIS-COMPARE**.

## Claim ceiling
positive ⇒ "compare-stage re-rooting produces a reconstruction change not reproducible by matched compare- or
rebuild-stage repetition." **NOT:** HBB-30 solved · Attention-Center validated · selector validated · mobility
solves fixation · breakthrough reproduced · Aruism implemented · fixation mechanism proven. Arbitrary external
detected-object injection is OUT OF SCOPE. C≠H.
