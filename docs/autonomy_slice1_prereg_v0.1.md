# PREREG / implementation contract — SLICE-1 mechanical CURRENT_STATE builder v0.1

**class:** AUTO-NOW (reversible mechanical scaffold). **authority:** none. **rollback:** delete `CURRENT_STATE.json` / `git revert`.
**claim ceiling:** produces a machine-derived state projection with honest origin tags. **NOT** an evidence promotion, NOT a status change, NOT autonomous decision-making. self-improvement claim なし. C≠H.

## Frozen contract
- module `autonomy/current_state.py` exposes `build_current_state() -> dict` that is **side-effect-free** (reads repo files, writes nothing).
- CLI `autonomy/build_state.py` writes the dict to `CURRENT_STATE.json` (the only write; a regenerable/deletable projection).
- **read-only invariant:** the builder MUST NOT write to `DESIGN_EVIDENCE_LEDGER.jsonl`, `data/events.jsonl`, `data/state.sqlite`, any `egl/*` state, or any seal/spec file. Only `CURRENT_STATE.json` (via CLI).
- **origin honesty invariant:** every top-level data field appears in `field_origins` with origin ∈ {MECHANICAL, CLAUDE-DERIVED, TAKA-OWNED}. A field derived by keyword-heuristic (e.g. `closed_branches`) MUST be tagged CLAUDE-DERIVED, never MECHANICAL.
- **no-fabrication invariant:** the builder does not invent status; it reports parsed facts + explicitly-tagged heuristics. Unverifiable seals → status `UNVERIFIABLE` (not `OK`).
- **totality invariant:** malformed/missing input files do not crash the builder (per C-TOTALITY discipline); they degrade to empty/error-tagged fields.

## Fields (origin)
`as_of`(MECHANICAL) · `latest_de`,`n_de_entries`(MECHANICAL) · `de_index`(MECHANICAL) · `seals`(MECHANICAL, sha256 recompute) · `component_files`(MECHANICAL) · `component_class_heuristic`(CLAUDE-DERIVED) · `closed_branches`(CLAUDE-DERIVED heuristic) · `unowned_constructs`(CLAUDE-DERIVED, from spec §2.8) · `validation_failures`(MECHANICAL) · `spec_staleness`(MECHANICAL) · `authority_pending`(TAKA-OWNED) · `candidate_executable_work`(MECHANICAL subset).

## Tests (`test_autonomy_state.py`, hermetic where possible)
- T1 `latest_de` == last ledger entry's `design_evidence_id`.
- T2 a known-good seal (`hbb_egl_bridge_prereg_seal_v0.2.json`) verifies OK (recomputed prereg hash == stored).
- T3 every field in the state dict (except `field_origins`,`as_of`) has an entry in `field_origins` with a valid origin value.
- T4 determinism: two builds are identical except `as_of`.
- T5 totality: builder does not crash on the real repo; returns a dict.
- T6 read-only: calling `build_current_state()` does not modify ledger/events byte size (sha256 before==after).
- T7 origin-honesty: `closed_branches` origin is CLAUDE-DERIVED (not MECHANICAL).

## Gate
independent audit(author≠auditor)で read-only / origin-honesty / no-fabrication を確認 → VALID なら record + commit。
