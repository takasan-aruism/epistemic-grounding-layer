# PREREG — Minimum HBB-Exhibit → EGL Unresolved Bridge v0.1 (to be FROZEN/HASHED)

Freezes spec `hbb_egl_bridge_spec_v0.1.md`, binding `hbb_egl_bridge_binding_v0.1.json`, offline-replay contract
`hbb_egl_bridge_offline_replay_contract_v0.1.json`, test plan `hbb_egl_bridge_test_plan_v0.1.md`. **Wiring
feasibility only.** Not solving HBB-30; no REC2; Attention Center / same-object binding / Aruism / structural
re-centering remain UNOWNED and unbuilt. C≠H.

## Frozen question
Can HBB/exhibit intermediate material be handed to the existing live EGL `answer_question` contract to expose an
answer candidate **and** unresolved material to the user simultaneously, **without changing the normal reasoning
path** and **without the bridge holding any authority**?

## Frozen boundary
- SOURCE: `scheduler_exhibit_candidates.json:records[].candidates` (persisted rebuild text; HBB-30 = 40 records
  / 240 candidates).
- TARGET: `egl/self_grounding.py answer_question(question, records=…, system=NEUTRAL, k=len(records))` +
  `validate_answer`.
- ADAPTER: `candidate str → {record_id, source_class="HBB_EXHIBIT_INTERMEDIATE", ordinal, text (byte-identical),
  provenance}`. Format + provenance only; **no** semantic verdict.

## Frozen reach (honest)
- Populates: `answer_claims`, `open_gaps` (+ historical_claims, source_trace), grounded by validate_answer M1.
- Does NOT populate: `status`, `validation_mode`, `non_guarantees` (curation/DW paths, out of scope).
- Does NOT create a Claim; does NOT call `apply_outcome`/`gates.decide`; does NOT hand-write `open_gaps`.

## Frozen authority invariants (all must hold; any failure ⇒ INVALID)
generated ≠ validated · retained ≠ evidence · open_gap ≠ false premise · UNRESOLVED ≠ rejection ·
REPORTED/DECLARED unchanged · SUPERSESSION unchanged · answer authority unchanged · user final authority.

## Frozen normal-path isolation
No classifier / heuristic / always-on observer added to the ordinary EGL question path (T8). The bridge is an
explicit adapter invoked from the HBB/exhibit side only.

## Frozen offline replay pins (DE-0132; no self-reference)
`scheduler_exhibit_candidates.json` = `b7c98296a3249ec86a73d9341a1975e863dfa800ec735b5d8672d4a4d032c74b`;
HBB-30 subset = `9e1ca25b1f060109b9b340b008056e99f87822cc6015a1334487737b9a4f49d2`; t0_stuck_frame =
`bc09d36ddfbcdb99fdc38adfa61477e33a7a489b88d64c3c4dc5c5f466db7ea0`. Corpus = ONLY exhibit material (never EGL
ledgers). k = n fed records (no silent drop).

## Frozen test set
T1 content identity · T2 provenance preserved (parent_ref not fabricated) · T3 no semantic verdict · T4 no
bypass (answer_question+validate_answer used) · T5 open_gaps reachable · T6 answer_claims coexists · T7 no
auto-reject · T8 normal path unchanged · T9 no rubric vocabulary · T10 no self-reference.

## Frozen verdict rule (post-audit / post-replay)
- **BRIDGE DESIGN INVALID** if any of T3/T4/T9/T10 fails by design, any authority invariant is unheld, or the
  adapter must judge/adjudicate to work.
- **BRIDGE DESIGN VALID** if the design binds 1:1 to existing code, holds all invariants, uses the answer
  contract without bypass, and the offline replay is feasible with ~30–50 LOC + 1 existing-mechanism call.
- **AUDIT REQUIRED / UNKNOWN** otherwise.

## Frozen claim ceiling
positive ⇒ "HBB/exhibit intermediate material can be wired to the live EGL answer contract to co-expose answer +
unresolved to the user, normal path unchanged, bridge authority-free." **NOT:** HBB-30 solved · REC2 · Attention
Center · same-object binding · structural re-centering · Aruism. C≠H.

## Run order (gated)
freeze/hash (this doc) → **independent construct audit** → **STOP + report** (no implementation, no run, no
commit this round). Implementation + offline replay separately gated on audit PASS + user go.
