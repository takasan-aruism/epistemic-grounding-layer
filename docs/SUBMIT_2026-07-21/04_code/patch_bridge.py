import os
import hashlib
from dataclasses import dataclass

@dataclass(frozen=True)
class _ValidatedPatch:
    diff: object
    filenames: tuple
    base_commit: str
    fingerprint: str

def validate_artifact(artifact, allowed_files, expected_base='abc', expected_fingerprint='hash'):
    if not isinstance(artifact, dict):
        raise ValueError('artifact must be a dict')

    tokens = artifact['diff'].split()
    filenames = tuple(t[2:] for t in tokens if t.startswith('a/') or t.startswith('b/'))

    for fname in filenames:
        if fname not in allowed_files:
            raise ValueError(fname)

    if artifact['base_commit'] != expected_base:
        raise ValueError('base_commit')

    if artifact['fingerprint'].lower() != expected_fingerprint.lower():
        raise ValueError('fingerprint')

    return _ValidatedPatch(
        diff=artifact['diff'],
        filenames=filenames,
        base_commit=artifact['base_commit'],
        fingerprint=artifact['fingerprint']
    )

@dataclass(frozen=True)
class _EnergizedApply:
    grant: str
    token_id: str = None
    item_id: str = None
    task_id: str = None
    trace_id: str = None
    repo_identity: str = None
    base_commit: str = None
    allowed_files: tuple = ()
    fingerprint: str = None
    expiry: str = None
    adjudication_ref: str = None

def _mint_test_energize(workspace_dir):
    """TEST-ONLY energization minter (Taka 2026-07-18 §1-1) — the ONLY sanctioned _EnergizedApply source in
    this module. It issues a token bound to workspace_dir ONLY IF that dir is a harness-generated throwaway,
    verified mechanically: the REAL (symlink-resolved) path must live under the OS temp root. Canonical repos
    live outside the temp root (e.g. /home/takasan/*), so a real repo — passed directly OR via a symlink under
    /tmp — resolves outside the temp root and is REFUSED (attack (g) blocked). (A throwaway clone under /tmp
    that carries its own .git is legitimately throwaway and is allowed; the temp-root test, not a .git test, is
    the throwaway discriminator.) There is NO real-repo minter here; that is a §3 design + Taka gate. The
    token's grant = the authorized realpath, so a token minted for one throwaway cannot authorize a write to
    any other dir (the writers enforce grant == realpath(workspace_dir) via _require_energize)."""
    import tempfile
    real = os.path.realpath(workspace_dir)
    tmproot = os.path.realpath(tempfile.gettempdir())
    if not (real == tmproot or real.startswith(tmproot + os.sep)):
        raise ValueError('not a throwaway (resolved path outside temp root): %s' % real)
    return _EnergizedApply(grant=real)

def _require_energize(workspace_dir, energize):
    """Structural energization gate for EVERY write-reaching path (DE-0418, choice 1). A write is impossible
    without a genuine _EnergizedApply whose grant authorizes THIS workspace_dir."""
    if not isinstance(energize, _EnergizedApply):
        raise TypeError('not an _EnergizedApply (write requires energization)')
    if energize.grant != os.path.realpath(workspace_dir):
        raise ValueError('energize token does not authorize this workspace_dir')

def _confined_path(workspace_dir, filename):
    """DE-0420 (JREV-0009): the dir-binding must confine the write TARGET, not just the root. Resolve the
    write path and require it to stay within realpath(workspace_dir); a '../'/symlink target that escapes
    the energized dir is refused. Returns the path to open."""
    root = os.path.realpath(workspace_dir)
    resolved = os.path.realpath(os.path.join(workspace_dir, filename))
    if not (resolved == root or resolved.startswith(root + os.sep)):
        raise ValueError('write target escapes workspace_dir: %s' % filename)
    return os.path.join(workspace_dir, filename)

