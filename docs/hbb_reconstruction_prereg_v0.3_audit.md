# Load-bearing audit — HBB Reconstruction Prereg v0.3 draft

**audited: 2026-07-08T19:13:06Z. verdict: `BLOCKED — NOT run-ready`.**
Method: **independent adversarial auditor** (general-purpose subagent, no stake in the design) performed the
primary audit; **author-side (Claude Code) verified each finding against the prereg text** — all 11 hold.
This is the author≠auditor discipline (same shape that caught the Formal-compiler laundering, DE-0111).
Target: `docs/hbb_reconstruction_prereg_v0.3_draft.md`. No implementation. Awaiting Taka.

## Headline
**4 of 5 hypotheses are unsupportable as written**: H_recon (S1+S2+S3+S4+S5), H_scheduler (S7+S9), H_structure (S6).
The `⟨TC⟩` flags in the draft cover the **plumbing** (undefined params); they do **not** cover these **validity
holes**, several of which the draft presents as *sound*. Most dangerous: **S1** (no in-experiment baseline →
primary claim is cross-harness, unattributable) and **S2** (anti-overfit guarantee asserted but not delivered —
the routing layer is author-defined by the party who also authored the held-out targets).

## Findings (ranked; all VERIFIED by author-side against the draft)

| ID | sev | load-bearing element | defect (one line) | undermines | class |
|---|---|---|---|---|---|
| **S1** | CRITICAL | in-experiment attribution (§0,§7) | R3 is a scheduler control, **not** an in-harness replication of HBB's "no arm reached"; a positive is attributable to harness/prompt/budget drift, not the reconstruction stage | H_recon | **(b) unflagged** |
| **S2** | CRITICAL | anti-overfit guarantee (§4.2,§4.3,§10) | "frozen refs ⇒ no incident-tuned operators" is **false** while the STRUCTURAL PROJECTION selector (the T0→operator routing) is free, author-defined, and the author knows the 3 targets; fixing hard-core-before-scheduler stops tuning targets-to-scheduler, **not routing-to-targets** | H_recon | **(b) false guarantee** |
| **S3** | CRITICAL | MULTI_SCORER_CONSENSUS (§5) | consensus = GPT∧Qwen, but source docs say consensus is **"GPT-bound"** (strict ⊂ lenient) ⇒ for a REC2 positive, consensus **= GPT alone**; reintroduces the single-scorer variance instrument_2 was created to control; caveat **dropped** from the prereg | H_recon robustness | **(b) unflagged** |
| **S4** | HIGH | "H0-autonomous" definition (§0,§7,§8) | detection stage hands the reconstructor the **defect locus** (R1/R3/R4) = functionally the H1 "hidden-premise" hint that HBB Verdict 2 already showed engines need; a REC2 could be H1-assisted **re-badged autonomous**. Only **R2** is detection-free | H_recon | **(b) unflagged** |
| **S5** | HIGH | primary success bar (§7,§8,§9) | "≥1 incident REC2" = max over ~45 stochastic cells (3 inc × 3 cond × 5 seed) with bar at 1; no seed-aggregation rule, no floor/null, no multiplicity control ⇒ one lucky seed "confirms" | H_recon (false-pos) | **(b) unflagged** |
| **S6** | HIGH | R5 lossy transform (§4.4,§7) | mask strips exactly the content a reconstructor needs ⇒ **R5≪R4 by construction**, non-diagnostic; the informative branch (R5≈R4) is a priori unlikely ⇒ H_structure unfalsifiable in its informative direction | H_structure | **(b) confound** |
| **S7** | MED-HIGH | matched-budget test (§6) | equal budget ⇒ R4 = N shallow passes vs R3 = 1 deep pass; `R4>R3` conflates the scheduler with generic **best-of-N-at-fixed-budget** (and R2 is already best-of-N) | H_scheduler | **(b) unflagged** |
| **S8** | MED | convergence/STOP/SHIFT rule (§4.1,§11) | flagged `⟨TC⟩`, but leaving the **convergence rule = the mechanism under test** open is an **overfit surface** (tune "converge" onto successful cells), not a cosmetic TODO ⇒ H_scheduler not falsifiable until frozen | H_scheduler | (a) flagged, implication unnamed |
| **S9** | MED | "R4/R5 differ only in T0" (§2,§6) | at equal **token** budget, R5's smaller (lossy) input affords **more passes** than R4 ⇒ breaks "差は T0 の情報量のみ"; `R5≈R4` could mean "extra passes compensated," not "structure suffices" | H_structure | **(b) contradiction** |
| **S10** | LOW-MED | "consensus detector" spec (§2) | the detector feeding R1/R3/R4 is unspecified and **not in the ⟨TC⟩ freeze list**; H_gen (R2 vs R1) and the R1/R3/R4 group confound reconstructor quality with detector quality | H_gen, comparability | **(b) unflagged** |
| **S11** | LOW | frozen-ref basis (§10 vs §11-4) | §10 asserts overfit-prevention via "既凍結 ref のみ" in the present tense, but §11-4 admits the **ref set is still `⟨TC⟩`**; ref-set choice is another author DOF (compounds S2) | H_recon | (a) flagged, tense overclaims |

