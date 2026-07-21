"""§4 counterfactual gate -- ENERGIZATION LAYER new injections (Taka §3/§4). Complements gate_s4.py
(bridge write path). Each injection is a violation of an energization invariant introduced by §2 (adjudication
existence/authority, reconciler freshness + re-derivation, revoke/expiry, single-use, per-patch binding,
reconciler read-only). Terminal requires 0 SLIPPED. Throwaway repos only; canonical stores untouched."""
import sys, os, subprocess, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_bridge as pb
import bridge_reconciler as rc
import bridge_minter as bm

results = []
def verdict(name, blocked, detail=''):
    results.append((name, blocked)); print('[%s] %-30s %s' % ('BLOCKED' if blocked else '*SLIPPED*', name, detail))

NOW, EXP = '2026-07-18T10:00:00', '2026-07-18T23:59:59'
class Log:
    def __init__(self): self.ev=[]
    def recorder(self, t,k,p,ts,identity='x'): self.ev.append({'task_id':t,'kind':k,'payload':p,'ts':ts,'identity':identity}); return (k,(p or {}).get('outcome'))
    def pa(self): return [e for e in self.ev if e['kind']=='PATCH_APPLICATION']
def repo():
    d=tempfile.mkdtemp(prefix='s4e_')
    for c in (['git','init','-q',d],['git','-C',d,'config','user.email','t@t'],['git','-C',d,'config','user.name','t']): subprocess.run(c,check=True)
    open(os.path.join(d,'impl.py'),'w').write('OLD\n'); subprocess.run(['git','-C',d,'add','.'],check=True); subprocess.run(['git','-C',d,'commit','-qm','i'],check=True)
    return d
def setup():
    d=repo(); log=Log(); base=pb.capture_provenance(d,['impl.py']).base_commit
    art=pb.worker_output_to_artifact('+ NEW',['impl.py'],base); fp=art['fingerprint']
    rc.emit_reconciliation(log.recorder,'T',rc.reconcile(d,[]),'tsp')
    adj={'kind':'ENERGIZATION_ADJUDICATION','ts':'t','payload':{'adjudication_id':'ADJ','authority_owner':'TAKA',
         'granted_by':'TAKA','attribution':'TAKA','item_id':'IT','repo_realpath':os.path.realpath(d),
         'base_commit':base,'fingerprint':fp,'allowed_files':['impl.py'],'expires_at':EXP}}
    req={'item_id':'IT','task_id':'TK','trace_id':'TR','repo_identity':'tw','repo_realpath':os.path.realpath(d),
         'base_commit':base,'allowed_files':['impl.py'],'fingerprint':fp,'token_id':'TOK','adjudication_id':'ADJ'}
    return d, log, art, adj, req
def refuses(name, mutate):
    d,log,art,adj,req = setup()
    try:
        log.ev.append(adj); mutate(d,log,art,adj,req)
        try:
            bm.mint_real_energize(req, log.ev, d, now_ts=NOW); verdict(name, False, 'minted (should refuse)')
        except bm.MintRefused as e: verdict(name, True, str(e))
    finally: shutil.rmtree(d, ignore_errors=True)

def _adjp(log):
    for e in log.ev:
        if e['kind']=='ENERGIZATION_ADJUDICATION': return e['payload']

# positive control: clean setup mints
d,log,art,adj,req = setup()
try:
    log.ev.append(adj); tok=bm.mint_real_energize(req, log.ev, d, now_ts=NOW)
    print('[OK-CTL] positive_control            minted=%s' % isinstance(tok, pb._EnergizedApply))
finally: shutil.rmtree(d, ignore_errors=True)

refuses('i_no_adjudication',      lambda d,l,a,adj,r: l.ev.remove(next(e for e in l.ev if e['kind']=='ENERGIZATION_ADJUDICATION')))
refuses('i_absent_attribution',   lambda d,l,a,adj,r: _adjp(l).pop('attribution'))
refuses('i_authority_not_taka',   lambda d,l,a,adj,r: _adjp(l).__setitem__('authority_owner','EVE'))
refuses('j_forged_balanced_proof',lambda d,l,a,adj,r: (open(os.path.join(d,'impl.py'),'w').write('HACK\n'),
                                     l.ev.append({'kind':rc.RECON_BALANCED,'ts':'t','payload':{'balanced':True,
                                     'baseline':False,'head':r['base_commit'],'orphans_event_without_git':[],
                                     'orphans_git_without_event':[],'checked_files':[],'applies_seen':0}})))
refuses('k_revoked',              lambda d,l,a,adj,r: l.ev.append({'kind':'ENERGIZATION_REVOCATION','ts':'t','payload':{'adjudication_id':'ADJ'}}))
refuses('l_expired',              lambda d,l,a,adj,r: _adjp(l).__setitem__('expires_at','2026-07-18T09:00:00'))
refuses('m_no_fresh_proof',       lambda d,l,a,adj,r: l.ev.append({'kind':'PATCH_APPLICATION','ts':'t','payload':{'outcome':'APPLIED','token_id':'X','filenames':['impl.py']}}))
refuses('n_repo_realpath_spoof',  lambda d,l,a,adj,r: r.__setitem__('repo_realpath','/tmp/elsewhere'))
refuses('o_patch_fp_mismatch',    lambda d,l,a,adj,r: r.__setitem__('fingerprint','ff'*32))

# p. wrong-patch under a valid token -> write primitive refuses (not applied)
d,log,art,adj,req = setup()
try:
    log.ev.append(adj); tok=bm.mint_real_energize(req, log.ev, d, now_ts=NOW)
    prov=pb.capture_provenance(d,['impl.py']); artY=pb.worker_output_to_artifact('+ EVIL',['impl.py'],prov.base_commit)
    before=open(os.path.join(d,'impl.py')).read(); blocked=False
    try: pb.bridge_apply_connector(tok, d, artY, ['impl.py'], prov, log.recorder, 'T','t')
    except ValueError: blocked=True
    verdict('p_wrong_patch_write', blocked and open(os.path.join(d,'impl.py')).read()==before, 'token bound to a different fingerprint')
finally: shutil.rmtree(d, ignore_errors=True)

# q. reconciler cannot mutate the repo (read-only, behavioral)
d=repo()
try:
    h0=subprocess.run(['git','-C',d,'rev-parse','HEAD'],capture_output=True,text=True).stdout
    rc.emit_reconciliation((lambda *a,**k: None), 'T', rc.reconcile(d,[]), 't')
    h1=subprocess.run(['git','-C',d,'rev-parse','HEAD'],capture_output=True,text=True).stdout
    clean=subprocess.run(['git','-C',d,'status','--porcelain'],capture_output=True,text=True).stdout.strip()==''
    verdict('q_reconciler_readonly', h0==h1 and clean, 'reconcile()+emit did not mutate repo')
finally: shutil.rmtree(d, ignore_errors=True)

slipped=[n for n,b in results if not b]
print('\n=== §4 ENERGIZATION GATE: %d injections, %d SLIPPED ===' % (len(results), len(slipped)))
for n,b in results:
    if not b: print('  *** SLIPPED:', n)
sys.exit(0 if not slipped else 2)
