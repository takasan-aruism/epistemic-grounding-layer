"""§2-B standalone verification of bridge_minter on a THROWAWAY repo.
Positive: a Taka adjudication + fresh reconciler proof -> mint -> token drives a REAL bridge apply E2E.
Structural per-patch binding: a token minted for patch X cannot apply patch Y.
Fail-closed: every refusal gate raises MintRefused. No real repo touched."""
import sys, os, subprocess, tempfile, shutil, hashlib, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_bridge as pb
import bridge_reconciler as rc
import bridge_minter as bm

results = []
def check(name, ok, detail=''):
    results.append((name, ok)); print('[%s] %-34s %s' % ('OK' if ok else '**FAIL**', name, detail))

def repo(seed):
    d = tempfile.mkdtemp(prefix='minB_')
    for c in (['git','init','-q',d],['git','-C',d,'config','user.email','t@t'],['git','-C',d,'config','user.name','t']):
        subprocess.run(c, check=True)
    for fn, body in seed.items():
        open(os.path.join(d, fn), 'w').write(body)
    subprocess.run(['git','-C',d,'add','.'], check=True)
    subprocess.run(['git','-C',d,'commit','-qm','init'], check=True)
    return d

class Log:
    def __init__(self): self.ev = []
    def recorder(self, task_id, kind, payload, ts, identity='x'):
        self.ev.append({'task_id':task_id,'kind':kind,'payload':payload,'ts':ts,'identity':identity})
        return (kind,(payload or {}).get('outcome'))
    def pa(self): return [e for e in self.ev if e['kind']=='PATCH_APPLICATION']

NOW = '2026-07-18T10:00:00'
EXP = '2026-07-18T23:59:59'

def good_setup():
    """Return (repo_dir, event_log(list), request) all consistent & mintable, with a fresh balance proof."""
    d = repo({'impl.py':'OLD\n'})
    log = Log()
    base = pb.capture_provenance(d, ['impl.py']).base_commit
    art = pb.worker_output_to_artifact('+ NEW', ['impl.py'], base)
    fp = art['fingerprint']
    # reconcile baseline & emit a fresh proof for this base (head == base)
    res = rc.reconcile(d, [])
    rc.emit_reconciliation(log.recorder, 'T', res, 'ts_proof')
    assert log.ev[-1]['payload']['head'] == base
    # Taka adjudication event
    adj = {'kind':'ENERGIZATION_ADJUDICATION','ts':'ts_adj','payload':{
        'adjudication_id':'ADJ-1','authority_owner':'TAKA','granted_by':'TAKA','attribution':'TAKA',
        'item_id':'ITEM-1','repo_realpath':os.path.realpath(d),'base_commit':base,'fingerprint':fp,
        'allowed_files':['impl.py'],'expires_at':EXP}}
    log.ev.append(adj)
    request = {'item_id':'ITEM-1','task_id':'TASK-1','trace_id':'TR-1','repo_identity':'throwaway',
               'repo_realpath':os.path.realpath(d),'base_commit':base,'allowed_files':['impl.py'],
               'fingerprint':fp,'token_id':'TOK-1','adjudication_id':'ADJ-1'}
    return d, log, art, request

def refused(name, mutate):
    d, log, art, req = good_setup()
    try:
        mutate(d, log, art, req)
        try:
            bm.mint_real_energize(req, log.ev, d, now_ts=NOW)
            check(name, False, 'mint SUCCEEDED (should refuse)')
        except bm.MintRefused as e:
            check(name, True, str(e))
    finally:
        shutil.rmtree(d, ignore_errors=True)