## Minimal fixes (preregisterable, no implementation)
- **S1** → add **R0 = HBB-best-method (base/skepticism) replication inside this harness at matched budget** on {08,10,30}; require H_recon: `R_success REC2 > R0 REC2` in-harness. If R0 already reaches REC2, the motivating premise was a harness artifact.
- **S2** → remove the free routing DOF: apply the frozen operator set **exhaustively** (no selection); OR freeze the selector on a **calibration set disjoint from {08,10,30}** (targets unseen); OR selector authored/frozen by a target-blind party. Until then **strike the anti-overfit claim** in §10.
- **S3** → carry the GPT-bound caveat into §5; require a positive to be **robust to dropping GPT** (Qwen-alone also REC2), OR add a genuine 3rd scorer, OR relabel the endpoint "GPT-certified," not "consensus."
- **S4** → define "autonomous"; treat detector-supplied defect locus as an H1-equivalent hint; restrict the **autonomous** primary claim to **R2**; classify R1/R3/R4 REC2 as assisted.
- **S5** → preregister seed-aggregation (reached = ≥⌈M/2⌉ seeds, not ≥1), a **floor/null** (needs S1's R0) with a fixed-α test, and a **single pre-specified** primary condition or explicit multiplicity correction.
- **S6** → replace the binary with a **graded lossy ladder** + a **manipulation check** (does the §4.3 selector still route on lossy T0?); reframe "structure is active" as an **absolute existence** result (R5 reaches REC2 on its own), not `R5≈R4`.
- **S7** → add a budget-matched **plain best-of-N** control (N samples + select, no STOP/SHIFT/COMPARE); `H_scheduler = R4 > max(R3, best-of-N)`; also report R4 vs R2.
- **S8** → freeze convergence rule + pass cap in the §10 freeze list **before go**; forbid outcome-dependent adjustment.
- **S9** → match **pass count** (not only tokens) between R4/R5, or report both axes and interpret only when both match.
- **S10** → add "detector spec" to the freeze list; identical across R1/R3/R4.
- **S11** → state the anti-overfit guarantee is **contingent** on freezing both the ref set and the selector.

## (a) known gaps vs (b) presented-as-sound
- **(a) flagged `⟨TC⟩`** (draft is honest these are unrun-until-defined): convergence/manifest (S8), lossy def (part of S6), ref-set (S11), selector *rule* (part of S2), budget number + M (parts of S5/S7).
- **(b) load-bearing weaknesses presented as SOUND** (the important ones): **S1, S2-guarantee, S3, S4, S5-bar-design, S6-interpretation, S7, S9, S10.** These are validity holes, not plumbing.

## Status / next
- Prereg draft = **BLOCKED**; do not freeze or run until S1–S7 (and S9) are resolved. `⟨TC⟩` param definitions are
  necessary but **not sufficient** — S1/S2/S3/S4 remain even after all params are filled.
- The hard-core {08,10,30} fixing (DE-0115) and the freeze-before-run discipline are intact; this audit does not
  touch them.
- Author-side corroboration: S1, S2, S3, S5, S6, and S7(partial) were independently pre-identified author-side;
  **S4 (sharpened), S9, S10** were added by the independent auditor. Recording the attribution honestly.
- No implementation. Revising the prereg to incorporate these fixes is a **design revision** (not implementation)
  and awaits Taka's direction — as does supplying the `⟨TC⟩` specs.