def _apply_to_working(workspace_dir, validated, energize, expected_base=None, expected_fingerprint=None, expected_preimage=None):
    # DE-0349: sole writer, un-callable without a _ValidatedPatch. DE-0418: AND un-callable without an
    # _EnergizedApply bound to workspace_dir (dual token). DE-0419: writes ONLY the canonical form and
    # requires sha256(canonical) == the attested fingerprint, so on-disk bytes == the fingerprinted bytes.
    if not isinstance(validated, _ValidatedPatch):
        raise TypeError("not a _ValidatedPatch")
    _require_energize(workspace_dir, energize)
    # §2-B per-patch token binding: a REAL (bound) _EnergizedApply energizes ONE specific patch. A token
    # minted for a different fingerprint/base/scope cannot apply this one -> patch changes => re-adjudicate,
    # and item_id alone can never energize. Test tokens leave these fields None -> no extra constraint
    # (backward compatible with _mint_test_energize).
    if getattr(energize, 'fingerprint', None) is not None and energize.fingerprint != validated.fingerprint:
        raise ValueError('energize token bound to a different fingerprint')
    if getattr(energize, 'base_commit', None) is not None and energize.base_commit != validated.base_commit:
        raise ValueError('energize token bound to a different base_commit')
    if getattr(energize, 'allowed_files', None):
        if not set(validated.filenames).issubset(set(energize.allowed_files)):
            raise ValueError('energize token allowed_files does not cover the patch filenames')
    if expected_base is not None and validated.base_commit != expected_base:
        raise ValueError('base_commit')
    if expected_fingerprint is not None and validated.fingerprint != expected_fingerprint:
        raise ValueError('fingerprint')
    canonical = canonical_diff_artifact(validated.diff, validated.base_commit)   # raw never reaches disk
    if canonical['fingerprint'] != validated.fingerprint:
        raise ValueError('fingerprint')   # attested != canonical bytes -> refuse (DE-0419)
    data = canonical['diff'].encode('utf-8')
    for filename in validated.filenames:
        path = _confined_path(workspace_dir, filename)   # DE-0420: write target confined to workspace_dir
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        if expected_preimage is not None:
            h = hashlib.sha256(open(path,'rb').read()).hexdigest()
            if h != expected_preimage.get(filename):
                raise ValueError('preimage')
        open(path,'wb').write(data)
    return None

def apply_patch(workspace_dir, artifact, allowed_files, energize=None, expected_base=None, expected_fingerprint=None):
    validated = validate_artifact(artifact, allowed_files, expected_base, expected_fingerprint)
    return _apply_to_working(workspace_dir, validated, energize, expected_base=expected_base, expected_fingerprint=expected_fingerprint)

def canonical_diff_artifact(diff_text, base_commit):
    if not isinstance(diff_text, str):
        raise ValueError('diff_text must be a str')

    text = diff_text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.rstrip('\n') + '\n'

    has_diff_header = False
    has_add_header = False
    for line in text.split('\n'):
        if line.startswith('--- a/'):
            has_diff_header = True
        if line.startswith('+++ b/'):
            has_add_header = True
        if has_diff_header and has_add_header:
            break

    if not (has_diff_header and has_add_header):
        raise ValueError('not a unified diff')

    fingerprint = hashlib.sha256(text.encode('utf-8')).hexdigest()

    return {
        'schema_version': 'unified-diff-v1',
        'base_commit': base_commit,
        'fingerprint': fingerprint,
        'diff': text
    }

def dry_run_apply(workspace_dir, validated):
    if not isinstance(validated, _ValidatedPatch):
        raise TypeError('not a _ValidatedPatch')

    diff_bytes = validated.diff.encode('utf-8')

    writes = []
    for filename in validated.filenames:
        filepath = os.path.join(workspace_dir, filename)
        exists = os.path.isfile(filepath)
        if exists:
            with open(filepath, 'rb') as f:
                current_sha256 = hashlib.sha256(f.read()).hexdigest()
        else:
            current_sha256 = None

        would_write_sha256 = hashlib.sha256(diff_bytes).hexdigest()
        would_write_bytes = len(diff_bytes)

        writes.append({
            'filename': filename,
            'exists': exists,
            'current_sha256': current_sha256,
            'would_write_sha256': would_write_sha256,
            'would_write_bytes': would_write_bytes
        })

    return {
        'schema_version': 'dry-run-v1',
        'workspace_dir': workspace_dir,
        'writes': writes
    }

@dataclass(frozen=True)
class _RollbackPlan:
    entries: tuple

def capture_preimage(workspace_dir, validated):
    if not isinstance(validated, _ValidatedPatch):
        raise TypeError('not a _ValidatedPatch')

    entries = []
    for filename in validated.filenames:
        filepath = os.path.join(workspace_dir, filename)
        existed = os.path.exists(filepath)
        if existed:
            with open(filepath, 'rb') as f:
                preimage = f.read()
        else:
            preimage = None
        entries.append({'filename': filename, 'existed': existed, 'preimage': preimage})
    return _RollbackPlan(entries=tuple(entries))

def _restore_preimage(workspace_dir, plan, energize):
    # rollback IS a write-reaching path -> dual token (DE-0418): _RollbackPlan AND an _EnergizedApply bound
    # to workspace_dir.
    if not isinstance(plan, _RollbackPlan):
        raise TypeError('not a _RollbackPlan')
    _require_energize(workspace_dir, energize)
    for entry in plan.entries:
        filename = entry['filename']
        existed = entry['existed']
        preimage = entry['preimage']
        path = _confined_path(workspace_dir, filename)   # DE-0420: rollback target confined to workspace_dir
        if existed:
            with open(path, 'wb') as f:
                f.write(preimage)
        else:
            if os.path.exists(path):
                os.remove(path)

