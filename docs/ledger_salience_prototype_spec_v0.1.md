# Ledger-salience minimum temporal prototype — spec v0.1

**One question only:** does the append-ordered categorical stream of `DESIGN_EVIDENCE_LEDGER.jsonl`, under
frozen ESDE-derived salience primitives applied **target-blind**, contain temporal salience structure that a
**count-preserving order-shuffle null** does not explain?

**This is NOT SHAKE detection.** No category is labelled good/bad/anomalous; no known-incident position is
passed to any generator/detector; no past-breakthrough cause is inferred (C≠H). Adapter = **A (LEDGER CATEGORY
STREAM)** only (B/C held: B n≈3–5 insufficient, C frame-manifest absent).

## Scope
- **Data**: `DESIGN_EVIDENCE_LEDGER.jsonl`, append order preserved. Primary stream = `evidence_class` (verbatim);
  secondary = `decision`-head (first token, reported-only). Normalization = mechanical only
  (`ledger_stream_contract_v0.1.json`).
- **Representations**: R1 run-length · R2 recurrence-interval · R3 window-distribution(entropy, W=10 fixed).
- **Primitives (ESDE math unchanged)**: A causal past-only EWMA-z · B two-sided rarity (both tails) ·
  C persistence-run (robust) · D distribution reporting (no argmax).
- **Null**: count-preserving order-shuffle (destroys ordinal order, preserves the multiset). N_NULL=2000,
  SEED=20260710 frozen. **No additional null** (adding one post-hoc is forbidden).
- **Decision**: `H_salience_structure` at a preregistered Bonferroni threshold (see prereg).
- **Claim ceiling**: positive ⇒ only "ledger stream contains non-random temporal salience structure detectable
  by reused ESDE primitives." negative ⇒ "A-adapter / current ledger stream did not detect useful temporal
  salience structure." **Never**: SHAKE detected / incidents recovered / breakthrough predicted / Aruism
  trigger / regime solved / ESDE transferred / autonomy improved.

## Deliverable set
spec(this) · contract(`ledger_stream_contract_v0.1.json`) · binding(`ledger_salience_construct_binding_v0.1.json`)
· prereg(`ledger_salience_prereg_v0.1.md`) · seal(`ledger_salience_prereg_seal.json`) ·
power-audit(`ledger_salience_power_audit_v0.1.json`) · impl(`run_ledger_salience.py`) · then independent
construct audit → gated real+null run → result → decision report → DE ledger entry proposal.

## Power reality (from pre-audit — load-bearing)
N=130, vocab=36, **only 7 categories have count≥3** (OPERATIONAL 41% dominant), 22 singletons, rare-share 0.277.
Run/recurrence power lives on those 7; singletons are **NO POWER**, not "normal." A zero must be reported with
its power (v1304c M-power lesson). This caps interpretability regardless of outcome.
