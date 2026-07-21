"""§2-A standalone verification of bridge_reconciler on a THROWAWAY git repo.
Checks: (1) bootstrap zero-orphan baseline; (2) balanced after a REAL bridge apply; (3) imbalance A =
git-without-event (unrecorded working-tree write); (4) imbalance B = event-without-git (recorded APPLIED not
reflected on disk); (5) pull-type freshness: latest_balance_proof fresh when no apply after proof, stale
when an apply follows. Uses a local fake recorder (accepts RECONCILIATION_*), so no dev-workcell dependency."""
import sys, os, subprocess, tempfile, shutil, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_bridge as pb
import bridge_reconciler as rc

results = []
def check(name, ok, detail=''):
    results.append((name, ok)); print('[%s] %-30s %s' % ('OK' if ok else '**FAIL**', name, detail))

def repo(seed):
    d = tempfile.mkdtemp(prefix='recA_')
    for c in (['git','init','-q',d],['git','-C',d,'config','user.email','t@t'],['git','-C',d,'config','user.name','t']):
        subprocess.run(c, check=True)
    for fn, body in seed.items():
        open(os.path.join(d, fn), 'w').write(body)
    subprocess.run(['git','-C',d,'add','.'], check=True)
    subprocess.run(['git','-C',d,'commit','-qm','init'], check=True)
    return d

class Log:
    """append-ordered merged event log + a recorder the reconciler/bridge can write through."""
    def __init__(self): self.ev = []
    def recorder(self, task_id, kind, payload, ts, identity='x'):
        self.ev.append({'task_id': task_id, 'kind': kind, 'payload': payload, 'ts': ts, 'identity': identity})
        return (kind, (payload or {}).get('outcome'))
    def pa_events(self):
        return [e for e in self.ev if e['kind'] == 'PATCH_APPLICATION']

# ---- (1) bootstrap baseline: clean tree + no events -> zero-orphan baseline ----
d = repo({'impl.py': 'OLD\n'})
try:
    res = rc.reconcile(d, [])
    check('1_bootstrap_baseline', res.balanced and res.baseline and not res.orphans_event_without_git
          and not res.orphans_git_without_event, 'balanced=%s baseline=%s' % (res.balanced, res.baseline))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ---- (2) balanced after a REAL bridge apply (canonical bytes on disk == fingerprint) ----
d = repo({'impl.py': 'OLD\n'})
try:
    log = Log()
    prov = pb.capture_provenance(d, ['impl.py'])
    art = pb.worker_output_to_artifact('+ NEW', ['impl.py'], prov.base_commit)
    r = pb.bridge_apply_connector(pb._mint_test_energize(d), d, art, ['impl.py'], prov, log.recorder, 'T', 'ts1')
    applied = r.get('applied') is True
    res = rc.reconcile(d, log.pa_events())
    # the file is dirty in git, but explained by a matching APPLIED event -> balanced, not baseline
    on_disk = hashlib.sha256(open(os.path.join(d,'impl.py'),'rb').read()).hexdigest()
    ev_fp = log.pa_events()[0]['payload']['fingerprint']
    check('2_balanced_after_apply', applied and res.balanced and not res.baseline
          and on_disk == ev_fp and res.applies_seen == 1,
          'balanced=%s disk==fp=%s' % (res.balanced, on_disk == ev_fp))
    # emit a balance proof; pull-type freshness = fresh (no apply after it)
    rc.emit_reconciliation(log.recorder, 'T', res, 'ts2')
    proof, fresh = rc.latest_balance_proof(log.ev)
    check('2b_proof_fresh', proof is not None and proof['kind'] == rc.RECON_BALANCED and fresh,
          'kind=%s fresh=%s' % (proof and proof['kind'], fresh))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ---- (3) imbalance A: git-without-event (manual working-tree write, no APPLIED event) ----
d = repo({'impl.py': 'OLD\n'})
try:
    open(os.path.join(d, 'impl.py'), 'w').write('MANUALLY_HACKED\n')   # unrecorded write
    res = rc.reconcile(d, [])
    check('3_imbalance_git_without_event', (not res.balanced) and ('impl.py' in res.orphans_git_without_event),
          'orphans_gw=%s' % (res.orphans_git_without_event,))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ---- (4) imbalance B: event-without-git (APPLIED event, but disk doesn't match the fingerprint) ----
d = repo({'impl.py': 'OLD\n'})
try:
    log = Log()
    prov = pb.capture_provenance(d, ['impl.py'])
    art = pb.worker_output_to_artifact('+ NEW', ['impl.py'], prov.base_commit)
    pb.bridge_apply_connector(pb._mint_test_energize(d), d, art, ['impl.py'], prov, log.recorder, 'T', 'ts')
    # now tamper the working tree back so the recorded APPLIED is no longer reflected
    open(os.path.join(d, 'impl.py'), 'w').write('SOMETHING_ELSE\n')
    res = rc.reconcile(d, log.pa_events())
    ew = [x[0] for x in res.orphans_event_without_git]
    check('4_imbalance_event_without_git', (not res.balanced) and ('impl.py' in ew),
          'orphans_ew=%s' % (res.orphans_event_without_git,))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ---- (5) freshness stale: a PATCH_APPLICATION recorded AFTER the last balance proof ----
d = repo({'impl.py': 'OLD\n'})
try:
    log = Log()
    # balanced state + proof
    res0 = rc.reconcile(d, [])
    rc.emit_reconciliation(log.recorder, 'T', res0, 'ts0')
    # then an apply happens (recorded) -> proof is now stale
    prov = pb.capture_provenance(d, ['impl.py'])
    art = pb.worker_output_to_artifact('+ NEW', ['impl.py'], prov.base_commit)
    pb.bridge_apply_connector(pb._mint_test_energize(d), d, art, ['impl.py'], prov, log.recorder, 'T', 'ts')
    proof, fresh = rc.latest_balance_proof(log.ev)
    check('5_freshness_stale_after_apply', proof is not None and (not fresh),
          'fresh=%s (apply after proof => stale)' % fresh)
    # empty log -> no proof -> not fresh (fail-closed)
    p2, f2 = rc.latest_balance_proof([])
    check('5b_no_proof_failclosed', p2 is None and (not f2), 'proof=%s fresh=%s' % (p2, f2))
finally:
    shutil.rmtree(d, ignore_errors=True)

fails = [n for n, ok in results if not ok]
print('\n=== §2-A RECONCILER STANDALONE: %d checks, %d FAIL ===' % (len(results), len(fails)))
sys.exit(0 if not fails else 2)
