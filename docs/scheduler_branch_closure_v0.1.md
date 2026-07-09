# Faithful scheduler branch — FORMAL CLOSURE (v0.1)

**Result: NEGATIVE at the preregistered bar.** Instrument valid; all three preregistered hypotheses NOT
confirmed. Closed per the frozen prereg (seal 64c08b63). GPT-strict consensus integrated. DE-0127 untouched.
Five axes recorded **separately** (Taka step 4).

## Scoring closure (steps 1–2)
- GPT strict scoring integrated as the third scorer: condition-blind, opaque_id join, frozen rubric v2
  (sha 012941ab), **consensus REC2 = GPT-strict ∧ Qwen**. No normalization, no post-hoc threshold change.
- Provenance note: GPT returned a `SCHEDULER_GPT_STRICT_SCORE_AUDIT` summary (n=226, blind, per-incident
  distribution + explicit strict-REC2 id list). Two 1,422-item arrays were also pasted but are the
  **reconstruction-primary** ids (wrong experiment) — NOT used. Join verified: all 8 strict-REC2 ids ∈ the 226
  handoff; per-incident counts match exactly (HBB-08 91, HBB-10 134, HBB-30 1). Since every handoff candidate
  is already Qwen-REC2, consensus REC2 = the GPT-strict-REC2 set (authoritative from the audit).

## Consensus seed-reach (GPT-strict ∧ Qwen), M=10
| incident | R0 | RS | RS_pool | RS_flat |
|---|---|---|---|---|
| HBB-08 | 0 | **3** | 1 | 0 |
| HBB-10 | 2 | 1 | 0 | 0 |
| HBB-30 | 0 | 0 | 0 | 0 |

The 8 consensus-REC2 candidates → blind conditions: HBB-08 {RS s0, RS s5, RS s8, RS_pool s2};
HBB-10 {RS s1, R0 s3, R0 s4, R0 s4}.

## Hypothesis adjudication (step 2) — decision rule: RS reach > comparator by binomial (α=0.05, Bonf/3) AND incident-reached ≥⌈M/2⌉=5
- **H_sched_exhibit (RS>R0): NOT CONFIRMED.** HBB-08 RS 3/10 vs R0 0/10 (binom p→0, sig) but **incident-reached
  fails (3<5)**. HBB-10 RS 1/10 < R0 2/10. HBB-30 0/0.
- **H_independence (RS>RS_pool): NOT CONFIRMED.** HBB-08 RS 3 vs RS_pool 1 (p=0.070, not sig, not reached);
  HBB-10 RS 1 vs RS_pool 0.
- **H_compare_rebuild (RS>RS_flat): NOT CONFIRMED.** HBB-08 RS 3 vs RS_flat 0 (sig, not reached); HBB-10 RS 1
  vs RS_flat 0. **RS_flat = 0 on every incident.**

None crosses the incident-reached gate; RS peaks at 3/10. **Formal verdict for all three = NEGATIVE.**

## The five axes, separated (step 4)

### ① Instrument validity — PASS (this is a *real* negative, not an R4-style artifact)
Acceptance gate passed (independent audit: 8/8 constructs PRESENT, no-pooling invariant holds, target-blind).
Candidate diversity 6/6 all conditions (R4 determinism defect fixed); convergence active (SHIFT-AGAIN 21/180,
resolved ~99%); M=10 genuine stochastic replication. The instrument can measure the effect; it measured its
absence at the bar.

### ② Scheduler capability result — NEGATIVE at bar; NON-ZERO below it
RS did produce **GPT-strict∧Qwen-certified** reconstructions of a hard-core incident (HBB-08: 3/10 seeds; plus
HBB-10 1/10) — the capability is **non-zero at the seed level** — but it does **not** reach the preregistered
exhibit threshold (≥5/10). Contrast DE-0127 where the include-all mechanism (old R2) hit HBB-08 10/10 under
consensus: **the faithful scheduler underperformed that closed exhibit on HBB-08.**

### ③ Independence contribution — WEAK / directional only
RS (indep. reread) > RS_pool (cumulative pooling) directionally on HBB-08 (3 vs 1) and HBB-10 (1 vs 0), but
not significant/reached. Note RS_pool was **not zero** (HBB-08 s2 reached), so pooling did not fully destroy
the effect. No confirmed independence contribution.

### ④ Compare/rebuild contribution — STRONGEST directional signal (still below bar)
**RS_flat (views scored directly, no compare+rebuild) = 0 consensus-REC2 on ALL incidents**, while RS = 4
across incidents. Qualitatively, the compare→rebuild stage looks **necessary** for any consensus-REC2 here.
This diverges from the earlier Qwen-alone candidate-level hint (RS≈RS_pool>R0≈RS_flat): under GPT-strict, RS
exceeds **both** ablations directionally. Not a confirmed hypothesis (incident-reached gate), recorded as
directional evidence only.

### ⑤ HBB-30 exceptional candidate status — QWEN FALSE-POSITIVE
The single HBB-30 RS Qwen-REC2 candidate (`5d6cd81acc350e`, seed 5) is **GPT-strict REC0/DET0** → consensus
fails. Per Taka step 3, saved readable with text + execution trace in
`experiments/hbb30_rs_exceptional_candidate.json`, classified **Qwen false-positive** (NOT an RS-only
breakthrough candidate). GPT reason: "accepts the 6× premise and invents a combinatorial state-space
derivation; does not reframe to evidence status / DECLARED historical claim handling / SUPERSESSION." HBB-30
remains unreconstructed under consensus by every condition.

## Claim ceiling / firewall (unchanged)
Capability-exhibit of a mechanism only; **not** confirmed here. No generalization, no autonomy, no
"this is Taka's cognition" (v0.1 quarantined). Transfer/autonomy → FUTURE-SEALED. DE-0127 not revised.

## Status: faithful scheduler branch CLOSED (negative). Ledger DE-0130.
