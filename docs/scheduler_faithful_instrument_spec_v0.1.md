# Faithful STOP–SHIFT–RUN–COMPARE scheduler — instrument spec v0.1

**Derived from** `docs/R4_construct_validity_audit.md` §8. **Purpose:** an instrument whose construct validity
for the Taka scheduling hypothesis is defensible (the thing R4 was not, DE-0128). **Claim ceiling:**
capability-exhibit only. **Target-blind, cognition-agnostic** (firewall:
`docs/next_branch/taka_breakthrough_hypothesis_v0.1_QUARANTINE.md`). Not Taka's mind — a *mechanism*.

## Hypothesis under test (mechanism, not cognition)
There exists a faithful STOP–SHIFT–RUN–COMPARE **scheduler** that produces consensus-REC2 reconstructions of a
hard-core incident above base R0. Faithful = it instantiates the active ingredients R4 lacked/inverted:
*short interrupted runs + independent reread of the same source + sampled viewpoint shift + partial
independence + structural signature extraction + comparison of signatures + rebuild-from-differences +
bounded convergence*, with **no cumulative pooling of views**.

## The scheduler RS (one candidate = one full run)
1. **SHORT INTERRUPTED VIEWS** — sample V distinct generic **lenses**; for each, produce a *deliberately
   incomplete, partial first impression* of **T0 only** (hard token cap + "give only your first rough partial
   read, then stop; do not resolve"). Views are generated **without seeing each other** (partial independence).
2. **SIGNATURE EXTRACTION** — for each view, a **separate** step reduces it to a structural signature
   `SUBJECT / LEVEL / KEY-DISTINCTION`. Reads the view **only** (not T0, not other views).
3. **COMPARE** — a step over the **signatures only** names the structural **differences** among the rough views
   (where they disagree on subject/level/distinction). No winner is picked; no view text is pooled.
4. **REBUILD** — a step synthesizes **one replacement frame from the differences** (+ the shared source T0 as
   anchor), changing subject/level/key-distinction, plus the next action. It does **not** read or restate any
   single view. The rebuilt frame is the scored candidate.
5. **CONVERGENCE (bounded)** — a CHECK grades whether the rebuild actually changed subject/level/distinction
   vs T0. If **HOLD** (no structural change), run **one** SHIFT-AGAIN pass with fresh lenses (HOLD-2 cap); else
   SELECT. Max 2 attempts. (SELECT / HOLD-2 / SHIFT-AGAIN / ESCALATE, versioned.)

**No cumulative pooling anywhere in RS** — this is the §5 inversion that must stay absent.

## Conditions (construct isolation)
- **R0** — base control (frozen exhibit base prompts). Reference for the capability-exhibit.
- **RS** — the full faithful scheduler above.
- **RS_pool** — INVERSION ablation: identical to RS **except** view *j* reads `T0 + all prior views 1..j-1`
  (cumulative pooling reintroduced, the R4 defect). Isolates *independence / non-accumulation*.
- **RS_flat** — COMPARE+REBUILD ablation: emit the V short independent views as the scored candidates directly
  (no signature/compare/rebuild). Isolates *compare + rebuild-from-differences*.

## Hypotheses & decision (preregistered)
Scoring identical to the frozen exhibit: rubric v2 (sha 012941ab), 2-axis DET/RECON, **blind to condition**,
consensus **REC2 = GPT RECON==2 ∧ Qwen RECON==2** (Claude excluded, author). Per (cond,inc,seed) *reached* =
≥1 candidate consensus-REC2; reach-rate over M; incident-reached = ≥⌈M/2⌉.
- **H_sched_exhibit (PRIMARY):** ∃ incident where RS reach > R0 by binomial (null p = R0 reach-rate),
  α=0.05, Bonferroni / 3 incidents, AND incident-reached.
- **H_independence (SECONDARY):** RS reach > RS_pool (per incident) — independence/non-accumulation active.
- **H_compare_rebuild (SECONDARY):** RS reach > RS_flat (per incident) — compare+rebuild active.

## Parameters (frozen at prereg)
incidents = {HBB-08, HBB-10, HBB-30}; M = 10 (genuinely stochastic — no seed-ignoring); N = 6 candidates/cell;
V = 3 views; lens pool = 8 generic structural lenses (target-blind); convergence cap = 2 (HOLD-2);
temperature = 0.9 (views/rebuild diversity), scorer temp 0 (frozen); budget = exhaustive completion;
no author selection (all N candidates scored). GPT external handoff (Qwen-REC2 subset), same as exhibit.

## Claim ceiling / firewall
Capability-exhibit only: "∃ a faithful scheduler mechanism producing consensus-REC2 reconstructions of a
hard-core incident above base." NOT generalization, NOT autonomy, NOT "this is Taka's cognition"
(→ quarantined v0.1). Transfer/autonomy → FUTURE-SEALED. Frozen prior artifacts (DE-0127) untouched.

## Acceptance gate (before any run)
Independent auditor grades construct-to-code elements 1–8 (see `scheduler_construct_binding.json`) as
**PRESENT** on the *code*, and confirms **no cumulative pooling in RS**. Only then may RS run. (This is the
gate R4 would have failed.)
