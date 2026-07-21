"""Deterministic, LLM-free git <-> PATCH_APPLICATION reconciler (Taka 2026-07-18 §2-A).

Constraints implemented (from the final-build directive):
  [BIND-1] READ-ONLY BY CONSTRUCTION. This module contains NO code that writes git or the working tree
    (no open(...,'w'/'a'/'+'), no os/shutil mutators, no git write subcommands). Every git call routes
    through _git_read, which refuses any subcommand not on the read-only allow-list. The ONLY write this
    module performs is emitting its OWN observation events (RECONCILIATION_*) via an injected recorder.
    Auto-correction of the repo is therefore structurally impossible, not merely disabled.
  [BIND-2] PULL-TYPE. The reconciler leaves only a "latest balance-proof" (RECONCILIATION_BALANCED /
    _IMBALANCED). It issues NO revocation. The minter PULLs the proof (latest_balance_proof); an imbalance
    simply means there is no fresh balanced proof, so the minter fails closed. Freshness is clock-free:
    a proof is fresh iff it is the latest reconciliation event AND no PATCH_APPLICATION was recorded after
    it (i.e. zero unreconciled applies since the proof).
  BOOTSTRAP. reconcile() flags a zero-orphan baseline (no events + clean tree) so a baseline equilibrium
    can be measured BEFORE the first patch apply.
  NOT A 3rd SoR (DE-0423 / DE-0006). This is an INSPECTOR of two INDEPENDENT records -- (A) the repo's git
    working tree (written by git/Taka) and (B) the bridge's PATCH_APPLICATION events (written by the bridge).
    Neither is derived from the other; the reconciler stores only its own verdict and derives nothing
    authoritative. It is not a system of record.

Correspondence (matches the as-built bridge write primitive _apply_to_working, DE-0419): an APPLIED apply
writes canonical diff bytes to each listed file, and sha256(on-disk bytes) == the event's fingerprint. So
an APPLIED event is reflected in git iff each of its files hashes to that fingerprint; a ROLLED_BACK event
means the file was restored (should be clean vs HEAD).
"""
import os
import hashlib
import subprocess
from dataclasses import dataclass

RECON_BALANCED = 'RECONCILIATION_BALANCED'
RECON_IMBALANCED = 'RECONCILIATION_IMBALANCED'
RECON_KINDS = (RECON_BALANCED, RECON_IMBALANCED)

# read-only git plumbing only. Any subcommand outside this set is refused at runtime by _git_read.
_READ_ONLY_GIT = frozenset({'rev-parse', 'status', 'ls-files', 'cat-file', 'rev-list', 'log', 'ls-tree'})


