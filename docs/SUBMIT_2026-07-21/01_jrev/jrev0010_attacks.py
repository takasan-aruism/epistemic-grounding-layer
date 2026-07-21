"""JREV-0010 -- FIRST application of the DE-0426 re-battle principle (Taka §3, [BIND-4]).

This is NOT a regression test. Each probe is a NOVEL attack that RE-USES a concept the §2 change INTRODUCED
(the reconciler, the pull-type balance-proof, the ENERGIZATION_ADJUDICATION event, freshness, single-use,
per-patch token binding). Author = Claude (disclosed). Attacker weight = this separate probe process, which
touches ONLY the public surface of patch_bridge / bridge_reconciler / bridge_minter and tries to breach it.
Adjudicator = GPT (via Taka relay). Throwaway repos only.

Outcome recorded per probe: BLOCKED (attack refused/ineffective) or *BREACH* (attack succeeded)."""
import sys, os, subprocess, tempfile, shutil, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_bridge as pb
import bridge_reconciler as rc
import bridge_minter as bm

verdicts = []
def rec(name, blocked, detail=''):
    verdicts.append((name, blocked)); print('[%s] %-40s %s' % ('BLOCKED' if blocked else '*BREACH*', name, detail))

NOW, EXP = '2026-07-18T10:00:00', '2026-07-18T23:59:59'

class Log:
    def __init__(self): self.ev = []
    def recorder(self, task_id, kind, payload, ts, identity='x'):
        self.ev.append({'task_id':task_id,'kind':kind,'payload':payload,'ts':ts,'identity':identity})
        return (kind,(payload or {}).get('outcome'))
    def pa(self): return [e for e in self.ev if e['kind']=='PATCH_APPLICATION']

def repo(seed='OLD\n'):
    d = tempfile.mkdtemp(prefix='jrev10_')
    for c in (['git','init','-q',d],['git','-C',d,'config','user.email','t@t'],['git','-C',d,'config','user.name','t']):
        subprocess.run(c, check=True)
    open(os.path.join(d,'impl.py'),'w').write(seed)
    subprocess.run(['git','-C',d,'add','.'], check=True); subprocess.run(['git','-C',d,'commit','-qm','i'], check=True)
    return d

def base_and_art(d):
    base = pb.capture_provenance(d, ['impl.py']).base_commit
    art = pb.worker_output_to_artifact('+ NEW', ['impl.py'], base)
    return base, art

def taka_adj(d, base, fp, aid='ADJ', item='IT'):
    return {'kind':'ENERGIZATION_ADJUDICATION','ts':'t','payload':{
        'adjudication_id':aid,'authority_owner':'TAKA','granted_by':'TAKA','attribution':'TAKA',
        'item_id':item,'repo_realpath':os.path.realpath(d),'base_commit':base,'fingerprint':fp,
        'allowed_files':['impl.py'],'expires_at':EXP}}

def req(d, base, fp, aid='ADJ', item='IT', tok='TOK'):
    return {'item_id':item,'task_id':'TK','trace_id':'TR','repo_identity':'tw','repo_realpath':os.path.realpath(d),
            'base_commit':base,'allowed_files':['impl.py'],'fingerprint':fp,'token_id':tok,'adjudication_id':aid}

def fresh_proof(d, log, events=None):
    res = rc.reconcile(d, events or [])
    rc.emit_reconciliation(log.recorder, 'T', res, 'tsp')

