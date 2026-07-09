# PREREG — Faithful scheduler capability-exhibit v0.1 (FROZEN)

Freezes `docs/scheduler_faithful_instrument_spec_v0.1.md` + `experiments/scheduler_construct_binding.json` as
the preregistered instrument. Distinct from and does not revise the closed reconstruction exhibit (DE-0127).
Target-blind, cognition-agnostic (firewall: `docs/next_branch/taka_breakthrough_hypothesis_v0.1_QUARANTINE.md`).

## Frozen hypotheses
- **H_sched_exhibit (PRIMARY):** ∃ hard-core incident where **RS** consensus-REC2 seed-reach exceeds **R0** by
  binomial (null p = R0 reach-rate), α=0.05, Bonferroni / 3 incidents, AND incident-reached (≥⌈M/2⌉).
- **H_independence (SECONDARY):** RS reach > **RS_pool** (independence / non-accumulation active).
- **H_compare_rebuild (SECONDARY):** RS reach > **RS_flat** (compare + rebuild-from-differences active).

## Frozen conditions
R0 (base control) · RS (constructs 1–8 PRESENT) · RS_pool (independence INVERTED = cumulative view pooling) ·
RS_flat (compare+rebuild ABSENT = independent short views scored directly).

## Frozen parameters
incidents = {HBB-08, HBB-10, HBB-30}; M = 10 (genuinely stochastic; seed drives every stage); N = 6
candidates/cell; V = 3 views; lens pool = 8 generic target-blind structural lenses; convergence cap = 2
(SELECT / HOLD-2 / SHIFT-AGAIN); temperature = 0.9 (generation), scorer temp 0; no author selection (all N
scored); budget = exhaustive completion.

## Frozen scoring
rubric v2 (sha256 012941aba485f33b8328b7e5cba2a84b5c1db82119bb96554bc8dea84f4f9f17), 2-axis DET/RECON, blind to
condition, Qwen local + GPT external handoff (Qwen-REC2 subset), consensus REC2 = GPT ∧ Qwen, Claude excluded.
opaque_id = sha256(incident|condition|seed|cand_idx)[:14].

## Frozen claim ceiling
Capability-exhibit of a MECHANISM only. NOT generalization, NOT autonomy, NOT "this is Taka's cognition"
(→ quarantined v0.1). Transfer/autonomy → FUTURE-SEALED.

## Acceptance gate (must pass before RS runs)
Independent auditor grades binding constructs 1–8 PRESENT on `run_scheduler_exhibit.py` and confirms the
`no_pooling_invariant` (no cumulative view pooling in RS / RS_flat; pooling only in RS_pool). This is the gate
R4 failed (DE-0128).

## Run order
freeze/hash (this doc) → implementation audit (acceptance gate) → generate (parallelized) → Qwen score →
GPT handoff (external, Taka) → consensus.