def _git_read(repo_dir, *args):
    """Sole subprocess entry point. Refuses any non-read-only git subcommand (fail-closed)."""
    if not args or args[0] not in _READ_ONLY_GIT:
        raise ValueError('reconciler: refused non-read-only git subcommand: %r' % (args[:1],))
    proc = subprocess.run(['git', '-C', repo_dir, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError('git %s failed: %s' % (args[0], proc.stderr.strip()))
    return proc.stdout


def _head(repo_dir):
    return _git_read(repo_dir, 'rev-parse', 'HEAD').strip()


def _dirty_files(repo_dir):
    """Tracked + untracked working-tree changes vs HEAD/index, via read-only porcelain."""
    out = _git_read(repo_dir, 'status', '--porcelain')
    files = set()
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if ' -> ' in path:            # rename: "old -> new"
            path = path.split(' -> ', 1)[1]
        files.add(path)
    return files


def _file_sha(repo_dir, filename):
    p = os.path.join(repo_dir, filename)
    if not os.path.isfile(p):
        return None
    with open(p, 'rb') as fh:          # read-only
        return hashlib.sha256(fh.read()).hexdigest()


@dataclass(frozen=True)
class ReconResult:
    balanced: bool
    orphans_event_without_git: tuple   # (filename, expected_fp): event says APPLIED, disk doesn't match
    orphans_git_without_event: tuple   # filename: dirty in git, no matching APPLIED event
    baseline: bool                     # True iff zero-orphan clean bootstrap baseline
    head: str
    checked_files: tuple
    applies_seen: int


def _payload(e):
    return (e.get('payload') or {})


def _fold_expected(patch_application_events):
    """Fold PATCH_APPLICATION events -> per-file expected on-disk fingerprint.
    None means the file was reverted (should equal HEAD / be clean)."""
    expected = {}
    for e in patch_application_events:
        p = _payload(e)
        outcome = p.get('outcome')
        fp = p.get('fingerprint')
        for fn in (p.get('filenames') or []):
            if outcome == 'APPLIED':
                expected[fn] = fp
            elif outcome == 'ROLLED_BACK':
                expected[fn] = None
    return expected


def reconcile(repo_dir, patch_application_events):
    """Pure inspection: read git (read-only) + files, fold the event stream, return a verdict. Writes NOTHING.
    Bidirectional orphan detection:
      - event-without-git: an APPLIED event whose file does not hash to the attested fingerprint (or a
        ROLLED_BACK file still dirty) -> the bridge recorded a write git does not reflect.
      - git-without-event: a dirty file not explained by any matching APPLIED event -> git shows a write the
        bridge never recorded (the crucial unrecorded-write case)."""
    head = _head(repo_dir)
    dirty = _dirty_files(repo_dir)
    expected = _fold_expected(patch_application_events)

    ew_git = []
    covered = set()
    for fn, fp in expected.items():
        if fp is None:
            if fn in dirty:                # claimed reverted but git still shows a change
                ew_git.append((fn, None))
            continue
        if _file_sha(repo_dir, fn) == fp:
            covered.add(fn)                # this change is explained by a matching APPLIED event
        else:
            ew_git.append((fn, fp))        # event claims applied; disk bytes disagree

    gw_event = [fn for fn in sorted(dirty) if fn not in covered]

    balanced = not ew_git and not gw_event
    baseline = balanced and not patch_application_events and not dirty
    return ReconResult(
        balanced=balanced,
        orphans_event_without_git=tuple(sorted(ew_git)),
        orphans_git_without_event=tuple(gw_event),
        baseline=baseline,
        head=head,
        checked_files=tuple(sorted(set(expected) | dirty)),
        applies_seen=sum(1 for e in patch_application_events
                         if _payload(e).get('outcome') == 'APPLIED'),
    )


def emit_reconciliation(recorder, task_id, result, ts, identity='bridge-reconciler'):
    """The ONLY write this module performs: its own observation event (BIND-1). Leaves a balance-proof;
    issues NO revocation (BIND-2). Returns whatever the recorder returns."""
    if not isinstance(result, ReconResult):
        raise TypeError('not a ReconResult')
    kind = RECON_BALANCED if result.balanced else RECON_IMBALANCED
    payload = {
        'balanced': result.balanced,
        'baseline': result.baseline,
        'head': result.head,
        'orphans_event_without_git': [list(x) for x in result.orphans_event_without_git],
        'orphans_git_without_event': list(result.orphans_git_without_event),
        'checked_files': list(result.checked_files),
        'applies_seen': result.applies_seen,
    }
    return recorder(task_id, kind, payload, ts, identity=identity)


def latest_balance_proof(event_log):
    """Pull-type freshness for the minter (BIND-2). `event_log` is the merged, append-ordered event log
    (all kinds). Returns (proof_event_or_None, fresh_bool). Fresh iff the latest RECONCILIATION_* event is
    RECONCILIATION_BALANCED AND no PATCH_APPLICATION appears AFTER it (clock-free freshness cap = zero
    unreconciled applies since the proof). Absent/imbalanced/stale -> fresh=False -> minter fails closed."""
    last_recon_idx = None
    for i, e in enumerate(event_log):
        if e.get('kind') in RECON_KINDS:
            last_recon_idx = i
    if last_recon_idx is None:
        return None, False
    proof = event_log[last_recon_idx]
    if proof.get('kind') != RECON_BALANCED:
        return proof, False
    applies_after = any(e.get('kind') == 'PATCH_APPLICATION'
                        for e in event_log[last_recon_idx + 1:])
    return proof, (not applies_after)
