# Round-2 load-bearing audit — HBB Reconstruction Prereg v0.4

**audited: 2026-07-08. verdict: `STILL-BLOCKED` on S2 (+ one doc reconciliation B2).**
Method: independent adversarial auditor (fresh general-purpose subagent) re-checked each v0.3 finding S1–S11
against v0.4's actual text (not the author's fix-claims), and looked for NEW holes; **author-side verified both
blocking findings against v0.4 §5.2/§5.3/§1/§2 — both hold.** author ≠ auditor. No implementation.

## Resolution table (vs DE-0116 S1–S11)
- **RESOLVED (9)**: S1 (R0 in-harness null + attribution rule R_success>R0, §3/§7) · S3 (mandatory honest relabel forecloses the overclaim regardless of param; real GPT-drop robustness still needs the 3rd scorer, §6) · S4 (clean autonomous/assisted split; primary autonomy = R2 only, §2/§4) · S5 (floor=R0, ≥⌈M/2⌉ seeds, α=0.05, multiplicity, single primary condition, §7/§8) · S6 (absolute-existence reframe + graded ladder + manipulation check, §5.4/§7) · S7 (R_bon best-of-N control; H_scheduler=R4>max(R3,R_bon), §3/§6/§7) · S8 (convergence rule frozen, outcome-dependent tuning forbidden, §5.1/§9) · S9 (R4↔R5 matched on pass count AND token; moot under S6 reframe, §6/§5.4) · S11 (ref set frozen; anti-overfit stated as contingent, §5.2/§9).
- **S10**: RESOLVED on substance (detector spec in freeze list) **but** a text contradiction remains → **B2**.
- **S2**: **PARTIAL — BLOCKING** → **B1**.

## Blocking items
### B1 (S2) — the overfit DOF is NOT foreclosed regardless of param
Two leaks in v0.4 §5.2/§5.3:
1. **"全 ref を budget 内で exhaustive 適用" (§5.2) + "multipass は budget 内" (§6)** ⇒ the operator budget can
   **truncate**. Under truncation, the "orders-only" selector is no longer a no-op: **which operators run
   becomes a function of ordering ⇒ ordering == selection ⇒ covert routing**. This is exactly the DOF S2 was
   meant to kill, re-entering through the budget door.
2. **Target-independence certification is too weak**: it checks the rule does not *reference* the target; it does
   NOT catch a *feature-set / priority chosen* by an author who knows {08,10,30}. The v0.3 audit's S2 fix menu
   required the stronger guarantees (target-blind authorship OR disjoint calibration set); v0.4 substituted the
   weaker "audit the rule," and the fully-clean option (pure exhaustive) is only a fallback, not mandated.

**Close B1 by choosing one (design decision — touches the Taka-requested STRUCTURAL PROJECTION feature):**
- **B1-(i) pure exhaustive (mandate)**: every ref operator runs **to completion on every run**; matched budget
  **sized to guarantee completion**; outputs pooled so **order is immaterial**. Selector collapses to a genuine
  no-op on the result set (STRUCTURAL PROJECTION becomes a *separate secondary study* — does ordering matter? —
  explicitly outside the overfit-critical primary path). Cleanest anti-overfit; auditor's preferred.
- **B1-(ii) keep selector load-bearing, harden it**: freeze the selector **and its feature set** on a
  **calibration set disjoint from {08,10,30}** (thresholds/features chosen without seeing hard-core targets), or
  by a **target-blind party**. Preserves STRUCTURAL PROJECTION as functional, but needs a target-blind authoring
  process (Claude, who knows the targets, cannot author it).

### B2 (S10) — doc reconciliation (mechanical, no design choice)
§1's S10 row said "R1/R3/**R4(assisted)** で同一"; §2/§4 define R4 as **autonomous (T0-only, no detector)**.
Fixed to "R1/R3 で同一 (R4 は autonomous=detector なし)". §2 governs.

## NEW holes check
Auditor confirmed the task-flagged risks did NOT materialize: R0 is faithful (it is the exact A/B arms that
failed the hard-core, so R0≈0 is the correct null, not a weak floor); multiplicity over N=3 does not kill power
(floor≈0 + M=10 keeps detectability; N=3 honestly scoped as a probe); the "author-run certification" escape is
only closed by B1-(i) pure exhaustive (loops back to B1). The one genuinely-new hole = B1 leak #1 ("exhaustive
within budget" reintroducing a truncation→selection confound).

