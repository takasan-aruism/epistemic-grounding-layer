"""Real-repo energization minter (Taka 2026-07-18 §2-B).

Mints a real _EnergizedApply ONLY when EVERY gate holds; otherwise raises MintRefused (fail-closed):
  (1) a real ENERGIZATION_ADJUDICATION event EXISTS in the injected event log and matches this exact request
      (existence-verification of a record, NOT a flag/config);
  (2) authority == Taka: authority_owner == 'TAKA' AND granted_by == 'TAKA' AND attribution is NOT self-/
      model-authored (self-energization refused). OS-level Taka impersonation is NOT defeatable at this layer
      alone -> documented residual risk (design doc (b)); this layer refuses the self/LLM attributions it can see;
  (2') the adjudication binds the SAME per-patch content as the request (item_id/repo/base_commit/fingerprint/
      allowed_files). A different patch => no match => re-adjudication required. item_id alone can never energize;
  (2'') not revoked (ENERGIZATION_REVOCATION referencing the adjudication_id) and not expired;
  (3) the reconciler proves a FRESH balance (bridge_reconciler.latest_balance_proof), and that proof is for the
      request's base_commit. None/imbalanced/stale => refuse (energization presupposes reconciliation);
  (BIND-3) single-use: the token_id must NOT already appear in a PATCH_APPLICATION event (consumption is DERIVED
      from the SoR log, not a separate consumption ledger -> DE-0006 consistent).

The minted token binds ALL fields (item_id/task_id/trace_id/repo identity/base_commit/allowed_files/fingerprint/
expiry/token_id/adjudication ref). The bridge write primitive additionally enforces the per-patch binding
(fingerprint/base_commit/allowed_files) at apply time, so the binding is STRUCTURAL, not advisory.

Scope note: this module READS adjudication events; it has NO code to WRITE them. Wiring the adjudication-event
WRITER to Taka (design doc options B1-B4) and any REAL-repo apply are OUT OF SCOPE of this directive (post-report
Taka adjudication). This module is verified only against throwaways. No self-energization, no self-promotion.
"""
import os
from patch_bridge import _EnergizedApply
import bridge_reconciler as rc

# attributions that are NOT Taka -> refuse (self-energization / model-authored adjudication)
_FORBIDDEN_ATTRIB = frozenset({'SELF', 'LLM', 'CLAUDE', 'AGENT', 'AUTO', 'MODEL',
                               'BRIDGE', 'RECONCILER', 'MINTER', 'SYSTEM'})

_REQUIRED_REQUEST_KEYS = ('item_id', 'task_id', 'trace_id', 'repo_identity', 'repo_realpath',
                          'base_commit', 'allowed_files', 'fingerprint', 'token_id', 'adjudication_id')

# per-patch fields that the adjudication event MUST match the request on (patch changes => re-adjudicate)
_BIND_MATCH = ('item_id', 'repo_realpath', 'base_commit', 'fingerprint')


class MintRefused(Exception):
    pass


def _p(e):
    return e.get('payload') or {}


def _find_adjudication(event_log, adjudication_id):
    for e in event_log:
        if e.get('kind') == 'ENERGIZATION_ADJUDICATION' and _p(e).get('adjudication_id') == adjudication_id:
            return e
    return None


def _is_revoked(event_log, adjudication_id):
    for e in event_log:
        if e.get('kind') == 'ENERGIZATION_REVOCATION' and _p(e).get('adjudication_id') == adjudication_id:
            return True
    return False


def _token_id_consumed(event_log, token_id):
    # [BIND-3] single-use consumption == token_id present in a PATCH_APPLICATION event (derived from the SoR).
    for e in event_log:
        if e.get('kind') == 'PATCH_APPLICATION' and _p(e).get('token_id') == token_id:
            return True
    return False


