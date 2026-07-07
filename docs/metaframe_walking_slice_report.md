# Meta-Frame Factory — Walking-Slice Report (narrow, outcome-neutral)

Spec v0.3 §33. Date 2026-07-07. Pilot N=5 held-out. Interpreted against the preregistration
(docs/metaframe_preregistration.md), fixed before results. **Not** a re-summary of ESDE history.

## A. Corpus inspection
`/docs/概念理解.md` = 3363 lines / 318 KB. Rich narrative incidents in v9.11–v9.18 (lines 1312–2677);
v10+ are mostly 教訓 lists. 51 教訓 sections / 162 numbered lessons. Sampling: phase-narrative chunks,
**教訓 sections excluded** from the extractor for blindness.

## B. Ownership implementation
DD-ARCH-6 (DE-0088): EGL owns meta-frames + currentness (metaframe_ledger.jsonl); RRI applies (not
run this slice); DW = the extraction/induction/transfer experiments; DS/Director ref-only. `metaframe.py`
gates 18/18. No parallel epistemic claim SoR.

## C. Gold set
7 Claude-annotated incidents, **SHA-256 5d04b788… sealed before freezing the extraction prompt**,
hidden from Qwen; 5 hypothesized families (ARTIFACT_VS_GROUNDED ×3). **Coupling limitation declared**:
gold builder + pipeline impl both Claude-family (imperfect separation, not called "independent").

## D. Incident extraction
Qwen3.6, frozen prompt e89a0035, 教訓 excluded. 12 candidates over 2 passes. **External-weight audit
(Claude, not same-Qwen-seed): 10 VERIFIED / 2 PARTIAL / 0 REJECTED.** Gold recovery 3/7 (G1 label-purity,
G2 failure-term, G6 dormant-not-delete); the missing gold were mostly v9.17 (chunk-truncation coverage
gap). **No lesson-copy backfill detected** — the blindness (excluding 教訓) worked.
- Good extraction example: INC-11 — a fixed-50-step result read as "self-awareness" → Taka: fixed timing =
  researcher control → artifact (a clean ARTIFACT_VS_GROUNDED incident, recovered independently).
- Field defect: INC-02's `initial_interpretation` was filled with the conclusion (mislabeled, causal chain OK).

## E. Frame-delta reconstruction
Deterministic from VERIFIED incident fields (pre = claim_before; post = added_dimensions/distinctions/
operations + claim_after; decision_effect). 10 frame-deltas. Separate object from raw prose (§10).

## F. Structural clustering (2 views)
Full view + topic-masked view (ESDE nouns → generic tokens). **The masked view is what surfaced the
strongest family** — evidence the cluster is structural, not topical.

## G. Meta-frame candidates (audit §19)
- **MF-M1 "Observer-Subject Decoupling"** [INC-03/10/11/12, 4 incidents, masked-robust] → PROVISIONAL_ACCEPT
  → admitted **MF-001 PROVISIONAL** to EGL (gate-valid, strongest).
- **MF-M2 "Artifact vs. Essence"** [INC-02/07] and **MF-M3 "Arbitrary Anchor vs. Derived"** [INC-01/08]
  → NARROW_DETECTED_UNDERPOPULATED (2 incidents each, gate-rejected <3). **Convergence finding: Qwen
  independently rediscovered the sealed-gold ARTIFACT_VS_GROUNDED family (MF-M2) without seeing gold**
  — but under-populated because v9.17's third instance (gold G3) was not extracted.
- MF-F1 PARTIAL_TOPICAL; MF-F3 REJECT_UNSUPPORTED (muddled).

## H. EGL lifecycle
MF-001 admitted PROVISIONAL, version lineage gate valid (currentness uniqueness holds). Not CURRENT
(pilot, §26). Update-path (§J) exercised below.

## I. Held-out transfer (leak-controlled) — the core result
5 held-out incidents (4 TIER-2 operational primitive incidents + 1 ESDE), pre-frames = pre-intervention
only (leak-controlled, hashed). Conditions per preregistration. **HIT = recovered the actual missing axis.**