## Status
- v0.4 = **STILL-BLOCKED on S2**. B2 fixed in-doc. Freeze/hash gated on: **B1 resolved (Taka's choice i/ii)** +
  `⟨TC⟩` params filled + (recommended) a short round-3 re-audit of the S2 fix.
- S1, S3–S9, S11 are audit-clean on validity. hard-core (DE-0115) and freeze-before-run intact.

---

## Round 3 — focused re-audit of B1-(i) (v0.4.1)

Independent auditor (fresh subagent) + author-side verification against the text. **Verdict: S2 STILL-OPEN.**
- **Leak #1 (within-pass truncation → ordering==selection): CLOSED param-independently.** §5.2 mandates full
  operator completion + pooled outputs + budget sized to guarantee ≥1 exhaustive pass; larger budget is always
  safe, so closure does not depend on the param. No residual within-pass path.
- **Leak #2 (selection criterion chosen with target knowledge): STILL-OPEN in the PRIMARY path.** H_recon is
  measured on **R2**, and §2 defines R2 = "独立生成→**選択**" — a Claude-authored selection step. §5.2's
  pure-exhaustive is scoped to **R4's shift operators**, not R2's frame-selection; so §5.3/§10's "primary path
  (R2/R4) uses no selector" is a non-sequitur for R2 and contradicts §2. Round-2 already ruled "frozen +
  non-referencing" insufficient for leak #2; R2's selection meets only that weak bar ⇒ leak #2 survives in the
  endpoint that carries the primary claim. (R_bon "N sample→選択" has the same shape.)
- **New holes:** (a) budget-sizing vs matched-budget (S7) — **NOT reopened**; giving all conditions R4's
  exhaustive-completion budget only makes R_bon a *stronger* control (conservative). Non-blocking caveat:
  equal-token ≠ equal-utility (R4 uniquely saturates the budget) — read the H_scheduler margin with that
  asymmetry. (b) **cross-pass minor gap**: doc guarantees completion for ≥1 pass but doesn't state the final
  output is pooled across passes (vs an author best-pass pick) or forbid a partial final pass — a thin cross-pass
  promotion DOF.

### Fix applied → v0.4.2 (extend B1-(i) to ALL selection)
**No author-side selection anywhere.** Every condition emits its **full candidate set** (R4: all operators × all
passes pooled; R2: all N generated frames; R_bon: all N samples; R0/R1/R3/R5 likewise). Generation prompts are
frozen, target-blind, T0-only, seed-varied. The **target-held-out independent scorers** score every candidate;
"condition reaches REC2 on incident" = **≥1 candidate certified by consensus**. Selection moves entirely to the
target-blind scorer; the author never picks. Cross-pass outputs pooled (no best-pass author pick); budget
guarantees full passes (no partial final pass). All conditions get this uniformly at matched budget, so the
any-of-N inflation is controlled by the R0 floor (H_recon = R2 > R0). §2 (R2/R_bon), §5.3, §10 reconciled.

---

## Round 4 — re-audit of the no-author-selection fix (v0.4.2) → STILL-OPEN (structural)

Independent auditor + author-side verification. **Verdict: the *selection* surface is genuinely closed; two
residuals remain — one patchable, one structural (root cause).**

- **Selection closed (real, param-independent)**: §2's no-author-selection principle removes the author's
  selection knob across R2/R4/R_bon/cross-pass; the endpoint is decided by the target-held-out scorers, not the
  author. Round-3's leak #2 *as scoped to selection* is closed. This is a genuine general closure, not a local patch.
- **Residual 1 — any-of-N floor fairness (PATCHABLE)**: the endpoint is now best-of-N ("≥1 of N certified"),
  monotonic in N. §6 matches **total token** but **never pins N (candidate count)** between R0 and R2 (R0="単段").
  If R2's per-candidate generation is cheaper, R2 draws more candidates → higher reach from N alone, not
  reconstruction. Compounds S3 (best-of-N over a GPT-bound consensus amplifies GPT idiosyncrasy). Fix = freeze
  **N-parity** (match candidate count, not just token) between R0 and R2 in §9, or an explicit N-invariance argument.
- **Residual 2 — target-aware GENERATION authorship (STRUCTURAL, root cause)**: with routing (round-2/3) and
  selection (round-3/4) removed, the only author-controlled surface left is **generation** — Claude authors the
  ref-operator **set** (§5.2) and R2's generation prompt **while knowing {08,10,30}** (Claude authored their
  breakthrough_structures, DE-0115 caveat). §2 guards these only with "frozen + non-referencing + T0-only +
  seed-varied" = **the weak bar round-2 explicitly rejected for leak #2** (which required *target-blind authorship*
  OR a *disjoint calibration set*). Pure-exhaustive stops covert *promotion*, but *including* a target-hitting
  operator in the frozen set still steers R2 toward the target = overfit by **set composition**. §11 ⟨TC⟩#2
  mislabels "ref set membership" as a benign param when *who authors it and whether authorship is target-blind* is
  a **validity** question. §10's "author=機構のみ" is in tension with Claude authoring this content knowing the targets.