def mint_real_energize(request, event_log, repo_dir, now_ts=None):
    """Return an _EnergizedApply bound to every field of `request`, or raise MintRefused (fail-closed)."""
    # request completeness
    for k in _REQUIRED_REQUEST_KEYS:
        if not request.get(k):
            raise MintRefused('request missing/empty %r' % k)

    # repo identity must match the actual dir (grant-binding precondition the bridge enforces)
    real = os.path.realpath(repo_dir)
    if request['repo_realpath'] != real:
        raise MintRefused('repo_realpath != realpath(repo_dir)')

    # (1) adjudication event must exist
    adj = _find_adjudication(event_log, request['adjudication_id'])
    if adj is None:
        raise MintRefused('no ENERGIZATION_ADJUDICATION event for adjudication_id')
    ap = _p(adj)

    # (2) authority == Taka; reject self-/model-attributed. FAIL-CLOSED ALLOWLIST (JREV-0010): attribution
    # must be PRESENT and exactly 'TAKA' -- an absent/empty attribution no longer passes (a blocklist let an
    # unattributed Taka-claiming event through). granted_by/authority_owner are additionally required == TAKA.
    if str(ap.get('authority_owner', '')).upper() != 'TAKA':
        raise MintRefused('authority_owner != TAKA')
    if str(ap.get('granted_by', '')).upper() != 'TAKA':
        raise MintRefused('granted_by != TAKA')
    attribution = str(ap.get('attribution', '')).upper()
    if attribution != 'TAKA':
        raise MintRefused('attribution must be TAKA (present + allow-listed), got %r' % ap.get('attribution'))
    if attribution in _FORBIDDEN_ATTRIB:                     # defence in depth (unreachable given allowlist)
        raise MintRefused('self-/model-attributed adjudication refused: %r' % ap.get('attribution'))

    # (2') adjudication binds the SAME per-patch content as the request
    for field in _BIND_MATCH:
        if ap.get(field) != request[field]:
            raise MintRefused('adjudication/request mismatch on %r' % field)
    if list(ap.get('allowed_files') or []) != list(request['allowed_files']):
        raise MintRefused('adjudication/request allowed_files mismatch')

    # (2'') not revoked, not expired
    if _is_revoked(event_log, request['adjudication_id']):
        raise MintRefused('adjudication revoked')
    expiry = ap.get('expires_at')
    if not expiry:
        raise MintRefused('adjudication has no expiry (fail-closed)')
    if now_ts is not None and str(now_ts) > str(expiry):
        raise MintRefused('adjudication expired')

    # (3) reconciler pull-type freshness: a fresh balanced proof for THIS base_commit ...
    proof, fresh = rc.latest_balance_proof(event_log)
    if not fresh:
        raise MintRefused('no fresh reconciler balance-proof (absent/imbalanced/stale)')
    if _p(proof).get('head') != request['base_commit']:
        raise MintRefused('balance-proof head != request base_commit')
    # ... AND do not trust the logged proof blindly (JREV-0010: a forged RECONCILIATION_BALANCED event over an
    # actually-imbalanced tree would otherwise pass). Re-derive the reconciliation independently and require it
    # to agree. This is trust-but-verify of the instrument, consistent with pull-type (the proof is still the
    # interface; the minter just refuses to be lied to).
    pa_events = [e for e in event_log if e.get('kind') == 'PATCH_APPLICATION']
    live = rc.reconcile(repo_dir, pa_events)
    if not live.balanced:
        raise MintRefused('independent reconcile disagrees: tree is imbalanced (forged/stale proof)')
    if live.head != request['base_commit']:
        raise MintRefused('independent reconcile head != request base_commit')

    # (BIND-3) single-use
    if _token_id_consumed(event_log, request['token_id']):
        raise MintRefused('token_id already consumed (single-use)')

    # all gates passed -> bind EVERY field
    return _EnergizedApply(
        grant=real,
        token_id=request['token_id'],
        item_id=request['item_id'],
        task_id=request['task_id'],
        trace_id=request['trace_id'],
        repo_identity=request['repo_identity'],
        base_commit=request['base_commit'],
        allowed_files=tuple(request['allowed_files']),
        fingerprint=request['fingerprint'],
        expiry=expiry,
        adjudication_ref=request['adjudication_id'],
    )
