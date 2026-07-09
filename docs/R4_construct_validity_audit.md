# R4 construct-validity audit — is R4 a valid instrument for STOP–SHIFT–RUN–COMPARE?

**Scope.** Construct validity of the R4 condition as an instrument for the intended Taka scheduling
hypothesis. This does **not** reopen or revise the primary capability-exhibit (DE-0127 stands). It does not
modify any frozen artifact. It reaches **no** verdict on whether the scheduling hypothesis is true or false.
Requested by Taka / GPT audit. No rerun performed.

Grounded in code: `experiments/run_recon_exhibit.py` (harness), `experiments/hbb_recon_impl_binding.json`
(B-2), `experiments/run_recon_consensus.py` (aggregation).

---

## 0. Empirical-premise correction (load-bearing, precedes everything)

The audit request assumes an empirical result: *"R2 reached HBB-08; R4 did not"* and *"R4 = 0 therefore
STOP–SHIFT–RUN–COMPARE did not work."* **Both premises are factually wrong about what was run.**

**R4 was never generated or scored.** Verified against the artifacts:
- primary candidates (`hbb_recon_primary_candidates.json`): conditions present = **R0, R2, R_bon only**
  (30 records each = 3 incidents × M=10).
- primary Qwen scores (`hbb_recon_primary_qwen_scores.json`): conditions = **R0, R2, R_bon only**
  (1320 each). No R4 rows exist.
- The `"R4": 0.0` values inside `hbb_recon_exhibit_consensus.json → H_scheduler_secondary` are a
  **default-fill**: `run_recon_consensus.py:59` is `def rr(cond,inc): return agg.get((cond,inc),{"reach_rate":0.0})["reach_rate"]`
  — any condition absent from the data returns `0.0`. R4/R3/R5 were all **held secondaries** in the
  primary-only run; their `0.0` is "not measured," not "measured zero."

**Consequence:** there is currently **no empirical R4 result to interpret.** The correct present statement is
even narrower than GPT's proposed correction:

> R4 has not been run. No inference about the STOP–SHIFT–RUN–COMPARE / Taka scheduling hypothesis — positive
> or negative — is licensed by the current artifacts.

The rest of this document audits whether R4, **as frozen/implemented**, *would be* a valid instrument if run.
Finding it doubtful is a reason to fix the instrument **before** spending a run, not to reinterpret a
non-existent result.

---

## 1. Intended construct (the hypothesis to be operationalized)

Taka's observed process, as a mechanism (not as an answer):

1. read roughly → form an **incomplete provisional** interpretation;
2. **STOP early** (cut the run before completion/coherence sets in);
3. **suspend/abandon** that interpretation;
4. **SHIFT** viewpoint;
5. **reread the same situation** from the new viewpoint (independent of the prior read);
6. repeat several **short, partly independent** views;
7. **COMPARE** structural differences among those rough views;
8. **REBUILD** a replacement frame from the differences.

Suspected LLM failure mode being targeted: **excessive completion and continuity inside one interpretation
path.** So the mechanism's active ingredients are: *short/incomplete runs + interruption + viewpoint change +
partial independence + structural comparison + frame rebuild.* It is **not** "apply multiple operators."

---

## 2. Actual R4 execution semantics (from code)

`candidates_for(..., "R4", ...)` → `out = r4_passes(fr, pass_cap)` (`run_recon_exhibit.py:105-106`).
Note: **`seed` is not passed into `r4_passes`** — R4 ignores the M-seed entirely.

`r4_passes(frame0, pass_cap)` (`run_recon_exhibit.py:68-77`):

```
pooled, frame = [], frame0
for p in range(pass_cap):                       # 4 passes
    outs = [op_candidate(o, frame) for o in OPERATORS]   # 11 deterministic operators
    pooled += outs                              # retain ALL outputs
    prior = " || ".join(pooled)[:2500]
    frame = frame0 + "[prior structural proposals, all pooled — no selection]" + prior
return pooled                                   # 44 raw operator outputs = the candidates
```

`op_candidate` (`:52-66`) runs `afe.run_operator(op, frame)` (temperature=0/seed=0 deterministic) and renders
the operator's own structural fields as the candidate text. **The operator outputs are themselves the scored
candidates** — there is no later stage.

So R4 is: **a deterministic, seed-invariant, cumulative multi-operator cascade** —
`T0 → 11 ops → pool all → append pool to T0 → same 11 ops → … ×4`.

---

## 3. Construct-to-code mapping (Q1)

