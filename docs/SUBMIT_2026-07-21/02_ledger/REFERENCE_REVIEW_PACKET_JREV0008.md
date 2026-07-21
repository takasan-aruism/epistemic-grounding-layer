# REVIEW PACKET — JREV-0008: bridge_apply_connector + _EnergizedApply (weight-separated review)

**Scope:** the non-conducting live caller of the bounded patch bridge — `bridge_apply_connector` +
`_EnergizedApply` — as committed in `twoder/patch_bridge.py` (commit 70c71a2 / harness commit b5ec156;
module sha256 `bb4d4f38003036f8`, 246 lines). This code is **Claude Code direct-authored (disclosed glue,
DE-0413)**, so per Taka 2026-07-18 §1 an independent weight-separated review is a **precondition of any
energization adjudication**.

- **Author:** Claude Code (this session). **Attacker:** local agent (separate principal; real attacks,
  throwaway copy only). **Adjudicator:** GPT (independent; Taka relays). Three separate principals.
- **Claim ceiling under review:** BOUNDED_PATCH_BRIDGE (sandbox), **NON-CONDUCTING**. Energization is a
  separate Taka gate (not authorized). This review does NOT authorize energization, apply, or promotion.

---

## 1. As-coded facts (the exact surface under review)

```python
@dataclass(frozen=True)
class _EnergizedApply:
    grant: str

def bridge_apply_connector(energize_token, workspace_dir, artifact, allowed_files, provenance, recorder, task_id, ts):
    if not isinstance(energize_token, _EnergizedApply):
        return {'applied': False, 'blocked': 'NOT_ENERGIZED',
                'reason': 'no _EnergizedApply token (energization is a separate Taka gate)'}
    expected_fp = canonical_diff_artifact(artifact['diff'], artifact['base_commit'])['fingerprint']
    validated = validate_artifact(artifact, allowed_files, provenance.base_commit, expected_fp)
    check_diff_within_allowed(validated.diff, provenance.allowed_files)
    result = apply_patch_bounded(workspace_dir, artifact, allowed_files, recorder, task_id, ts,
                                 expected_base=provenance.base_commit, expected_fingerprint=expected_fp)
    return {'applied': True, 'result': result}
```

Collaborators it calls (all committed in the same module):
- `canonical_diff_artifact(diff_text, base_commit)` → recomputes the fingerprint (integrity root for the diff body).
- `validate_artifact(artifact, allowed_files, expected_base, expected_fingerprint)` → mints `_ValidatedPatch`;
  rejects on allow-list / base_commit / fingerprint mismatch.
- `check_diff_within_allowed(diff_text, allowed_files)` → apply-time scope check on the ACTUAL `+++ b/` paths.
- `apply_patch_bounded(...)` → validate → capture_preimage → `_apply_to_working` (sole writer) with rollback + event.
- `capture_provenance(target_repo_dir, allowed_files)` → the `_Provenance` root (base_commit git-read; fail-closed).

## 2. Root of trust (what decides "whether it fires" and "what it may touch")

| Property | Root | How the root is protected |
|---|---|---|
| **Firing (conduction)** | a genuine `_EnergizedApply` token passed to `energize_token` | **NO module function mints `_EnergizedApply` (AST-verified, 0 minters).** The autonomous flow has no path to obtain one → cannot conduct. Energization = a future Taka-gated minter (not built). |
| **What may be written** | `provenance.allowed_files` + apply-time `check_diff_within_allowed` on the real diff paths | `_Provenance` minted only by `capture_provenance`; `allowed_files` is caller-supplied (trust boundary = the caller); the apply-time check re-derives paths from the diff body, not a declaration. |
| **Which base** | `provenance.base_commit` (git-read inside `capture_provenance`, never an argument) | worker/LLM output cannot supply/forge base_commit. |
| **Diff integrity** | `expected_fp = canonical_diff_artifact(artifact['diff'], ...)['fingerprint']` recomputed from the body | validate_artifact then requires `artifact['fingerprint'] == expected_fp`; a tampered body → mismatch → reject (DE-0413 fix). |
| **Sole writer** | `_apply_to_working` (via apply_patch_bounded) | un-callable without a `_ValidatedPatch`; DE-0349 structural gate. |

## 3. Declared holes (author-disclosed; attacker must probe these + beyond)

1. **Token forge by direct construction.** `_EnergizedApply(grant=...)` can be constructed by any *caller* that
   chooses to. The non-conduction guarantee is scoped to the **autonomous flow** (which never constructs it),
   NOT to a caller that deliberately builds one — that IS energization, which is a separate Taka gate. The
   review question: can the autonomous flow reach a construction site *without* an explicit Taka-gated minter?
2. **`allowed_files` trust boundary.** `capture_provenance` takes `allowed_files` as an argument; its integrity
   depends on the caller passing a trusted list (not a worker/LLM-derived one). base_commit is git-read (safe);
   allowed_files is the softer edge. Backstop: apply-time `check_diff_within_allowed`.
2b. **Connector is Claude-direct-authored** (worker non-convergence + DE-0417 harness signal issue). No worker
   provenance; correctness rests on the oracles + §4 gate + this review.
3. **Skip path shape.** The no-token branch returns a dict (never raises) so it is a safe no-op in the live
   flow. Probe: can a partial side effect occur *before* the token check, or can the skip be made to look like
   an apply?

## 4. Attack checklist (minimum — attacker runs REAL attacks in a throwaway copy)

- **A. token forge / minter-add:** find ANY path where the autonomous flow (module functions only, no explicit
  hand-construction) obtains an `_EnergizedApply`; attempt to add a minter that evades the AST 0-minter check
  (dynamic construction: `type(...)`, `_EnergizedApply.__new__`, dataclasses.replace, copy, pickle, eval).
- **B. fingerprint recompute bypass / tampered-diff retry:** get a tampered diff (body ≠ fingerprint) applied
  via the connector; try to make `canonical_diff_artifact` recompute to the stale fingerprint; canonicalization
  collisions.
- **C. skip-path abuse:** make the no-token branch perform or leak a partial write; make a blocked call look applied.
- **D. provenance mismatch:** pass a `_Provenance` with `allowed_files` that doesn't match the diff; empty/degenerate
  provenance; provenance for a different base_commit; escape allowed_files via path tricks (`./`, `../`, symlink,
  absolute path in `+++ b/`).
- **E. non-conducting bypass (all systems):** any way to reach `apply_patch_bounded` / `_apply_to_working` /
  `_restore_preimage` without a genuine token AND without going through the gate.
- **F. §4 re-run:** the 4 counterfactual injections must remain ALL-BLOCKED on the reviewed bytes.

## 5. Verification obligations at review close

- Re-measure **0 `_EnergizedApply` minters** on the COMMITTED module (AST).
- Re-run the **§4 gate** on the reviewed bytes → ALL-BLOCKED.
- Attacker energization attempts confined to a **throwaway copy**; committed module untouched.
- In-scope fixes (connector + its direct tests) authorized (DE-0413 procedure); out-of-scope defect → S-6, ticket only.
- Two-stage record preserved (pre/post); raw attacker output referenced, not editorially rewritten.
