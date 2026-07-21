# Energization minter — design v0.1 (Taka 2026-07-18 §3 — DESIGN ONLY, NO BUILD)

Status: **design for review**. This document authorizes NOTHING. The real-repo `_EnergizedApply` minter is
NOT built and is NOT authorized to be built by any current directive. Building it is a separate future Taka
gate. Reviewer: GPT (via Taka relay).

## 0. Where we are (as-built, so the design is grounded)

After the §1 core surgery (DE-0418/0419/0421, twoder 0d914e4), a real write through the bridge is structurally
impossible without BOTH tokens at the write primitive:
- `_ValidatedPatch` (content validity: allow-list, base_commit, fingerprint) — minted only by `validate_artifact`.
- `_EnergizedApply` (apply authorization) — bound to `realpath(workspace_dir)`; the writers additionally confine
  each write target within that dir (`_confined_path`, DE-0421).
The ONLY `_EnergizedApply` minter today is the TEST-ONLY `_mint_test_energize`, which issues a token only for a
harness throwaway (resolved path under the OS temp root). **There is ZERO real-repo minter.** This document
designs what a real-repo minter would have to be — and why it must remain unbuilt until Taka builds it.

## (a) Minter firing condition = a real ledger adjudication EVENT (not a flag/config)

A real-repo `_EnergizedApply` may be minted **only if** a Taka adjudication event **actually exists** in the
ledger for the exact target being energized. Concretely:

- New event kind **`ENERGIZATION_ADJUDICATION`** (append-only, in the canonical DESIGN_EVIDENCE / autonomy ledger).
  Fields (proposed): `target_repo`, `target_repo_realpath`, `allowed_files` (or scope selector, see (c)),
  `base_commit_pin` (optional), `granted_by`, `granted_at`, `expires_at` (see (d)), `adjudication_id`, `nonce`.
- The minter reads the ledger and **verifies the event's existence and match** (target realpath == the requested
  workspace realpath; not expired; not revoked — see (d)). **Absent/มismatched/expired event ⇒ the minter raises;
  a token is un-mintable.** This is existence-verification of a real record, NOT a boolean flag or a config value
  (a flag can be flipped; a missing event cannot be faked into existence without writing the ledger, which (b) locks
  to Taka).
- The minted token binds to `realpath(target_repo)` exactly as the test minter does, so the write primitives'
  existing grant-binding + `_confined_path` apply unchanged.

## (b) Restricting the adjudication event's WRITER to Taka — options + honest residual risk

The security reduces to: **who can append an `ENERGIZATION_ADJUDICATION` event?** The root of trust moves from
"who can mint a token" to "who can write the adjudication event." A move table (root → what guards it):

| Option | Root of trust | Guard | Honest residual risk |
|---|---|---|---|
| **B1. Signature** | a Taka-held private key; the event carries a signature the minter verifies with a pinned public key | crypto | key management (theft/loss); the pinned pubkey must itself be write-protected; whoever can edit the pinned pubkey can forge — moves the problem, doesn't remove it |
| **B2. OS write-permission** | the ledger file is writable only by a Taka-controlled uid; the autonomous process runs as a different uid with no write access to the adjudication log | filesystem perms | anything running as Taka's uid (or root) can write; a bug that runs bridge code as Taka's uid defeats it; append-only-fs (chattr +a) hardens but ops-fragile |
| **B3. Out-of-band channel** | the event is injected by a Taka-only path (e.g. a manual CLI Taka runs, never called by the autonomous flow) | process separation | the autonomous flow must have NO code path that calls the injector; requires the "no minter reachable from the flow" AST discipline extended to the injector; a smuggled call defeats it |
| **B4. Two-person / co-sign** | two independent principals must both append/sign | redundancy | collusion; both principals being the same weight (not truly independent) — the JREV weight-separation lesson applies |

**No option is a complete solution and this document does not claim one.** The realistic posture: **B2 (OS write-
perms, append-only) as the base, optionally + B1 (signature) for tamper-evidence**, with the honest residual that
"whoever controls Taka's uid / the pinned key controls energization." The choice of where to accept residual risk
is a **Taka adjudication**, not something this design should decide.

## (c) Energization scope control — comparison

