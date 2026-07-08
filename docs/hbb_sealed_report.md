# HBB SEALED Report (§5) — for GPT / Claude-chat independent cross-review

Date 2026-07-08. Scorer: Claude external-weight (partially blind — knows arms; external cross-review is
the real blind check). SEALED local N=11 (HBB-04/30 = GPT handoff, not run). Frozen config; probe sets
sealed before opening (565899c9 / 2e301c52 / 38111563). Leak audit max 5-gram 0.0. **Per directive §6,
the result is recorded as-is; H_primary did not hold, and that is a valid benchmark output.**

## A. H_primary verdict — NOT_CONFIRMED
Prereg H_primary: `B∪C > max(B,C) on SEALED AA AND C-unique ≥ 1`.
- B on AA (6): HBB-01, 05, 08, 10, 11 = **5/6**.
- C (AFE) on AA: HBB-05, 08, 10 = **3/6**, all ⊆ B.
- **B∪C = 5 = max(B,C) = 5. C-unique = 0.**
→ Falls on the prereg row **"B∪C ≈ max(B,C) → engine は skepticism を補完せず"** AND **"C-unique = 0 →
AFE固有の AA 回収は DEV/VAL 偶然だった"**. The DEV/VAL complementarity (C uniquely reached HBB-02) did
**not replicate**. Skepticism alone dominates AA.

## B. Per-incident matrix (Independent Hint Sufficiency depth; 4=Free … 0=none)
| incident | scope | A | B | F | C(AFE) | D(Formal) | breakthrough |
|---|---|---|---|---|---|---|---|
| HBB-01 | AA | 0 | 3 | 4 | 0 | 0 | def→pred leakage |
| HBB-03 | AA | 0 | 0 | 0 | 0 | 0 | return-to-substrate |
| HBB-05 | AA | 0 | 4 | 3 | 2 | 3 | measurement individuation |
| HBB-06 | FOS | 0 | 3 | 3 | 2 | **4** | birth-method artifact |
| HBB-08 | AA | 0 | 2 | 0 | 2 | 0 | physical layer is floor |
| HBB-10 | AA | 4 | 4 | 2 | 2 | 2 | sync ≠ integration |
| HBB-11 | AA | 0 | 3 | 0 | 0 | **4** | cross-system node ID |
| HBB-12 | FOS | 0 | 2 | 0 | 0 | **4** | averaging trap |
| HBB-13 | FOS | 0 | 3 | 0 | 2 | 2 | self-fulfilling baseline |
| HBB-17 | FOS | 0 | 4 | 0 | 3 | 0 | ICC≈0 inert lens |
| HBB-24 | FOS | 0 | 2 | 0 | 0 | 0 | timescale/spatial mismatch |

**Breakthrough Reach**: A 1/11 · **B 10/11** · F 4/11 · C 6/11 · D 6/11. AA: A 1 · **B 5** · F 3 · C 3 · D 3.
FOS: A 0 · **B 5** · F 1 · C 3 · D 3.

## C. C-unique / B-unique
- **C-unique (C reached, B missed) = 0** (on AA and overall).
- B-unique over C = HBB-01, 11 (AA) + HBB-17, 24 (FOS). B reaches almost everything.
- **Nobody reached HBB-03** (return-to-substrate) — the deepest AA resist. HBB-24 only B (partial).

## D. D-SECONDARY (Formal) — null HOLDS
Prereg null: "D does not beat B alone on AA." D on AA = 3/6 < B 5/6 → **null holds** (Formal layer adds no
reach over skepticism). D-unique on AA = 0.
- **Honest bright spot (not a claim)**: D reached **HBB-06 / HBB-11 / HBB-12 at H0 (Free)** via genuinely
  Formal-structural probes — "procedure_induced_structure" (FE-L/observer → birth artifact),
  "injection_artifact" (FE-LINK → cross-system), "individual_atom_distribution" (FE-L/ε → averaging).
  So the Formal probes CAN generate the right structural axis at LOW hint on specific incidents — but B
  reached those too (at H1-H2), so D shows no net reach advantage. Per D-SECONDARY status this is
  reported, not claimed.

## E. EMP secondary — not supported
On observer-artifact/level-subject SEALED incidents (HBB-05/06/10/13), C+EMP (=D) did not exceed C or B.
HBB-03 (level-shift) reached by no arm. No support for the empirical observer probe adding reach here.