Grade each intended element against its implementation site. PRESENT / PARTIAL / ABSENT.

| # | Intended element | Implementation site | Grade | Note |
|---|---|---|---|---|
| 1 | **STOP** (early cutoff of a run) | none; each pass runs all 11 operators to completion | **ABSENT** | no interruption primitive at all |
| 2 | **interpretation suspension/abandonment** | `pooled += outs` (`:74`) retains everything | **ABSENT (inverted)** | see §5 |
| 3 | **SHIFT** (viewpoint change) | 11 distinct operators applied in parallel (`:73`) | **PARTIAL** | viewpoint *multiplicity* exists; a *scheduled* suspend-then-shift does not; same operator set every pass |
| 4 | **independent reread** | pass 1 reads `frame0`; passes 2-4 read `frame0 + pooled prior` (`:76`) | **PARTIAL** | only pass 1 is an independent reread of T0; later passes read accumulated interpretations |
| 5 | **short run** (truncated/incomplete) | operators emit full structural proposals; `mt=280` is generic, not a "stop-early" | **ABSENT** | no incompleteness pressure |
| 6 | **incomplete/lossy view** | not in R4 (R5's job) | **ABSENT** | R4 uses full T0 |
| 7 | **structural signature extraction** | none | **ABSENT** | no signature per view |
| 8 | **comparison across views** | pooling (`:74-76`) is concatenation, not comparison | **ABSENT** | no `delta(A,B)` anywhere |
| 9 | **frame-family rebuild** | operator outputs are the candidates directly (`return pooled`) | **ABSENT** | no rebuild stage |
| 10 | **convergence / selection** | explicitly "no selection" (`:76`) | **ABSENT** | by design |

**Summary:** 0 PRESENT, 2 PARTIAL, 8 ABSENT. Every element that distinguishes the hypothesis from "apply
multiple operators" (STOP, abandonment, independent reread beyond pass 1, comparison, rebuild, selection) is
ABSENT.

---

## 4. Missing mechanisms

- **Interruption / temporal granularity** (STOP, short run): entirely unimplemented. R4 has no notion of
  cutting a read short; it is the opposite of "stop early."
- **COMPARE**: no extraction of per-view structural signatures and no computation of differences among them.
  Pooling text ≠ comparing structure.
- **REBUILD**: no stage converts multiple short views into one structurally rebuilt replacement frame. The
  candidates *are* the raw views.
- **Genuine M-sampling**: `seed` is ignored for R4 (`:106`), operators are deterministic, so all M=10 seeds
  would produce **identical** R4 candidates. As an instrument, M=10 gives **one** sample reported ten times —
  zero variance, all-or-nothing reach. Even as a *cascade* test this is a single observation.

## 5. Inverted mechanisms (Q2)

The hypothesis wants to **break** within-path completion/continuity. R4 does the reverse:

```
intended:   interpretation → STOP → suspend/abandon → fresh independent view
R4:         interpretation → retain ALL → append ALL to frame → re-run → (coherence with prior grows)
```

Passing `frame0 + pooled prior` into the next pass (`:76`) creates **cumulative context** that plausibly
increases anchoring / commitment / coherence-with-prior — the exact failure mode (excessive completion and
continuity) the hypothesis was trying to disrupt. I cannot *measure* anchoring from the current artifacts
(R4 wasn't run), but **structurally the pooling applies pressure in the inverted direction.** This is the
single most serious construct defect: R4 may not merely omit the mechanism, it may enact its opposite.

## 6. R2 vs R4 behavioral comparison (Q4 — ignore labels, compare traces)

- **R2** (`:99-101`): for each of N candidates, `qgen(P_R2, "CURRENT STUCK FRAME:\n"+fr, seed*1000+k)`.
  Every draw reads **only T0**, independently, stochastically (temp 0.8, distinct seeds). No accumulation.
- **R4**: deterministic, seed-ignored, cumulative pool, same 11 operators each pass.

| Dimension (from the hypothesis) | R2 | R4 |
|---|---|---|
| repeated reread of the **same source** | **yes** (every draw reads T0) | only pass 1; then reads accumulated pool |
| **no cumulative commitment** to prior interpretations | **yes** (fresh each draw) | **no** (pools all prior) |
| **partial independence** across views | **yes** (independent samples) | weak (later passes see all prior) |
| genuine **sampling variance** over M | **yes** (stochastic) | **no** (deterministic, seed ignored) |
| multiple **distinct viewpoints** per step | no (one reframer prompt) | yes (11 operators) |
| explicit **STOP / short run / COMPARE / REBUILD** | no | no |

**Answer (Q4):** on the dimensions that most define the hypothesis — *repeated same-source reread*, *no
cumulative commitment*, *partial independence*, *real sampling* — **R2 is behaviorally closer to the intended
mechanism than R4.** R4 is closer only on raw viewpoint multiplicity, which it then pools rather than compares.
Neither implements STOP / COMPARE / REBUILD. (This is a statement about execution traces, not about which
"worked" — R4 has no result, and R2's confirmed exhibit is single-incident and GPT-strictness-driven per
DE-0127.)

## 7. Is a negative R4 result interpretable against the hypothesis?

Two-part answer:

1. **There is no R4 result** (§0). So the immediate question is moot: nothing to interpret.
2. **Even if R4 were run and returned 0**, it would be interpretable only as: *"the deterministic cumulative
   operator-cascade produced no consensus REC2"* — **not** as evidence against the STOP–SHIFT–RUN–COMPARE
   hypothesis, because (§3–§5) R4 does not instantiate that construct and may invert it. Construct validity
   fails on 8/10 elements including all of STOP, COMPARE, REBUILD.

Adopt exactly:

- Supported by artifacts: **nothing about R4** (unrun); if run, at most *R4-cascade implementation result*.
- **Not** supported: *Taka scheduling hypothesis = negative*. This distinction is load-bearing.

**Q3 (reconstruction stage), explicit:** operator outputs became candidates because the binding
(`hbb_recon_impl_binding.json` B-2 `operator_candidate_rendering`) renders each operator's own output as a
readable candidate and scores it directly. **There was no implemented stage that converts multiple short views
into one structurally rebuilt replacement frame.** Stated plainly: the COMPARE and REBUILD portions were never
built, hence never tested.

**Q5 (what was actually specified to be tested), narrowest defensible:** R4 as frozen would test *repeated
multi-operator structural transformation under growing cumulative context, deterministically*. It would **not**
test temporal granularity, interruption scheduling, independent reread, or compare-then-rebuild.

---

## 8. Minimum faithful scheduler prototype for a future test (spec only — not designed here, not run)

Target-blind (breakthrough_structure never enters generation), no author selection at the view level,
consensus scoring (GPT ∧ Qwen), M genuinely stochastic. Each intended element gets a real site:

1. **Short/interrupted view** — generate a *deliberately incomplete* read: hard cap (e.g. very low
   max_tokens and/or an explicit "give only your first provisional partial read, then stop") so no view
   completes into a coherent frame.
2. **Independent reread** — every view reads **only T0** (or a lossy T0), **never** any prior view's output.
   No pooling. This is the core fix vs R4.
3. **Viewpoint SHIFT** — each short view is taken under a **different explicit lens**, and the lens set is
   **sampled** per seed (so M seeds are real independent draws of the schedule).
4. **Partial independence** — views generated without visibility of each other.
5. **Structural signature extraction** — a distinct step that reduces each short view to a structural
   signature (subject / level / key-distinction axis), not prose.
6. **COMPARE** — compute differences among signatures (what structurally varies across the rough views).
7. **REBUILD** — a **separate** stage that synthesizes a replacement frame **from the deltas**, not from any
   single view. This is the candidate that gets scored (not the raw views).
8. **Convergence / selection** — SELECT / HOLD-2 / SHIFT-AGAIN / ESCALATE as an explicit, versioned rule.
9. **Instrument hygiene** — fix R4's seed-ignored determinism: the view generator and lens sampling must be
   stochastic so M is real replication; log per-view so the schedule is auditable.

**Construct-validity acceptance gate (before any such run):** an independent auditor must grade elements
1–8 as PRESENT (not PARTIAL/ABSENT) on the *code*, and confirm **no cumulative pooling** re-enters (i.e. the
§5 inversion is gone). Only then is the instrument eligible to test the hypothesis.

**Constraints honored:** frozen primary artifacts untouched; DE-0127 not revised; hypothesis neither supported
nor rejected; prototype is mechanism-only and target-blind; nothing run. This is a spec, gated on Taka.

---

### One-line finding

R4 (as frozen, and in any case **not run**) is **not** a valid instrument for the STOP–SHIFT–RUN–COMPARE /
Taka scheduling hypothesis: 0/10 constructs PRESENT, all of STOP/COMPARE/REBUILD ABSENT, and its cumulative
pooling plausibly **inverts** the mechanism under test. Any future test requires the §8 instrument, not R4.
