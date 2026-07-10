# PREREG — Minimum HBB-Exhibit → EGL Unresolved Bridge v0.2 (to be FROZEN/HASHED)

Supersedes **v0.1 (AUDIT REQUIRED)**. Freezes spec `hbb_egl_bridge_spec_v0.2.md`, binding
`hbb_egl_bridge_binding_v0.2.json`, offline-replay contract `hbb_egl_bridge_offline_replay_contract_v0.2.json`,
test plan `hbb_egl_bridge_test_plan_v0.2.md`. **Wiring feasibility only.** Not solving HBB-30; no REC2; Attention
Center / same-object binding / Aruism / structural re-centering remain UNOWNED and unbuilt. C≠H.

## Why v0.2 (the 5 audit fixes)
1. **FIX-1 no silent drop** — `retrieve()` appends only `score>0` and `k` does not override it. v0.2 uses the
   existing `force_include=[all record_ids]` (`self_grounding.py:262-267`) and asserts
   `set(retrieved_ids)==set(all_ids)`, logging+failing on any shortfall. No stopword-coincidence dependence.
2. **FIX-2 no self-reference default** — assert `records` is a non-empty list; never `records=None` (would
   default to `load_corpus()` = EGL ledgers, DE-0132).
3. **FIX-3 honest open_gaps** — withdraw v0.1's false "open_gaps grounded by validate_answer M1"; `validate_answer`
   only counts open_gaps. T5 pass = "open_gaps non-empty" only. Grounding, if ever needed, is a separate future
   construct.
4. **FIX-4 supersession** — pass `superseded={}` so `detect_supersession` does not inject tags over HBB text.
5. **FIX-5 call sizing** — 240 candidates ≈ ~48K input tokens; nominal 1 call if context ≥ ~64K, else logged
   per-condition batching (≤4 calls). Verify context at impl.

## Frozen question
Can HBB/exhibit intermediate material be handed to the existing live EGL `answer_question` contract to expose an
answer candidate **and** unresolved material to the user simultaneously, **without changing the normal reasoning
path** and **without the bridge holding any authority**?

## Frozen boundary
- SOURCE: `scheduler_exhibit_candidates.json:records[].candidates` (HBB-30 = 40 records / 240 candidates).
- TARGET: `answer_question(question, records, system=NEUTRAL, k=len(records), force_include=[all ids],
  superseded={})` → assert coverage → `validate_answer`.
- ADAPTER: `candidate str → {record_id, source_class="HBB_EXHIBIT_INTERMEDIATE", ordinal, text (byte-identical),
  provenance}`. Format + provenance only; no semantic verdict.

## Frozen reach (honest)
- Populates: `answer_claims` (source-trace grounded), `open_gaps` (answerer-produced, **NOT** mechanically
  grounded), + historical_claims, source_trace.
- Does NOT populate: `status`, `validation_mode`, `non_guarantees`. Does NOT create a Claim; does NOT call
  `apply_outcome`/`gates.decide`; does NOT hand-write `open_gaps`.

## Frozen authority invariants (any failure ⇒ INVALID)
generated ≠ validated · retained ≠ evidence · open_gap ≠ false premise · UNRESOLVED ≠ rejection ·
REPORTED/DECLARED unchanged · SUPERSESSION unchanged · answer authority unchanged · user final authority.

## Frozen normal-path isolation
No classifier/heuristic/always-on observer on the ordinary EGL question path (T8). Adapter invoked from the
HBB/exhibit side only.

## Frozen offline replay pins (DE-0132; no self-reference)
candidates `b7c98296a3249ec86a73d9341a1975e863dfa800ec735b5d8672d4a4d032c74b`; HBB-30 subset
`9e1ca25b1f060109b9b340b008056e99f87822cc6015a1334487737b9a4f49d2`; t0_stuck_frame
`bc09d36ddfbcdb99fdc38adfa61477e33a7a489b88d64c3c4dc5c5f466db7ea0`. Corpus = ONLY exhibit material. records =
non-empty list (never None). Coverage asserted via retrieved_ids.

## Frozen test set
T1 identity · T2 provenance · T3 no verdict · T4a no bypass · **T4b coverage (FIX-1)** · T5 open_gaps non-empty
(FIX-3) · T6 answer_claims coexists · T7 no auto-reject · T8 normal path unchanged · T9 no rubric · T10 input
no-live-ledger · **T11 no self-reference default (FIX-2)** · **T12 no supersession bleed (FIX-4)**.

## Frozen verdict rule
- **BRIDGE DESIGN INVALID** if any of T3/T4a/T4b/T9/T10/T11/T12 fails by design, any authority invariant unheld,
  or the adapter must adjudicate to work.
- **BRIDGE DESIGN VALID** if the design binds 1:1 to existing code, holds all invariants, uses the answer
  contract without bypass, provably feeds all records, and the offline replay is feasible with ~30–65 LOC + 1
  existing-mechanism call (≤4 if context-batched, logged).
- **AUDIT REQUIRED / UNKNOWN** otherwise.

## Frozen claim ceiling
positive ⇒ "HBB/exhibit intermediate material can be wired to the live EGL answer contract to co-expose answer +
unresolved to the user, normal path unchanged, bridge authority-free." **NOT:** HBB-30 solved · REC2 · Attention
Center · same-object binding · structural re-centering · Aruism · open_gaps grounded. C≠H.

## Run order (gated)
freeze/hash (this doc) → **independent re-audit** → **STOP + report** (no implementation, run, or commit this
round). Implementation + offline replay separately gated on audit PASS + user go.