### Convergence judgment (escalate, do NOT patch)
Rounds 2→3→4 are the **same signature**: the overfit DOF hops routing → selection → generation while the guard
stays "frozen/non-referencing." Per-knob patching will keep surfacing the next knob. The structural terminator is
the round-2-prescribed fix never adopted for CONTENT authorship: **decouple authorship from target knowledge**.
This is not "⟨TC⟩ params + Taka freeze" — it is a design/process decision for Taka:
- **(A) target-blind authoring party**: a party that does NOT know {08,10,30}'s targets authors the ref-operator
  set + generation prompts (Claude is 当事者 → excluded).
- **(B) disjoint calibration set**: freeze/validate the operator set + prompts on incidents disjoint from
  {08,10,30} (e.g. HBB DEV/VAL), so they can't be tuned to the hard-core targets.
- **(C) accept & downgrade**: acknowledge H_recon is contingent on target-aware authoring and downgrade the
  autonomy claim accordingly (the experiment cannot cleanly claim *autonomous* reconstruction when the mechanism
  author knew the answers).
Residual 1 (N-parity) is patchable in-doc regardless of the (A)/(B)/(C) choice. Residual 2 gates freeze.

---

## Round 5 — re-audit of v0.4.3 (claim split, B disjoint-calibration) → STILL-OPEN (narrowed)

Independent auditor + author-side verification. **The claim split killed the autonomy overclaim cleanly and
closed N-parity, but the round-4 root cause moved up one level (criterion/pool/template authorship) and the
kept "transfer" claim rides it.** DOF-hopping signature (rounds 2→3→4→5) NOT terminated.

**Clean (confirmed):** autonomy disclaimed consistently (§1/§2/§7/§10); §12 FUTURE-SEALED is a genuine deferral
(names requirements the setup can't meet, gates on Taka go); N-parity (residual 1) closed across R0↔R2↔R_bon↔R4↔R5
(§4/§5/§6/§9); DEV∪VAL confirmed disjoint from {08,10,30} (hbb_split.json); prior routing/selection closures hold.
B disjoint-calibration is real *partial* protection (a pure target-memorizer failing on DEV/VAL is excluded).

**STILL-OPEN — R5-A (root cause, narrowed):** B constrains the fitting *data* (DEV∪VAL), not the fitting
*apparatus*. Claude — who authored {08,10,30}'s breakthrough_structures — still authors the **ref-pool
composition, the membership rule form + θ, and the R2 generation template** (§3; §11 ⟨TC⟩#1/#2). The
"DEV/VAL-reach ≥ θ" gate narrows steering to **dual-purpose operators (DEV/VAL-useful AND target-hitting) +
pool/template choice** but does not remove it; the guard ("generic + pre-registered + auditable") is the
audit-the-rule bar round-2 rejected for leak #2. **§9 "no-Claude-discretion" contradicts §11 (criterion left as a
Claude-filled ⟨TC⟩).** §11 still mislabels ref-pool membership a "parameter" (round-4 mislabel).

**Over-claim:** §3's closing sentence ("残る contamination は claim downgrade で honest に負う") is **false as
written** — the downgrade discharges *autonomy*, not *transfer*. "Transfer" is a held-out/generalization claim;
a target-aware criterion breaks its held-out-ness. §1/§7 read clean when the mechanism is only
**calibration-DATA-disjoint, not authorship-disjoint.**

**New hole from the reframe:** under the transfer frame, **R0 is the wrong null** — R2>R0 isolates
"mechanism > no-mechanism," not "disjoint-derived mechanism transfers"; no arm applies a blindly-/differently-
derived mechanism, so R2>R0 cannot separate genuine transfer from criterion-to-target contamination. R0 remains
a valid floor; it must not be read as isolating the disjoint-derivation's contribution.

### Terminators (naming, not proposing implementation) — a Taka decision, not a param
The audit has **converged on a diagnosis**: Claude authoring an experiment whose targets Claude knows cannot
support a *generalization* claim (autonomy OR transfer); every round the same knob reappears one level up.
Concrete terminators (v0.4.3 adopted B+autonomy-downgrade, which sits *between* these):
- **(A) target-blind authorship** — a party that does NOT know {08,10,30} authors the criterion + ref-pool +
  generation template (round-4 menu (A), not picked). Removes the knob → transfer becomes clean.
- **Downgrade the kept claim: "transfer" (generalization) → "capability exhibit"** — claim only that *this
  specific frozen artifact reconstructs these 3 hard-core structures*; assert no generalization. Then the
  criterion-authorship residual is **non-load-bearing** (nothing held-out is claimed). Cheapest honest option;
  reserve transfer + autonomy for the FUTURE-SEALED track (§12) with target-blind authorship.
- **(C) blind/differently-derived control arm** — add an arm whose mechanism is derived by a target-blind
  process; compare, and bound "transfer" to the gap.

Also fix regardless of the choice: §9↔§11 contradiction; §3 over-claim sentence; R0-as-null caveat; N-vs-M
label nit (§5/§8/§11).