def emit_patch_application(recorder, task_id, validated, outcome, ts, identity='patch-bridge', token_id=None):
    if not isinstance(validated, _ValidatedPatch):
        raise TypeError('not a _ValidatedPatch')

    payload = {
        'outcome': outcome,
        'fingerprint': validated.fingerprint,
        'base_commit': validated.base_commit,
        'filenames': list(validated.filenames),
        'token_id': token_id
    }

    return recorder(task_id, 'PATCH_APPLICATION', payload, ts, identity=identity)

def apply_patch_bounded(workspace_dir, artifact, allowed_files, recorder, task_id, ts, energize=None, expected_base=None, expected_fingerprint=None, expected_preimage=None, identity='patch-bridge'):
    validated = validate_artifact(artifact, allowed_files, expected_base, expected_fingerprint)
    plan = capture_preimage(workspace_dir, validated)
    try:
        _apply_to_working(workspace_dir, validated, energize, expected_base=expected_base, expected_fingerprint=expected_fingerprint, expected_preimage=expected_preimage)
    except Exception:
        try:
            _restore_preimage(workspace_dir, plan, energize)
        except Exception:
            pass   # rollback needs the same energization; if absent, apply never wrote, so nothing to undo
        emit_patch_application(recorder, task_id, validated, 'ROLLED_BACK', ts, identity=identity, token_id=getattr(energize, 'token_id', None))
        raise
    emit_patch_application(recorder, task_id, validated, 'APPLIED', ts, identity=identity, token_id=getattr(energize, 'token_id', None))
    return {
        'schema_version': 'apply-bounded-v1',
        'outcome': 'APPLIED',
        'fingerprint': validated.fingerprint,
        'filenames': list(validated.filenames)
    }

def worker_output_to_artifact(worker_diff, files_changed, base_commit):
    if not isinstance(worker_diff, str) or not worker_diff:
        raise ValueError("worker_diff must be a non-empty string")
    if not isinstance(files_changed, (list, tuple)) or len(files_changed) != 1:
        raise ValueError("files_changed must be a list/tuple of exactly one filename")

    filename = files_changed[0]
    diff_str = f"--- a/{filename}\n+++ b/{filename}\n{worker_diff}"
    return canonical_diff_artifact(diff_str, base_commit)

def _head_commit(target_repo_dir):
    import subprocess
    out = subprocess.run(['git', '-C', target_repo_dir, 'rev-parse', 'HEAD'],
                         capture_output=True, text=True, timeout=10)
    if out.returncode != 0 or not out.stdout.strip():
        raise ValueError('cannot read base_commit (not a git repo?): %s' % out.stderr.strip())
    return out.stdout.strip()

@dataclass(frozen=True)
class _Provenance:
    base_commit: str
    allowed_files: tuple

def capture_provenance(target_repo_dir, allowed_files):
    if not allowed_files:
        raise ValueError("allowed_files is invalid")
    base_commit = _head_commit(target_repo_dir)
    return _Provenance(base_commit, tuple(allowed_files))

def check_diff_within_allowed(diff_text, allowed_files):
    target_paths = []
    for line in diff_text.splitlines():
        if line.strip().startswith('+++ b/'):
            path = line.strip()[len('+++ b/'):].strip()
            if path:
                target_paths.append(path)

    if not target_paths:
        raise ValueError("No target paths found")

    for path in target_paths:
        if path not in allowed_files:
            raise ValueError(f"Path '{path}' not allowed")

    return target_paths

def bridge_apply_connector(energize_token, workspace_dir, artifact, allowed_files, provenance, recorder, task_id, ts):
    if not isinstance(energize_token, _EnergizedApply):
        return {'applied': False, 'blocked': 'NOT_ENERGIZED',
                'reason': 'no _EnergizedApply token (energization is a separate Taka gate)'}
    expected_fp = canonical_diff_artifact(artifact['diff'], artifact['base_commit'])['fingerprint']
    validated = validate_artifact(artifact, allowed_files, provenance.base_commit, expected_fp)
    check_diff_within_allowed(validated.diff, provenance.allowed_files)
    result = apply_patch_bounded(workspace_dir, artifact, allowed_files, recorder, task_id, ts,
                                 energize=energize_token,
                                 expected_base=provenance.base_commit, expected_fingerprint=expected_fp)
    return {'applied': True, 'result': result}