# ==== A1. adjudication CONTENT forgery: an event that CLAIMS Taka but omits attribution (re-use: the
#         authority concept). A blocklist would let it through; the allowlist must refuse. ====
d = repo()
try:
    base, art = base_and_art(d); log = Log(); fresh_proof(d, log)
    forged = {'kind':'ENERGIZATION_ADJUDICATION','ts':'t','payload':{
        'adjudication_id':'ADJ','authority_owner':'TAKA','granted_by':'TAKA',   # NO 'attribution' field
        'item_id':'IT','repo_realpath':os.path.realpath(d),'base_commit':base,'fingerprint':art['fingerprint'],
        'allowed_files':['impl.py'],'expires_at':EXP}}
    log.ev.append(forged)
    try:
        bm.mint_real_energize(req(d, base, art['fingerprint']), log.ev, d, now_ts=NOW)
        rec('A1_unattributed_taka_claim', False, 'minted from an unattributed event')
    except bm.MintRefused as e:
        rec('A1_unattributed_taka_claim', 'attribution' in str(e), str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ==== A2. forged BALANCED proof over an ACTUALLY-imbalanced tree (re-use: the pull-type balance-proof).
#         Attacker makes an UNRECORDED write, then appends a RECONCILIATION_BALANCED event to fake liveness.
#         The minter must re-derive reconcile() and refuse. ====
d = repo()
try:
    base, art = base_and_art(d); log = Log()
    open(os.path.join(d,'impl.py'),'w').write('UNRECORDED_HACK\n')     # real imbalance (git-without-event)
    # forge a BALANCED proof claiming head==base with no orphans
    log.ev.append({'kind':rc.RECON_BALANCED,'ts':'t','payload':{'balanced':True,'baseline':False,
                   'head':base,'orphans_event_without_git':[],'orphans_git_without_event':[],
                   'checked_files':[],'applies_seen':0}})
    log.ev.append(taka_adj(d, base, art['fingerprint']))
    try:
        bm.mint_real_energize(req(d, base, art['fingerprint']), log.ev, d, now_ts=NOW)
        rec('A2_forged_balanced_proof', False, 'minted despite an unrecorded working-tree write')
    except bm.MintRefused as e:
        rec('A2_forged_balanced_proof', 'imbalanced' in str(e) or 'reconcile' in str(e), str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ==== A3. per-patch binding evasion via a WIDER adjudication (re-use: item/patch binding). Attacker holds a
#         Taka adjudication for fingerprint X and tries to energize a DIFFERENT patch Y under the same item. ====
d = repo()
try:
    base, artX = base_and_art(d); log = Log(); fresh_proof(d, log)
    log.ev.append(taka_adj(d, base, artX['fingerprint']))
    tok = bm.mint_real_energize(req(d, base, artX['fingerprint']), log.ev, d, now_ts=NOW)   # bound to X
    prov = pb.capture_provenance(d, ['impl.py'])
    artY = pb.worker_output_to_artifact('+ EVIL_PAYLOAD', ['impl.py'], prov.base_commit)     # different fp
    before = open(os.path.join(d,'impl.py')).read(); breached = False
    try:
        pb.bridge_apply_connector(tok, d, artY, ['impl.py'], prov, log.recorder, 'T', 't')
        breached = open(os.path.join(d,'impl.py')).read()!=before
    except ValueError:
        breached = False
    rec('A3_wrong_patch_under_token', not breached, 'patch-X token cannot apply patch Y (write primitive binding)')
finally:
    shutil.rmtree(d, ignore_errors=True)

# ==== A4. reconciler coerced to WRITE (re-use: the reconciler is the new standing component). Attacker passes
#         a malicious "recorder" hoping the reconciler mutates the repo. The reconciler must only ever call the
#         recorder with RECONCILIATION_* and never touch git/files (structural; here we assert behaviourally). ====
d = repo()
try:
    base, art = base_and_art(d)
    touched = {'writes': 0}
    class Spy:
        def recorder(self, *a, **k):
            return None
    res = rc.reconcile(d, [])                      # pure read
    before_head = subprocess.run(['git','-C',d,'rev-parse','HEAD'],capture_output=True,text=True).stdout
    rc.emit_reconciliation(Spy().recorder, 'T', res, 't')   # only path that writes = the injected recorder
    after_head = subprocess.run(['git','-C',d,'rev-parse','HEAD'],capture_output=True,text=True).stdout
    tree_clean = subprocess.run(['git','-C',d,'status','--porcelain'],capture_output=True,text=True).stdout.strip()==''
    rec('A4_reconciler_cannot_write', before_head==after_head and tree_clean,
        'reconcile()+emit did not mutate git or working tree')
finally:
    shutil.rmtree(d, ignore_errors=True)

# ==== A5. revocation ignored (re-use: revoke fail-closed). A revoked adjudication must not mint even with a
#         fresh proof and matching content. ====
d = repo()
try:
    base, art = base_and_art(d); log = Log(); fresh_proof(d, log)
    log.ev.append(taka_adj(d, base, art['fingerprint']))
    log.ev.append({'kind':'ENERGIZATION_REVOCATION','ts':'t','payload':{'adjudication_id':'ADJ'}})
    try:
        bm.mint_real_energize(req(d, base, art['fingerprint']), log.ev, d, now_ts=NOW)
        rec('A5_revoked_still_mints', False, 'minted a revoked adjudication')
    except bm.MintRefused as e:
        rec('A5_revoked_still_mints', 'revoked' in str(e), str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

# ==== A6. stale-proof replay across a NEW apply (re-use: clock-free freshness). After a legit apply, the old
#         proof is stale; attacker re-submits it to mint again. ====
d = repo()
try:
    base, art = base_and_art(d); log = Log(); fresh_proof(d, log)
    log.ev.append(taka_adj(d, base, art['fingerprint']))
    tok = bm.mint_real_energize(req(d, base, art['fingerprint']), log.ev, d, now_ts=NOW)
    prov = pb.capture_provenance(d, ['impl.py'])
    pb.bridge_apply_connector(tok, d, art, ['impl.py'], prov, log.recorder, 'T', 't')   # apply -> proof now stale
    # attacker tries to mint AGAIN with a new adjudication but WITHOUT a new reconciler proof
    log.ev.append(taka_adj(d, base, art['fingerprint'], aid='ADJ2', item='IT'))
    try:
        bm.mint_real_energize(req(d, base, art['fingerprint'], aid='ADJ2', tok='TOK2'), log.ev, d, now_ts=NOW)
        rec('A6_stale_proof_replay', False, 'minted on a stale proof after an apply')
    except bm.MintRefused as e:
        rec('A6_stale_proof_replay', 'stale' in str(e) or 'fresh' in str(e), str(e))
finally:
    shutil.rmtree(d, ignore_errors=True)

nb = [n for n,b in verdicts if not b]
print('\n=== JREV-0010 RE-BATTLE: %d novel attacks, %d BREACH ===' % (len(verdicts), len(nb)))
for n,b in verdicts:
    if not b: print('  BREACH:', n)
sys.exit(0 if not nb else 2)
