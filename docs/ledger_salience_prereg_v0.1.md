# PREREG — Ledger-salience temporal prototype v0.1 (to be FROZEN/HASHED)

Freezes the single-question prototype (spec `ledger_salience_prototype_spec_v0.1.md`, contract
`ledger_stream_contract_v0.1.json`, binding `ledger_salience_construct_binding_v0.1.json`, impl
`run_ledger_salience.py`). Target-blind; no SHAKE label; C≠H.

## Frozen hypothesis
**H_salience_structure**: the append-ordered `evidence_class` stream contains temporal salience structure,
under the frozen ESDE-derived primitives, that **exceeds count-preserving order-shuffle null behavior**.

## Frozen primary decision
- Primary stream = `evidence_class` (decision on this only; `decision`-head reported-only).
- Primary metrics (pre-fixed, no additions): `max_run`, `n_runs_ge3` (runs ≥ L0=3), `uppertail_run_mass`
  (top-decile run lengths), `max_causal_entropy_z` (max |past-only EWMA-z| of window-entropy).
- Null = count-preserving order-shuffle; N_NULL=2000; SEED=20260710. One-sided empirical p per metric =
  (1 + #{null ≥ real}) / (1 + N_NULL).
- **α=0.05, Bonferroni / 4 metrics ⇒ α_corr=0.0125.**
- **H_salience_structure CONFIRMED iff ≥1 primary metric has p < 0.0125 AND the power gate passes**
  (power gate = ≥5 categories with count≥3; observed = 7, so the gate is met a priori).
- **Anti-triviality (per the warning that shuffle inflates runs by construction):** the count-preserving null
  IS the guard — exceeding it means run/entropy structure beyond the multiset alone. All 4 metrics are reported;
  a positive driven only by `max_run` is reported transparently as such and does NOT license a distributional
  claim; the distributional metrics (`n_runs_ge3`, `uppertail_run_mass`) and the orthogonal
  `max_causal_entropy_z` are reported alongside so a single-metric positive cannot masquerade as structure.

## Frozen measurement audit (secondary, NOT in the decision)
- **premise-drift**: window category-mix entropy trend across the sequence (reported).
- **two-sided rarity** of recurrence intervals (both tails) for the 7 powered categories (reported).
- **detection-power / censoring** (`ledger_salience_power_audit_v0.1.json`): N=130, vocab=36, cats_ge3=7,
  singletons=22, rare-share 0.277, dominant OPERATIONAL 0.408; causal-z silent first WARMUP=10; recurrence
  right-censored on each category's last occurrence. **signal=0 vs no-power** distinguished per primitive:
  count<2 ⇒ NO POWER (run/recurrence); first 10 window-points ⇒ NO POWER (z=0). A null result is only
  interpretable next to this table.

## Frozen claim ceiling
- positive ⇒ "the ordered ledger stream contains **non-random temporal salience structure detectable by reused
  ESDE primitives**." Nothing more.
- negative ⇒ "the A-adapter / current ledger-stream combination **did not detect useful temporal salience
  structure**."
- **NOT claimed under any outcome**: SHAKE detected · historical incidents recovered · Taka breakthrough
  predicted · Aruism trigger discovered · operational regime solved · ESDE attention transferred · autonomy
  improved.

## Run order (gated)
freeze/hash (this doc) → **independent construct audit** (representations/primitives PRESENT + invariants:
no-category-value, causal-no-future-leak, null-count-preserving, target-blind, metrics-pre-fixed) → only then
the real+null run → result → decision report → DE ledger entry proposal. PROCESS-01: log wall/primitive-calls/
n_null.