| condition | HIT/5 | over-trigger | cross-domain misfire |
|---|---|---|---|
| A ordinary Qwen | 2 | 0 | 0 |
| B generic skepticism | 2 | 0 | 0 |
| C lesson memory | 2 | 0 | **1** |
| D verified-incident retrieval | 2 | 0 | **1** |
| **T1 = MF-001 (admitted, observer-subject)** | 2 | **2** | 0 |
| **T2 = MF-M2 (candidate, artifact, under-populated)** | **3** | 0 | 0 |

- **T2 (the artifact family, matching sealed gold) was best (3/5, 0 over-trigger)** and was the only
  condition besides D to recover the *subtle* HO-1 axis (finding reproducibility vs over-flag), where
  A/B gave only severity categorization. → the structural family is real and transfers.
- **But T2 is under-populated (not promotable), and on HO-1 CONTROL D (retrieval) matched it** → per the
  preregistration this reads as **"CONTROL D ≈ TREATMENT: case retrieval may be sufficient (MF-R15)."**
- **T1 (the gate-valid admitted frame) over-triggered on HO-4/HO-5** — forcing observer-subject axes onto
  unrelated GPU/firing-rate questions (**MF-R5 overgeneralized trigger, observed on the promoted frame**).
- **HO-2/HO-3 missing axes are common software instincts** (edge-case coverage / measure the vendor claim)
  → A/B matched T → **"CONTROL B ≈ TREATMENT: prompt effect."**
- **C/D misfired cross-domain on HO-2** (applied ESDE qubit/label/bit-identity concepts literally to a
  software gate) — lesson/incident memory can mis-transfer.

## J. Update-path test
The held-out surfaced two triggers: (1) T1 over-trigger (harmful application on HO-4/HO-5) →
META_FRAME_REVIEW_NEED for MF-001 (narrow its applicability predicate / add disqualifying conditions for
non-observer-subject domains); (2) the artifact family is under-populated → a revision need to add a
third incident (re-extract v9.17 G3). Both are REVIEW_REQUIRED candidates; no in-place mutation — a v2
would be appended. Lineage/currentness authority remains EGL (DD-ARCH-6).

## K. Origin accounting
HUMAN_LESSON (教訓, excluded from extractor) / CORPUS_EXTRACTION (12 candidates) / DERIVED_FROM_INCIDENT
(10 frame-deltas) / INDUCED_FROM_INCIDENT_CLUSTER (6 meta-frame candidates, 1 admitted). No human-origin
laundering (MF-R6 gate + audit).

## L. Narrow conclusion
**NOT DEMONSTRATED** that incident-derived meta-frame *induction* recovers a decision-relevant missing
axis more reliably than ordinary Qwen, generic skepticism, lesson memory, or verified-incident retrieval,
in this pilot (N=5). The best transfer came from an **under-populated, non-promotable** artifact candidate,
and where it helped, **retrieval (CONTROL D) matched it**; the **promoted** frame **over-triggered**.
→ leans "retrieval may be sufficient" + "prompt effect on common-instinct cases."

**Positive signal (not over-claimed):** Qwen independently rediscovered the sealed-gold artifact family
(convergence), and that family uniquely (with retrieval) recovered the subtle HO-1 axis. So a *structural
incident/family memory* may have value — but *induction as a mechanism beating retrieval* is unproven here.
One positive does not become a self-improvement claim (§24). MF-001 stays PROVISIONAL.

## M. Open gaps
- Coverage: v9.17 truncated → artifact family under-populated (the single biggest limiter of this result).
- Promotion threshold: DESIGN_REQUIRED (not invented here); MF-001 stays PROVISIONAL + now REVIEW_REQUIRED.
- Retrieval vs induction: CONTROL D ≈ TREATMENT — a real question about whether induction earns its complexity.
- Over-trigger cost: the promoted frame's harmful over-application (MF-R5) needs an applicability gate before
  any runtime use (§21 not run this slice).
- Gold/pipeline coupling (Claude-family), N=5 pilot, single extractor model — all limit generality.
