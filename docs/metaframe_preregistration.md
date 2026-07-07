# Meta-Frame Factory — Preregistration (outcome-neutral, fixed before results)

Spec: 2DER Meta-Frame Formation & Lifecycle v0.3. Date 2026-07-07. Written BEFORE any extraction/induction/
transfer outcomes are observed (§25.1). This document fixes the interpretation of every outcome in advance.

## Core question (§3/§34)
Can 2DER derive a reusable frame-changing operation from multiple historical incidents **without being given
Taka's lesson statement as the answer**, and does the induced meta-frame recover a decision-relevant missing
axis on a held-out incident **more specifically/reliably than** ordinary Qwen, generic skepticism, explicit
human lesson memory, and verified-incident retrieval?

## Conditions (held-out transfer, §24/§25)
- **CONTROL A** — ordinary Qwen3.6 (no frame material)
- **CONTROL B** — generic skepticism prompt ("be skeptical, consider hidden assumptions")
- **CONTROL C** — explicit human lesson memory (Taka's 教訓 sentences)
- **CONTROL D** — verified-incident retrieval only (top-3 VERIFIED INCIDENT_FRAME, no induced meta-frame) **[required]**
- **TREATMENT** — EGL-current induced meta-frame

## Preregistered outcome interpretation (§25.1) — all outcomes informative
| observed | interpretation |
|---|---|
| TREATMENT > A/B/C/D | provisional evidence induction adds value |
| CONTROL D ≈ TREATMENT | case retrieval may be sufficient; induction may not justify complexity (MF-R15) |
| CONTROL C > TREATMENT | explicit human lessons may outperform induced abstraction |
| CONTROL B ≈ TREATMENT | likely prompt-engineering / generic-skepticism effect (MF-R4) |
| all conditions weak | incident/frame representation or held-out task inadequate |

**This is a pilot (N≈5 held-out).** A positive result is at most PROVISIONAL transfer evidence unless the
effect is exceptionally large AND later replicated. No CURRENT status from this pilot (§26, §20.1).
Default meta-frame status after the walking slice = **PROVISIONAL**.

## Primary metrics (§15/§24, no composite score)
missing-axis recovery (did the condition recover the historical human-added frame delta?), new-useful-axis,
irrelevant-axis count, decision-path changed, over-trigger/needless-skepticism, H3 intervention required.
Kept as raw dimensions — **no "answer trust score"** (§19 of AEC discipline reused).

## Integrity controls (declared before running)
- **Gold sealing** (§12.1): Claude builds 6–10 gold incident annotations, SHA-256 sealed + timestamped
  BEFORE the extraction prompt is frozen; gold hidden from the Qwen extractor/inducer; unsealed only for eval.
- **External-weight audit** (§14/§19): Phase-A audit and meta-frame audit use Claude (external weight vs Qwen),
  not a different seed of the same Qwen weights, as the load-bearing verifier. Grounded in measured evidence
  that same-weight Qwen audit was insufficient here (7 findings / 0 accepted / 0-of-2 real-defect recall).
- **Held-out leakage control** (§6 MF-R7A): held-out pre-frames built from spans that chronologically precede
  the intervention (Method B truncation), recording cutoff_span / source_hash / builder / later-spans-unavailable.
- **Blindness passes** (§6): extraction ≠ frame-delta ≠ induction; inducer gets only VERIFIED frame-deltas,
  no lesson headings / 教訓 sentences / family labels; one topic-masked induction view.
- **Origin separation** (§5): HUMAN_LESSON / CORPUS_EXTRACTION / DERIVED_FROM_INCIDENT /
  INDUCED_FROM_INCIDENT_CLUSTER kept distinct; human-origin laundering (MF-R6) is a defect.
- **Corpus tier + fidelity** (§9.1, MF-R7B): TIER_1 retrospective incidents record
  pre_frame_fidelity=RETROSPECTIVE_RECONSTRUCTION; a bounded TIER_2 primitive subset (recent 2DER operational
  incidents with primitive pre-intervention records: axis over-flag, RDA fail-open, Sleep Mode, sealed GPU
  preference) tests survival outside retrospective narrative.

## Declared limitation (§12.2, no laundering behind "independent")
Gold builder = Claude; pipeline implementation = Claude Code; extractor/inducer = Qwen3.6. Gold-builder vs
pipeline-implementer separation is **imperfect** (both Claude-family). Recorded as an experiment limitation,
not hidden behind the word "independent". GPT cross-review is preferred where available.

## Walking-slice targets (§27)
20–30 VERIFIED INCIDENT_FRAME, 20–30 VERIFIED FRAME_DELTA, 2 clustering views, ≤3 META_FRAME_CANDIDATE,
≥5 held-out incidents, CONTROL A/B/C/D + TREATMENT, bounded TIER_2 subset. A narrow positive needs ONE
strong meta-frame (≥3 materially-different verified incidents, not copied from lesson text, structurally
audited, held-out missing-axis recovery beating ordinary + generic-skepticism controls).

## Non-claims (§3/§24)
One positive does NOT establish meta-learning, self-evolution, or general metacognition. The result is scoped
to the tested corpus, incidents, and held-out task.
