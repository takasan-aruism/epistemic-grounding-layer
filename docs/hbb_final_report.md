# HBB Final Report — N=13 two-axis MULTI_SCORER_CONSENSUS (closure, DE-0115)

**status: HBB branch = CLOSED candidate (Taka の最終 CLOSE 判定待ち)**
Supersedes the single-axis verdict in `hbb_sealed_report.md` §A–§I for reach/complementarity claims.
Instrument: `DETECTION_RECONSTRUCTION_SPLIT` (primary) × `MULTI_SCORER_CONSENSUS`.
Machine record: `experiments/hbb_n13_consensus.json`. Hard-core: `experiments/hbb_hard_core_fixed.json`.

## Setup
- **N=13** SEALED (added HBB-04 AA / HBB-30 FOS; 40 new cells run on local Qwen, original 220 byte-identical).
- **Two independent 2-axis scorers**: GPT rubric-v2 (strict) + Qwen rubric-v2 (lenient), both on the frozen
  rubric (sha256 `012941ab…`, verified). **Consensus reach = both scorers agree** (best-across-rungs).
- **Claude** authored arms C/D → **not a scorer**. HBB-04/30 scored by {Qwen, GPT} only (当事者 excluded).
- AA (7): HBB-01,03,04,05,08,10,11 · FOS (6): HBB-06,12,13,17,24,30.

## Consensus reach (both scorers, best-across-rungs)
| axis | A | B | C | D | F |
|---|---:|---:|---:|---:|---:|
| **RECONSTRUCTION=2** ALL | 3 | 4 | 4 | 4 | 0 |
| REC2 AA | 1 | 2 | 1 | 2 | 0 |
| REC2 FOS | 2 | 2 | 3 | 2 | 0 |
| **DETECTION=2** ALL | 6 | **9** | 7 | 7 | 0 |

REC2 incident sets: A `{04,06,13}` · B `{03,11,12,17}` · C `{05,12,17,24}` · D `{01,05,12,24}` · F `{}`.

## Verdict 1 — REVERSAL of the single-axis DE-0112/0114 result
Under the **promoted 2-axis instrument**, on AA:
- **C-unique_AA = {HBB-05}**, **D-unique_AA = {HBB-01, HBB-05}** — i.e. the engines uniquely *reconstruct*
  specific AA breakthroughs that skepticism (B) only *detects* (HBB-05 metric-individuation by C; HBB-01
  definition→prediction + HBB-05 by D).
- **B∪C_AA = {03,11,05} = 3 > max(|B_AA|,|C_AA|) = 2**, and C-unique_AA ≥ 1 →
  **H_primary WEAKLY CONFIRMED** (margin = 1 incident, HBB-05).
- This **supersedes** DE-0112/0114's "C-unique = D-unique = 0 / H_primary NOT_CONFIRMED": that was computed on
  the **single-axis reach instrument which DE-0114 itself demoted from load-bearing**. On the reconstruction
  axis, the engines add unique reach. *The demotion was the right call; this is what it revealed.*

## Verdict 2 — but the engine advantage is HINT-ASSISTED, not autonomous
- All engine AA-unique reconstructions occur at **H1** (min_hint_depth 3, the weak "hidden-premise" hint) —
  **none at H0-free**.
- The **only** AA reconstruction at **H0-autonomous** consensus is **base arm A on HBB-04** (neither an engine
  nor skepticism).
- So: engines add unique AA reconstruction **reach with a hint**; **autonomous (H0) AA reconstruction remains
  essentially unmet** across all arms (a single base-arm data point). Do not over-read Verdict 1 as autonomous
  engine capability.

## Verdict 3 — B detection→reconstruction gap (robust, both scorers)
**B consensus DETECTION=2 = 9/13 (most of any arm); consensus RECONSTRUCTION=2 = 4/13.** Skepticism is the
strongest **detection gate** but does not complete reconstruction. This confirms the DE-0114 SUPPORTED claim,
now robust across both 2-axis scorers.

## Verdict 4 — robust hard-core FIXED (ground truth for the scheduler prereg)
**Hard-core = {HBB-08, HBB-10, HBB-30}** — no arm reaches consensus RECONSTRUCTION=2; all three are
**detected-but-not-reconstructed** (none fully-missed). Fixed **before** any scheduler design so it cannot
overfit the scheduler (DE-0111-type accident). This is the R1–R4 / STOP-SHIFT-RUN-COMPARE target set
(`hbb_hard_core_fixed.json`).

## Caveats (over-claim brakes)
1. Consensus is **GPT-bound**: GPT (strict) is the binding scorer; Qwen (lenient) concurs.
2. RECONSTRUCTION targets: the 11 = **GPT-formalized** target_map (deviation_log #3); 04/30 =
   Taka-adjudicated breakthrough_structure. The original breakthrough_structures were **Claude-authored**
   (builder contamination).
3. H_primary confirmation **margin = 1** (HBB-05) — fragile.
4. **HBB-03** (return-to-substrate) is **not** in the hard-core because B reaches consensus REC2 on it
   (hint-assisted, H2). This is in tension with GPT report §3 prose calling HBB-03 the deepest hard case:
   both hold — B reconstructs HBB-03 only *with* hints, not at H0.
5. best-across-rungs reach includes hint-assisted reaches; the H0-autonomy picture is reported separately
   (Verdict 2).

## Scope held OUT of closure (post-closure track)
Per Taka: **GPT/Claude raw-API cross-model arm** and **independent cross-review** are NOT closure conditions —
they measure deployment significance (Qwen+engine vs commercial models), a different layer from engine
efficacy. Held as a post-closure deployment / external-validation track (NBC gate).

## Next (gated, not started)
hard-core fixed → **NBC-1 R1–R4 prereg** (R1 Detection→Reconstructor / R2 Independent Frame Generator /
R3 Detection+T0 / R4 STOP-SHIFT-RUN-COMPARE) on {HBB-08,10,30}. **Order is load-bearing**; scheduler
implementation awaits Taka's go. Autonomous RD not enabled. No self-improvement claim.