| Scope | Grant | Pros | Cons |
|---|---|---|---|
| **Full** (any repo) | one event energizes all writes | simple | largest blast radius; a single bad event = unrestricted write; NOT recommended |
| **Per-repo** | event names `target_repo_realpath`; token binds to it (matches the current grant-binding) | matches the built dir-binding; blast radius = one repo | one event per repo; still whole-repo within allowed_files |
| **Per-item** | event names repo + a specific item/change id + `base_commit_pin` + tight `allowed_files` | smallest blast radius; each energization is one adjudicated change | most events; needs an item identity carried from the flow to the adjudication |

Recommendation for first real energization: **per-item** (or per-repo with a tight `allowed_files` + `base_commit_pin`),
never Full. The write primitives already enforce `allowed_files` + apply-time `_confined_path` + fingerprint, so a
tight per-item event is well-supported by the as-built core.

## (d) Revocation / expiry — fail-closed

- Every adjudication event carries `expires_at`; the minter refuses to mint after it (time-boxed energization).
- A **`ENERGIZATION_REVOCATION`** event (referencing an `adjudication_id`) **immediately** invalidates it: the
  minter must check "no revocation for this adjudication_id exists" at mint time, AND the reconciler (e) must
  treat a revocation as an immediate de-energization trigger. Fail-closed: any doubt (event unreadable, clock
  unavailable, revocation ambiguous) ⇒ refuse to mint / de-energize.

## (e) Reconciler chapter (differential to the §2 inventory)

Per the §2 inventory, the only BUILT standing double-entry mechanism is LAYER-3 (build-time); there is no standing
reconciler over applied patches. This chapter designs the first one.

- **The two independent records** (double-entry, NOT a DE-0006 derivable duplicate): (A) the **target repo's git
  history** (commits, written by git/Taka), and (B) the bridge's **`PATCH_APPLICATION` events** (written by the
  bridge at apply/rollback time, DE-0402). Neither is derived from the other.
- **Bidirectional reconciliation**: for each `PATCH_APPLICATION`(APPLIED) event there must exist a corresponding
  commit whose content hash matches the event's fingerprint (and whose base is the event's base_commit); and for
  each commit within the energized scope there should exist a corresponding event. **An orphan on either side =
  imbalance** (a write that git shows but the bridge didn't record, or an event with no matching commit).
- **Deterministic, LLM-free (absolute)**: the reconciler is plain code (git plumbing + event read + hash compare).
  No model is in the loop — a reconciler that "judges" is not a reconciler.
- **Imbalance ⇒ immediate automatic de-energization (fail-closed)**: on detecting any orphan/mismatch, the
  reconciler emits an `ENERGIZATION_REVOCATION` (or equivalent) that the minter honors — subsequent minting is
  refused until the imbalance is adjudicated. This is the "an unbalanced ledger freezes the account" discipline.
- **State-based activation (energization gated on the reconciler running)**: an `_EnergizedApply` is valid only
  while the reconciler is demonstrably live and balanced. Proposed: the minter's (a) existence check ALSO requires
  a recent reconciler "balanced" heartbeat/attestation (itself a ledger record, deterministic), so that if the
  reconciler is not running, energization is not available. Energization presupposes reconciliation.

## (f) Appendix — throwaway-first real apply procedure

Before any energized apply touches a canonical repo: (1) clone/copy the target repo into a throwaway dir under the
OS temp root; (2) energize + apply there (the test minter already covers throwaway dirs; a real-repo apply reuses
the same write primitives); (3) run the target repo's own tests + the reconciler on the throwaway; (4) only after
green + balanced does a Taka-adjudicated event authorize the same apply against the canonical repo. This keeps the
first real writes reversible and observed. (Procedure only — not authorized here.)

## (g) Explicit non-goals

- This document is **NOT a build authorization**. No minter, no event kind, no reconciler is built.
- It does **NOT include racing** (DE-0389/0396 remain frozen).
- It does **NOT include a claim-ceiling promotion**: the ceiling stays BOUNDED_PATCH_BRIDGE (sandbox) until a
  separate post-build, post-throwaway-E2E Taka adjudication. No self-energization, no self-promotion.