## F. Scoring provenance + spot-check
Scorer = Claude external-weight (partially blind). Rubric = Independent Hint Sufficiency depth +
disposition (all reaches were HISTORICAL_MATCH or MISS; no FALSE_BREAKTHROUGH or ALT_UNTESTED surfaced —
outputs were either on-target or accepted-the-frame). **External spot-check targets (pre-fixed rule = all
SEALED AA + 20% FOS)**: HBB-01, 03, 05, 08, 10, 11 (AA) + HBB-06, 12 (FOS, = D's H0 Formal reaches, worth
verifying they aren't orchestrator JSON-leak noise).

## G. Methodological flags for cross-review
1. **B's SEALED reach (10/11) ≫ its DEV/VAL reach (8/15 = 53%).** Either the class-stratified split put
   more "question-the-taken-for-granted-metric" incidents in SEALED (a composition imbalance), or the
   scorer drifted more lenient on B in SEALED. Cross-review should re-score B on the AA set blind.
2. Scorer is partially blind (knows arms). Anonymized re-scoring by GPT/Claude-chat is the real check.
3. D's orchestrator emitted JSON-leak fragments on several cells (same defect as AFE walking) — D's H0
   reaches (HBB-06/11/12) should be verified against the raw operator signals, not just the orchestrator.

## H. Preregistration deviations
**ZERO.** No probe wording, rubric, or arm-config change after opening. No post-hoc hypothesis swap.
H_primary recorded as NOT_CONFIRMED as-is (§6).

## I. Narrow conclusion
On the SEALED one-shot (N=11 local), **the ontological engine (AFE, C) and the Formal-ESDE engine (D)
did NOT demonstrate added value over generic skepticism (B) on historical-breakthrough reach.** B alone
reached 10/11 (5/6 AA); C/D each 6/11 with C-unique = D-unique = 0. The B∪C complementarity seen in
DEV/VAL did not generalize. Generic skepticism is a strong baseline on this benchmark. The engines'
only differentiated behavior was D reaching a few incidents at lower hint via genuine structural probes
(reported under D-SECONDARY, not claimed). Deepest resist (HBB-03 return-to-substrate) reached by no arm.

---

## CORRECTION ADDENDUM (skeptical re-check, DE-0113)

Taka directed a skeptical re-examination. It found a real defect and NARROWS this report:

**Defect — scorer-reliability crisis.** Re-scoring the same SEALED outputs with a genuinely-blind,
brevity-neutral Qwen scorer gave the OPPOSITE absolute picture: engine C/D = 11/11 (Qwen) vs 6/11 (my
strict scoring); B = 10/11 in both. Inter-scorer variance on absolute reach is enormous — the single-
scorer disposition used in §A-F is **not reliable**.

**Retraction.** The §I / §B framing "B dominates 10/11, engine no added value, engine weaker than
skepticism" was a **strict-scoring artifact** — under Qwen the engine *out-reaches* B. That framing is
RETRACTED. (Likely an over-negative bias — this session repeatedly rewarded humble negatives.)

**What survives (robust across my / Qwen / consensus scorers).** **C-unique = D-unique = 0 in all three.**
No engine arm uniquely reaches an AA breakthrough that skepticism misses. So the *corrected* verdict:
- **H_primary NOT_CONFIRMED (robust):** the AFE/Formal engines do NOT complement skepticism (no unique AA
  recovery), across all scorers.
- **Absolute engine-vs-skepticism strength is NOT measurable here** — scorer variance dominates. Any claim
  that the engine is weaker (or stronger) than skepticism is unsupported.

**Fix registered.** MULTI_SCORER_CONSENSUS permanent instrument: future reach/disposition claims require
multi-scorer agreement; report only findings robust across scorers. Arms need NOT be re-run (outputs are
sound; the defect was in scoring). Additional un-controlled caveats: Formal D was a partial compiler
(5/8 probes, L/Ω/boundary SOURCE_GAP), so "Formal no value" is doubly narrow; and the SEALED split may be
composition-imbalanced toward skepticism-favorable metric-artifact incidents.

---

## GPT THIRD-SCORER (rubric-v2 DETECTION/RECONSTRUCTION, DE-0114)

Taka handed off a **third independent scorer (GPT)** using a frozen rubric (`HBB_SEALED_GPT_RUBRIC_V2`,
SHA-256 `012941aba485f33b8328b7e5cba2a84b5c1db82119bb96554bc8dea84f4f9f17`) that scores every answer on **two
independent axes** — DETECTION and RECONSTRUCTION — with arm anonymized, incident order shuffled, mixed batch.
**Hash verification = VERIFIED**: reproduced exactly by `sha256(json.dumps(rubric, sort_keys=True,
separators=(",",":")))` (canonical sorted-compact JSON). Files: `experiments/HBB_GPT_rubric_v2_frozen.json`,
`experiments/HBB_GPT_v2_scores.json`, `docs/HBB_GPT_v2_report.md`.

**Instrument change.** Single-axis Reach (the §B Independent-Hint-Sufficiency depth) is **removed from
load-bearing status**; reach/complementarity is now scored on the two-dimension split
(`DETECTION_RECONSTRUCTION_SPLIT`, permanent instrument #5), composed with `MULTI_SCORER_CONSENSUS`
(claim only what is robust across scorers AND across both axes).

### H0 / free response (GPT rubric-v2)
| Arm | DET mean | RECON mean | D=2 | R=2 |
|---|---:|---:|---:|---:|
| A | 0.818 | 0.182 | 1 | 1 |
| B | **1.455** | 0.545 | 5 | 1 |
| F | 0.545 | 0.000 | 0 | 0 |
| C | 0.636 | 0.273 | 2 | 1 |
| D | 1.000 | 0.455 | 4 | 2 |

### All four independent hint rungs pooled (answer-level)
| Arm | DET mean | RECON mean | D=2 | R=2 |
|---|---:|---:|---:|---:|
| A | 0.909 | 0.273 | 9 | 3 |
| B | 1.000 | 0.364 | 12 | 4 |
| F | 0.523 | 0.045 | 1 | 1 |
| C | 0.773 | 0.364 | 10 | 6 |
| D | **1.068** | **0.523** | 15 | 9 |

### Verdict updates (supersede §I framing on the two-dimension instrument)
- **SUSPENDED "engine < B" → REJECTED.** B leads H0 DETECTION (1.455) but D is competitive, and on pooled
  RECONSTRUCTION D (0.523) is the highest of any arm. The engine is not simply weaker.
- **SUSPENDED "engine > B" → REJECTED.** At H0 free RECONSTRUCTION, C (0.273) and D (0.455) do not cleanly
  exceed B (0.545); the preregistered C-unique/D-unique AA claim stays unsupported.
- **SUPPORTED: "B is a strong H0 detection gate but does not substitute for reconstruction."** The largest
  signal in the re-score is the DETECTION→RECONSTRUCTION drop, steepest for B (1.455 → 0.545). Reconstruction
  is a distinct stage that **no arm reliably completes**.
- **`C-unique = D-unique = 0` MAINTAINED** across all three scorers (Claude strict / Qwen blind / GPT
  rubric-v2). H_primary **NOT_CONFIRMED still holds**. Hard-core (HBB-03 return-to-substrate, HBB-08, HBB-11)
  reached by no arm on reconstruction.

### Provenance / deviations (preserved, not deleted)
GPT `deviation_log` is kept verbatim in `HBB_GPT_v2_scores.json`: rubric frozen before raw-file open; after
freeze, file-search exposed some arm labels so **human-level arm blindness is not pristine** (the scoring
function itself receives incident_id + answer text only, never arm); the incident historical-equivalence
`target_map` was formalized after raw access (procedural deviation); ALT_UNTESTED emitted as CANDIDATE only.
These are recorded as over-claim brakes, not hidden.

**HBB-30** is added as a T0 packet with provenance `USER_ATTESTED_HISTORICAL_RECONSTRUCTION`
(`experiments/HBB-30_T0_GPT_user_attested.json`) — distinct from source-extracted T0, anchored on Taka's
2026-07-08 attestation plus the surviving "~6x ternary vs binary" claim. Claude remains excluded from scoring
HBB-30/04 (当事者); the packet is standalone and is **not** merged into the locally-scored `hbb_sealed_t0.json`
packets.

**Next design step (proposal only, awaiting Taka).** Because DETECTION ≫ RECONSTRUCTION across all arms, the
reconstruction stage is proposed as an **independent function** — see
`docs/hbb_reconstruction_stage_proposal.md` (status PROPOSAL / AWAITING_TAKA; not implemented). External
handoffs still open: GPT/Claude raw-API arm, GPT T0 scoring of HBB-04/30, independent cross-review.
