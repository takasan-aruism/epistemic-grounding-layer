# FIX-01 仕様 r2 — repo identity binding(JREV-0010-F1 / EM-4 / EM-3(a))

r2 改版(DE-0485 の振動2点を本文で固定。契約の意味は不変・明示化のみ):
  - latest_balance_proof の戻り値契約を明文化(§2 LBP-RET)
  - realpath 両辺適用を分類規則の箇所に不変条件として再掲(§2 RP-INV)

authority: SEAL-2026-07-21 §4(FIX-LIFT-JREV0010)/ bundle-a-remediation-spec-v1.1 R1
実装対象: patch_bridge.py / bridge_reconciler.py / bridge_minter.py の3ファイルを
**完全なファイルとして再出力**する。本仕様末尾の <current_source> が現行版であり、
指定された変更以外の挙動を一切変えないこと(回帰は配備時に既存 oracle 全件で実測される)。

## 変更契約(この API を厳守。テストはこの契約に対して書かれている)

### 1. patch_bridge.py — emit_patch_application
新シグネチャ:
    emit_patch_application(recorder, task_id, validated, outcome, ts,
                           identity='patch-bridge', token_id=None,
                           repo_identity=None, repo_realpath=None)
- repo_identity / repo_realpath のどちらかが None または空 → ValueError
  ('PATCH_APPLICATION requires repo identity (fail-closed)')。既定 None は
  「省略可」ではなく「未指定を検出して拒否するため」の哨戒値。
- payload に repo_identity / repo_realpath を追加(既存キーは不変)。
- 他の関数・クラスは一切変更しない。

### 2. bridge_reconciler.py
- reconcile 新シグネチャ:
    reconcile(repo_dir, patch_application_events, repo_identity)
  repo_identity が falsy → ValueError。
  冒頭で real = os.path.realpath(repo_dir) を取り、入力 events を分類:
    bound_here  = repo_identity 一致 かつ os.path.realpath(payload の
                  repo_realpath) == real
    bound_other = repo 場が両方あり、上記不一致
    unbound     = repo_identity / repo_realpath のどちらかが欠落
  【RP-INV・退行禁止の不変条件】path の比較は**必ず両辺に os.path.realpath を
  適用してから**行う。event 側の path を生文字列で比較してはならない。
  「path が既に正規形か」を自分自身と比較する述語は無意味であり禁止。
  この不変条件の番人テストは test_t3_symlink_alias_of_same_repo_accepted
  である(symlink 経由の自 repo イベントは realpath 解決により受理される)。
  折込(_fold_expected)には bound_here のみを使う。bound_other は無視。
  ReconResult に3フィールド追加:
    repo_identity: str / repo_realpath: str / unbound_events_seen: int
  (unbound は balanced 判定に影響させない。fail-closed は minter が担う。)
- emit_reconciliation 新シグネチャ:
    emit_reconciliation(recorder, task_id, result, ts,
                        identity='bridge-reconciler', ledger_offset=None)
  payload に追加: repo_identity / repo_realpath(result から)/
  proof_issuance_identity(=identity)/ checked_ledger_offset(=ledger_offset、
  None 可)。既存キーは不変。
- latest_balance_proof 新シグネチャ:
    latest_balance_proof(event_log, repo_identity, repo_realpath)
  対象 repo の proof のみを走査(payload の repo_identity が一致し、かつ
  os.path.realpath(payload の repo_realpath) == os.path.realpath(引数の
  repo_realpath) である RECONCILIATION_* のみ。RP-INV はここにも適用)。
  【LBP-RET・戻り値契約】走査は「対象 repo に bound な RECONCILIATION_* の
  うち最後のもの」を選ぶ。他 repo の proof・旧形式(repo 場欠落)の proof は
  **選択候補にすら入らない**。対象 repo の RECONCILIATION_* が1件も無ければ
  **(None, False) を返す**——「global 最後の proof を返して fresh=False」は
  契約違反である。選ばれた proof が IMBALANCED なら (proof, False)。freshness の「以後の PATCH_APPLICATION」
  判定は、**同 repo に bound な PA と、unbound な PA の両方**を stale 要因と
  数える(unbound は帰属不明ゆえ安全側で stale 扱い)。bound_other の PA は
  数えない。repo 場を欠く RECONCILIATION_* proof は対象外(旧形式 proof は
  この関数を通らない = 旧 proof で mint 不能、fail-closed)。

### 3. bridge_minter.py — mint_real_energize
ゲート(3) を次で置換(順序どおり):
  (3a) 全 PATCH_APPLICATION を走査し、repo_identity / repo_realpath の
       どちらかを欠く event が1件でもあれば
       MintRefused('unbound PATCH_APPLICATION in log (fail-closed)')。
  (3b) proof, fresh = rc.latest_balance_proof(event_log,
           request['repo_identity'], request['repo_realpath'])
       fresh でなければ従来どおり refuse。proof payload の repo_identity /
       repo_realpath が request と不一致 → MintRefused。head 検査は従来どおり。
  (3c) pa_repo = bound_here のみ(realpath 一致 + identity 一致)を抽出し
       live = rc.reconcile(repo_dir, pa_repo, request['repo_identity'])。
       live.balanced / live.head 検査は従来どおり。
- realpath 照合は常に os.path.realpath を両辺に適用(symlink / 相対 path /
  大文字小文字 alias を弾く)。
- _token_id_consumed は**意図的に全 repo 走査のまま**とする(消費の広い解釈 =
  拒否が増える方向 = 安全側)。コメントでその旨を明記。
- 他のゲート(1)(2)(2')(2'')(BIND-3) と docstring の束縛宣言は不変。

## 禁止事項
- 上記以外の関数・定数・例外クラスの追加/削除/改名。
- git 書込系コードの追加(BIND-1 維持。AST gate が配備時に検査する)。
- テストファイルの変更(immutable)。

## 現行ソース(この3ファイルを基点に、変更契約のみを適用して全文出力せよ)

<current_source path="patch_bridge.py">
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

</current_source>

<current_source path="bridge_reconciler.py">
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

</current_source>

<current_source path="bridge_minter.py">
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

</current_source>