# ---- POSITIVE: mint + real bridge apply E2E ----
d, log, art, req = good_setup()
try:
    tok = bm.mint_real_energize(req, log.ev, d, now_ts=NOW)
    bound = (isinstance(tok, pb._EnergizedApply) and tok.grant == os.path.realpath(d)
             and tok.token_id=='TOK-1' and tok.fingerprint==req['fingerprint']
             and tok.base_commit==req['base_commit'] and tok.allowed_files==('impl.py',)
             and tok.adjudication_ref=='ADJ-1')
    check('P_mint_binds_all_fields', bound, 'grant/token_id/fp/base/allowed/adj all bound')
    # drive a REAL bridge apply with the minted token
    prov = pb.capture_provenance(d, ['impl.py'])
    r = pb.bridge_apply_connector(tok, d, art, ['impl.py'], prov, log.recorder, req['task_id'], 'ts_apply')
    on_disk = hashlib.sha256(open(os.path.join(d,'impl.py'),'rb').read()).hexdigest()
    applied_ev = [e for e in log.pa() if e['payload'].get('outcome')=='APPLIED']
    tokid_recorded = applied_ev and applied_ev[-1]['payload'].get('token_id')=='TOK-1'
    check('P_token_drives_real_apply', r.get('applied') is True and on_disk==req['fingerprint'] and tokid_recorded,
          'applied=%s disk==fp=%s token_id in event=%s' % (r.get('applied'), on_disk==req['fingerprint'], bool(tokid_recorded)))
    # re-reconcile + emit a FRESH proof after the apply (so freshness is satisfied), then re-mint must be
    # refused SPECIFICALLY by single-use (token_id now appears in a PATCH_APPLICATION event).
    res2 = rc.reconcile(d, log.pa())
    rc.emit_reconciliation(log.recorder, 'T', res2, 'ts_proof2')
    try:
        bm.mint_real_energize(req, log.ev, d, now_ts=NOW)
        check('P_single_use_after_apply', False, 're-mint succeeded (should be consumed)')
    except bm.MintRefused as e:
        check('P_single_use_after_apply', 'single-use' in str(e), str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ---- STRUCTURAL: token for patch X cannot apply patch Y (per-patch binding at the write primitive) ----
d, log, art, req = good_setup()
try:
    tok = bm.mint_real_energize(req, log.ev, d, now_ts=NOW)     # bound to art's fingerprint
    prov = pb.capture_provenance(d, ['impl.py'])
    art_Y = pb.worker_output_to_artifact('+ DIFFERENT_PAYLOAD', ['impl.py'], prov.base_commit)  # different fp
    before = open(os.path.join(d,'impl.py')).read()
    raised = False
    try:
        pb.bridge_apply_connector(tok, d, art_Y, ['impl.py'], prov, log.recorder, 'T', 'ts')
    except ValueError:
        raised = True   # write primitive refuses: token bound to a different fingerprint
    applied_Y = [e for e in log.pa() if e['payload'].get('outcome')=='APPLIED']
    no_apply = raised and open(os.path.join(d,'impl.py')).read()==before and not applied_Y
    check('S_wrong_patch_blocked', no_apply and art_Y['fingerprint']!=req['fingerprint'],
          'patch Y refused by patch-X token (raised=%s, file unchanged)' % raised)
finally:
    shutil.rmtree(d, ignore_errors=True)

# ---- REFUSAL PATHS (fail-closed) ----
def _adj(log):
    for e in log.ev:
        if e['kind']=='ENERGIZATION_ADJUDICATION': return e['payload']
    raise AssertionError('no adj')
def _proof(log):
    for e in reversed(log.ev):
        if e['kind'] in rc.RECON_KINDS: return e['payload']
    raise AssertionError('no proof')

refused('R_missing_request_key',   lambda d,l,a,r: r.pop('trace_id'))
refused('R_repo_realpath_mismatch',lambda d,l,a,r: r.__setitem__('repo_realpath','/tmp/not-this'))
refused('R_no_adjudication',       lambda d,l,a,r: l.ev.__setitem__(slice(0,len(l.ev)),
                                       [e for e in l.ev if e['kind']!='ENERGIZATION_ADJUDICATION']))
refused('R_authority_not_taka',    lambda d,l,a,r: _adj(l).__setitem__('authority_owner','EVE'))
refused('R_granted_by_not_taka',   lambda d,l,a,r: _adj(l).__setitem__('granted_by','EVE'))
refused('R_self_attributed',       lambda d,l,a,r: _adj(l).__setitem__('attribution','CLAUDE'))
refused('R_item_mismatch',         lambda d,l,a,r: r.__setitem__('item_id','ITEM-OTHER'))
refused('R_fingerprint_mismatch',  lambda d,l,a,r: r.__setitem__('fingerprint','deadbeef'*8))
refused('R_allowed_files_mismatch',lambda d,l,a,r: r.__setitem__('allowed_files',['impl.py','extra.py']))
refused('R_revoked',               lambda d,l,a,r: l.ev.append({'kind':'ENERGIZATION_REVOCATION','ts':'t',
                                       'payload':{'adjudication_id':'ADJ-1'}}))
refused('R_expired',               lambda d,l,a,r: _adj(l).__setitem__('expires_at','2026-07-18T09:00:00'))
refused('R_no_fresh_proof_apply_after', lambda d,l,a,r: l.ev.append({'kind':'PATCH_APPLICATION','ts':'t',
                                       'payload':{'outcome':'APPLIED','token_id':'OTHER','filenames':['impl.py']}}))
refused('R_proof_head_mismatch',   lambda d,l,a,r: _proof(l).__setitem__('head','0'*40))
refused('R_token_already_consumed',lambda d,l,a,r: l.ev.append({'kind':'PATCH_APPLICATION','ts':'t',
                                       'payload':{'outcome':'APPLIED','token_id':'TOK-1','filenames':['impl.py']}}))

fails = [n for n,ok in results if not ok]
print('\n=== §2-B MINTER STANDALONE: %d checks, %d FAIL ===' % (len(results), len(fails)))
for n,ok in results:
    if not ok: print('  FAIL:', n)
sys.exit(0 if not fails else 2)
