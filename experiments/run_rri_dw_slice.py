#!/usr/bin/env python3
"""Generic RRI-through-DW slice runner (A-mode, sequential swap). argv[1] = slice name.

各 slice を DW loop に流す: GENERATE=Qwen3-Coder-Next(8006) → swap → AUDIT=Qwen3.6(8005) → (swap → REGEN)。
load-bearing test = coder のコードを subprocess 実行。終了時に必ず Qwen3.6 restore。
slice config は SLICES に。call/result_key で 1-arg/2-arg・ok/may_* を吸収。
"""
import json, os, re, subprocess, sys, tempfile, time, urllib.request, urllib.error, socket
from pathlib import Path
sys.path.insert(0, "/home/takasan/dev-workcell")
from dw import workcell as W

QWEN_EP, QWEN_M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
CODER_EP, CODER_M = "http://localhost:8006/v1/chat/completions", "Qwen3-Coder-Next"
SCRIPTS = "/home/takasan/models_trtllm"
RUN_SOR = "/home/takasan/dev-workcell/run_sor"  # F-1: persistent append-only DW run SoR (NOT a temp dir)
SWAPS = []
CURRENT_TASK = None
CURRENT_MODEL = "qwen"  # 起動時は Qwen3.6 が上がっている前提


def _iso(t=None):
    import datetime as _dt
    return _dt.datetime.fromtimestamp(t if t is not None else time.time(), _dt.timezone.utc).isoformat()


def _proc(kind, payload, ts):
    """F-1: 実行過程 primitive を DW SoR に append(best-effort、run を壊さない)。"""
    try:
        if CURRENT_TASK:
            W.record_process_event(CURRENT_TASK, kind, payload, ts)
    except Exception as e:
        print(f"  (proc-event {kind} skipped: {type(e).__name__})", flush=True)

# ── slice registry ───────────────────────────────────────────────────────────
XT = "RAW_REQUEST_TO_RESOLVED_INTENT|RESOLVED_INTENT_TO_RESEARCH_DESIGN|RESEARCH_AXIS_TO_RQ|OBSERVATION_TO_EVIDENCE|EVIDENCE_TO_CLAIM"
_RDEC = {"rdec_id":"RDEC-1","decision":"WORKER_ASSIGNMENT","axis":"STARTUP_COST","why_required":"cost may make a capable worker impractical","expected_decision_effect":"may change LOCAL_WORKER vs ESCALATION","omission_risk":"select a capable but unusable worker","stop_condition_ref":"STOP-1"}
_NEC = {"validated":True,"origin_decision":"WORKER_ASSIGNMENT","observed_block_refs":["DWSTATE-1"],"alternative_causes":["adapter unavailable","policy undefined"],"research_requirement_summary":"no role-validation state exists"}
_NEED = {"need_id":"RNEED-1","origin_system":"DW","decision_to_support":"WORKER_ASSIGNMENT","blocked_state":"PLANNING","nec":_NEC}
SLICES = {
 "rda": {
   "fn":"research_design_audit_gate","call":"research_design_audit_gate(item)","key":"may_proceed","task":"TASK-RRI-RDA-02",
   "goal":"research_design_audit_gate §27-28: MAJOR dispositioned w/ finding-level C-TOTALITY + RESOLVED needs revision + rq_candidates",
   "spec":("Implement `research_design_audit_gate(design)` for an RRI Research Design (spec sections 27-28). It "
     "decides whether a research design may proceed to an Approved RQ Set. design is a dict with: audit_findings "
     "(list of dicts, each {finding_id, severity ('MAJOR'|'MINOR'), disposition ('RESOLVED'|'REJECTED'|"
     "'MOVED_TO_GAP'|'OPEN')}), revision_ref (str, optional), rq_candidates (list). Return {\"may_proceed\": bool, "
     "\"reason\": str}. RULES: (D1) C-TOTALITY: if design is not a dict, return may_proceed False (never crash). "
     "(D2) EVERY finding with severity 'MAJOR' must be a dict that HAS a 'disposition' key whose value is one of "
     "RESOLVED, REJECTED, MOVED_TO_GAP (NOT 'OPEN'). CRITICAL finding-level C-TOTALITY: a MAJOR finding that is not "
     "a dict, or lacks a 'disposition' key, or whose disposition is 'OPEN' or any unrecognized value, must be "
     "treated as NOT properly dispositioned -> may_proceed False. Do NOT treat a missing disposition as "
     "dispositioned. A MINOR finding MAY remain OPEN. (D3) if ANY finding has disposition 'RESOLVED', a non-empty "
     "revision_ref must be present else may_proceed False. (D4) rq_candidates must be a non-empty list else "
     "may_proceed False. Return ONLY JSON {\"source\": \"<full python source of research_design_audit_gate>\"}."),
   "cases":[
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR","disposition":"RESOLVED"}],"revision_ref":"RDRV-1","rq_candidates":["RQ-1"]}, True, "MAJOR resolved + revision + rqs -> proceed"),
     ({"audit_findings":[],"rq_candidates":["RQ-1"]}, True, "no findings -> proceed"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MINOR","disposition":"OPEN"}],"rq_candidates":["RQ-1"]}, True, "MINOR may stay OPEN -> proceed"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR","disposition":"OPEN"}],"rq_candidates":["RQ-1"]}, False, "OPEN MAJOR -> reject (D2)"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR"}],"revision_ref":"R1","rq_candidates":["RQ-1"]}, False, "MAJOR missing disposition -> reject (D2 finding-level C-TOTALITY)"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR","disposition":"BOGUS"}],"revision_ref":"R1","rq_candidates":["RQ-1"]}, False, "MAJOR unrecognized disposition -> reject (D2)"),
     ({"audit_findings":["notadict"],"rq_candidates":["RQ-1"]}, False, "finding not a dict -> reject no crash (D2)"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR","disposition":"RESOLVED"}],"rq_candidates":["RQ-1"]}, False, "RESOLVED but no revision_ref -> reject (D3)"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR","disposition":"MOVED_TO_GAP"}],"rq_candidates":["RQ-1"]}, True, "MAJOR MOVED_TO_GAP no revision -> proceed"),
     ({"audit_findings":[{"finding_id":"F1","severity":"MAJOR","disposition":"RESOLVED"}],"revision_ref":"R1","rq_candidates":[]}, False, "empty rq_candidates -> reject (D4)"),
     (None, False, "non-dict -> reject no crash (D1)"),
   ]},
 "rdec": {
   "fn":"validate_rdec","call":"validate_rdec(item, [\"WORKER_ASSIGNMENT\"])","key":"ok","task":"TASK-RRI-RDEC-01",
   "goal":"validate_rdec §23: decision-linked explanation, no non-load-bearing axis + C-TOTALITY",
   "spec":("Implement `validate_rdec(rdec, known_decisions)` for an RRI Research Design Explanation Contract (spec "
     "section 23). rdec is a dict with: rdec_id (str), decision (str), axis (str), why_required (str), "
     "expected_decision_effect (str), omission_risk (str), stop_condition_ref (str). known_decisions is a list of "
     "valid decision ids. Return {\"ok\": bool, \"problems\": list}. RULES: (C1) all listed fields present else ok "
     "False. (C2) decision must be in known_decisions (an axis must trace to a real decision; a decision not in "
     "known_decisions is fabricated) else ok False. (C3) expected_decision_effect must be a NON-EMPTY string — an "
     "axis that does not state how it can change the decision is non-load-bearing NOISE and must be rejected -> ok "
     "False if empty/whitespace. (C4) omission_risk must be non-empty else ok False. (C5) stop_condition_ref must "
     "be non-empty else ok False. (C6) C-TOTALITY: non-dict or wrong-type -> ok False, never crash, never ok True "
     "on malformed. Return ONLY JSON {\"source\": \"<full python source of validate_rdec>\"}."),
   "cases":[
     (_RDEC, True, "valid decision-linked RDEC -> ok"),
     ({**_RDEC,"expected_decision_effect":""}, False, "empty expected_decision_effect -> non-load-bearing reject (C3)"),
     ({**_RDEC,"expected_decision_effect":"   "}, False, "whitespace expected_decision_effect -> reject (C3)"),
     ({**_RDEC,"decision":"UNKNOWN_DEC"}, False, "fabricated decision -> reject (C2)"),
     ({k:v for k,v in _RDEC.items() if k!="omission_risk"}, False, "missing omission_risk -> reject (C1)"),
     ({**_RDEC,"omission_risk":""}, False, "empty omission_risk -> reject (C4)"),
     ({**_RDEC,"stop_condition_ref":""}, False, "empty stop_condition_ref -> reject (C5)"),
     (None, False, "non-dict -> reject no crash (C6)"),
   ]},
 "needval": {
   "fn":"validate_research_need","call":"validate_research_need(item)","key":"may_enter","task":"TASK-RRI-NEEDVAL-01",
   "goal":"validate_research_need §19-20: Need Validation (validated + alternative causes considered) before research + C-TOTALITY",
   "spec":("Implement `validate_research_need(need)` for RRI Need Validation (spec sections 19-20). A system-"
     "originated RESEARCH_NEED may enter Research Design ONLY if validated. need is a dict with: need_id (str), "
     "origin_system (str), decision_to_support (str), blocked_state (str), nec (dict with validated (bool), "
     "origin_decision (str), observed_block_refs (list), alternative_causes (list), research_requirement_summary "
     "(str)). Return {\"may_enter\": bool, \"reason\": str}. RULES: (N1) C-TOTALITY: if need is not a dict, return "
     "may_enter False (never crash). (N2) nec must be present and a dict else may_enter False. (N3) nec['validated'] "
     "must be exactly True else may_enter False. (N4) nec['alternative_causes'] must be a NON-EMPTY list — Need "
     "Validation must have considered non-research causes (do not trust the need's own hint as sole root); empty -> "
     "may_enter False. (N5) nec['observed_block_refs'] must be a non-empty list else may_enter False. (N6) "
     "decision_to_support must be a non-empty string else may_enter False. "
     "Return ONLY JSON {\"source\": \"<full python source of validate_research_need>\"}."),
   "cases":[
     (_NEED, True, "validated NEC + alternatives + observed block -> may enter"),
     ({**_NEED,"nec":{**_NEC,"validated":False}}, False, "nec not validated -> reject (N3)"),
     ({**_NEED,"nec":{**_NEC,"alternative_causes":[]}}, False, "no alternative_causes -> reject (N4)"),
     ({k:v for k,v in _NEED.items() if k!="nec"}, False, "missing nec -> reject (N2)"),
     ({**_NEED,"nec":{**_NEC,"observed_block_refs":[]}}, False, "no observed block -> reject (N5)"),
     ({**_NEED,"decision_to_support":""}, False, "empty decision_to_support -> reject (N6)"),
     (None, False, "non-dict -> reject no crash (N1)"),
   ]},
 "transform": {
   "fn": "validate_transformation", "call": "validate_transformation(item)", "key": "ok", "task": "TASK-RRI-XFORM-01",
   "goal": "validate_transformation §31: explainability structure + grounded refs + C-TOTALITY",
   "spec": ("Implement `validate_transformation(xform)` for an RRI EXPLAINABLE_TRANSFORMATION (spec section 31). "
     "xform is a dict with: transformation_id (str), transformation_type (one of "+XT+"), input_refs (list), "
     "output_refs (list), basis_refs (list), operation (str), retained_uncertainty (list), excluded_scope (list), "
     "revision_triggers (list). Return {\"ok\": bool, \"problems\": list}. RULES: (T1) all listed fields present "
     "else ok False. (T2) transformation_type must be one of the allowed values else ok False. (T3) input_refs, "
     "output_refs, basis_refs must EACH be a non-empty list (a grounded transformation traces from inputs, to "
     "outputs, on a basis) else ok False. (T4) retained_uncertainty, excluded_scope, revision_triggers must each "
     "be a list (the explanation structure must exist; may be empty) else ok False. (T5) operation must be a "
     "non-empty string else ok False. (T6) C-TOTALITY: non-dict or wrong-type field -> ok False, never crash, never "
     "ok True on malformed. Return ONLY JSON {\"source\": \"<full python source of validate_transformation>\"}."),
   "cases": [
     ({"transformation_id":"X1","transformation_type":"EVIDENCE_TO_CLAIM","input_refs":["E1"],"output_refs":["C1"],"basis_refs":["B1"],"operation":"admit","retained_uncertainty":[],"excluded_scope":[],"revision_triggers":["T"]}, True, "valid"),
     ({"transformation_id":"X1","transformation_type":"EVIDENCE_TO_CLAIM","input_refs":[],"output_refs":["C1"],"basis_refs":["B1"],"operation":"admit","retained_uncertainty":[],"excluded_scope":[],"revision_triggers":["T"]}, False, "empty input_refs (T3)"),
     ({"transformation_id":"X1","transformation_type":"EVIDENCE_TO_CLAIM","input_refs":["E1"],"output_refs":["C1"],"basis_refs":[],"operation":"admit","retained_uncertainty":[],"excluded_scope":[],"revision_triggers":["T"]}, False, "empty basis_refs (T3)"),
     ({"transformation_id":"X1","transformation_type":"BOGUS","input_refs":["E1"],"output_refs":["C1"],"basis_refs":["B1"],"operation":"admit","retained_uncertainty":[],"excluded_scope":[],"revision_triggers":["T"]}, False, "bad type (T2)"),
     ({"transformation_id":"X1","transformation_type":"EVIDENCE_TO_CLAIM","input_refs":["E1"],"output_refs":["C1"],"basis_refs":["B1"],"operation":"admit","retained_uncertainty":[],"excluded_scope":[]}, False, "missing revision_triggers (T1)"),
     ({"transformation_id":"X1","transformation_type":"EVIDENCE_TO_CLAIM","input_refs":["E1"],"output_refs":["C1"],"basis_refs":["B1"],"operation":"","retained_uncertainty":[],"excluded_scope":[],"revision_triggers":["T"]}, False, "empty operation (T5)"),
     ({"transformation_id":"X1","transformation_type":"EVIDENCE_TO_CLAIM","input_refs":["E1"],"output_refs":["C1"],"basis_refs":["B1"],"operation":"admit","retained_uncertainty":"x","excluded_scope":[],"revision_triggers":["T"]}, False, "retained_uncertainty not list (T4)"),
     (None, False, "non-dict (T6)"),
   ]},
 "axis": {
   "fn": "validate_research_axis", "call": "validate_research_axis(item, [\"WORKER_ASSIGNMENT\"])", "key": "ok", "task": "TASK-RRI-AXIS-01",
   "goal": "validate_research_axis §24: supports real decisions + unknown handling + required needs RDEC + C-TOTALITY",
   "spec": ("Implement `validate_research_axis(axis, known_decisions)` for an RRI Research Axis (spec section 24). "
     "axis is a dict with: axis_id (str), supports_decisions (list of decision ids), required (bool), "
     "safe_behavior_if_unknown (str), rdec_ref (str, may be empty). known_decisions is a list of valid decision "
     "ids. Return {\"ok\": bool, \"problems\": list}. RULES: (A1) all listed fields present else ok False. (A2) "
     "supports_decisions must be a NON-EMPTY list and EVERY element must be in known_decisions (an axis must "
     "support a real decision; a decision not in known_decisions is fabricated) else ok False. (A3) "
     "safe_behavior_if_unknown must be a non-empty string (unknown handling must be defined; unknown is not "
     "negative) else ok False. (A4) if required is True, rdec_ref must be a non-empty string (a required axis needs "
     "a decision-linked RDEC) else ok False. (A5) C-TOTALITY: non-dict or wrong-type -> ok False, never crash. "
     "Return ONLY JSON {\"source\": \"<full python source of validate_research_axis>\"}."),
   "cases": [
     ({"axis_id":"A1","supports_decisions":["WORKER_ASSIGNMENT"],"required":True,"safe_behavior_if_unknown":"defer","rdec_ref":"RDEC-1"}, True, "valid required axis"),
     ({"axis_id":"A1","supports_decisions":[],"required":True,"safe_behavior_if_unknown":"defer","rdec_ref":"RDEC-1"}, False, "empty supports_decisions (A2)"),
     ({"axis_id":"A1","supports_decisions":["UNKNOWN_DEC"],"required":True,"safe_behavior_if_unknown":"defer","rdec_ref":"RDEC-1"}, False, "fabricated decision (A2)"),
     ({"axis_id":"A1","supports_decisions":["WORKER_ASSIGNMENT"],"required":True,"safe_behavior_if_unknown":"defer","rdec_ref":""}, False, "required but no rdec_ref (A4)"),
     ({"axis_id":"A1","supports_decisions":["WORKER_ASSIGNMENT"],"required":False,"safe_behavior_if_unknown":"defer","rdec_ref":""}, True, "optional axis no rdec_ref -> ok"),
     ({"axis_id":"A1","supports_decisions":["WORKER_ASSIGNMENT"],"required":True,"safe_behavior_if_unknown":"","rdec_ref":"RDEC-1"}, False, "empty safe_behavior_if_unknown (A3)"),
     (None, False, "non-dict (A5)"),
   ]},
 "rqgate": {
   "fn": "validate_rq_candidate", "call": "validate_rq_candidate(item, [\"STARTUP_COST\"])", "key": "ok", "task": "TASK-RRI-RQC-01",
   "goal": "validate_rq_candidate §25: derived from real axes + decision relevance + required needs RDEC + C-TOTALITY",
   "spec": ("Implement `validate_rq_candidate(rqc, known_axes)` for an RRI RQ Candidate (spec section 25). rqc is a "
     "dict with: rq_candidate_id (str), question (str), derived_from_axes (list of axis ids), decision_relevance "
     "(str), priority (one of REQUIRED|OPTIONAL|DEFERRED), rdec_refs (list). known_axes is a list of valid axis "
     "ids. Return {\"ok\": bool, \"problems\": list}. RULES: (Q1) all listed fields present else ok False. (Q2) "
     "derived_from_axes must be a NON-EMPTY list and EVERY element must be in known_axes (an RQ must derive from "
     "real axes; an axis id not in known_axes is fabricated) else ok False. (Q3) decision_relevance must be a "
     "non-empty string else ok False. (Q4) priority must be one of REQUIRED, OPTIONAL, DEFERRED else ok False. "
     "(Q5) if priority is 'REQUIRED', rdec_refs must be a non-empty list (a required RQ needs a decision-linked "
     "RDEC) else ok False. (Q6) C-TOTALITY: non-dict or wrong-type -> ok False, never crash. "
     "Return ONLY JSON {\"source\": \"<full python source of validate_rq_candidate>\"}."),
   "cases": [
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":["STARTUP_COST"],"decision_relevance":"picks worker","priority":"REQUIRED","rdec_refs":["RDEC-1"]}, True, "valid required RQ"),
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":[],"decision_relevance":"x","priority":"REQUIRED","rdec_refs":["RDEC-1"]}, False, "empty derived_from_axes (Q2)"),
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":["UNKNOWN_AXIS"],"decision_relevance":"x","priority":"REQUIRED","rdec_refs":["RDEC-1"]}, False, "fabricated axis (Q2)"),
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":["STARTUP_COST"],"decision_relevance":"","priority":"REQUIRED","rdec_refs":["RDEC-1"]}, False, "empty decision_relevance (Q3)"),
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":["STARTUP_COST"],"decision_relevance":"x","priority":"BOGUS","rdec_refs":["RDEC-1"]}, False, "bad priority (Q4)"),
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":["STARTUP_COST"],"decision_relevance":"x","priority":"REQUIRED","rdec_refs":[]}, False, "REQUIRED no rdec_refs (Q5)"),
     ({"rq_candidate_id":"Q1","question":"?","derived_from_axes":["STARTUP_COST"],"decision_relevance":"x","priority":"OPTIONAL","rdec_refs":[]}, True, "OPTIONAL no rdec_refs -> ok"),
     (None, False, "non-dict (Q6)"),
   ]},
}

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)
def serving(ep, name):
    try:
        with urllib.request.urlopen(ep.replace("/chat/completions","/models"), timeout=4) as r:
            return any(name in m.get("id","") for m in json.load(r).get("data",[]))
    except Exception: return False
def swap_to(target):
    global CURRENT_MODEL
    t0=time.time(); frm=CURRENT_MODEL
    _proc("SWAP_START", {"to":target,"from":frm}, _iso(t0))   # F-1 primitive (real ts)
    if target=="coder": sh("docker rm -f qwen36_vllm"); sh(f"bash {SCRIPTS}/serve_codernext_vllm.sh"); ep,name,cont=CODER_EP,CODER_M,"codernext_vllm"
    else: sh("docker rm -f codernext_vllm"); sh(f"bash {SCRIPTS}/serve_qwen36_vllm.sh"); ep,name,cont=QWEN_EP,QWEN_M,"qwen36_vllm"
    ok=False
    for _ in range(120):
        if serving(ep,name): ok=True; break
        if cont not in sh("docker ps --format '{{.Names}}'").stdout: break
        time.sleep(5)
    lat=round(time.time()-t0,1); SWAPS.append({"to":target,"latency_s":lat,"ok":ok})
    _proc("SWAP_END", {"to":target,"from":frm,"ok":ok}, _iso())  # F-1 primitive (real ts) -> duration は log から導出
    if ok: CURRENT_MODEL=target
    print(f"  [swap #{len(SWAPS)} -> {target}] {'OK' if ok else 'FAIL'} in {lat}s", flush=True); return ok,lat
def chat(ep,model,system,user,max_tokens=1100,seed=0):
    body=json.dumps({"model":model,"temperature":0,"seed":seed,"max_tokens":max_tokens,"chat_template_kwargs":{"enable_thinking":False},"messages":[{"role":"system","content":system},{"role":"user","content":user}]}).encode()
    with urllib.request.urlopen(urllib.request.Request(ep,data=body,headers={"Content-Type":"application/json"}),timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""
def parse_findings(a):
    i,j=a.find("{"),a.rfind("}")
    if 0<=i<j:
        try: return json.loads(a[i:j+1]).get("findings",[]) or []
        except Exception: pass
    return []
def extract(raw, fn):
    i,j=raw.find("{"),raw.rfind("}")
    if 0<=i<j:
        try:
            o=json.loads(raw[i:j+1])
            if isinstance(o.get("source"),str) and f"def {fn}" in o["source"]: return o["source"]
        except Exception: pass
    m=re.search(rf"(def {fn}.*)", raw, re.S); return m.group(1) if m else None
def run_tests(source, cfg):
    if not source: return {"status":"no_source","passed":False,"cases":0,"failures":["no source"]}
    harness=source+"\n\nimport json\n_c="+repr(cfg["cases"])+"\n_r=[]\nfor item,exp,lbl in _c:\n    try:\n        out="+cfg["call"]+"\n        ok=(isinstance(out,dict) and out.get("+repr(cfg["key"])+")==exp)\n        _r.append({'lbl':lbl,'ok':ok,'got':(out.get("+repr(cfg["key"])+") if isinstance(out,dict) else 'NOT_DICT')})\n    except Exception as e:\n        _r.append({'lbl':lbl,'ok':False,'got':'CRASH:%s'%type(e).__name__})\nprint(json.dumps(_r))\n"
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/"c.py"; f.write_text(harness)
        p=subprocess.run([sys.executable,str(f)],capture_output=True,text=True,timeout=15)
    if p.returncode!=0: return {"status":"error","passed":False,"cases":len(cfg["cases"]),"failures":[p.stderr.strip()[:200]]}
    try: res=json.loads(p.stdout.strip().splitlines()[-1])
    except Exception: return {"status":"unparseable","passed":False,"cases":len(cfg["cases"]),"failures":[p.stdout[:150]]}
    fails=[r for r in res if not r["ok"]]
    return {"status":"executed","passed":not fails,"cases":len(res),"n_pass":len(res)-len(fails),"failures":[{"lbl":r["lbl"],"got":r["got"]} for r in fails]}

def main(name):
    global CURRENT_TASK, CURRENT_MODEL
    cfg=SLICES[name]; trial={"slice":name,"swaps":SWAPS,"authority":"BOOTSTRAP_REPORTED"}; final=None
    try:
        os.makedirs(RUN_SOR, exist_ok=True)
        if True:  # F-1: DW SoR = persistent RUN_SOR。temp dir は hermetic test 専用(run_tests のみ)
            os.environ["DW_DATA_DIR"]=RUN_SOR; import importlib; importlib.reload(W)
            TASK=f"{cfg['task']}-{int(time.time())}"; mgr="claude-manager"; CURRENT_TASK=TASK; CURRENT_MODEL="qwen"
            def ts(): return _iso()  # 実 wall-clock ISO。process trace timeline を authoritative にする
            W.create_task(TASK,"RRI",cfg["goal"],{"related_failure_patterns":["IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION"]},ts(),mgr)
            _proc("RUN_START",{"slice":name},_iso())
            W.record_plan(TASK,{"narrow_goal":cfg["goal"]},ts(),mgr)
            assert swap_to("coder")[0],"coder swap failed"
            raw=chat(CODER_EP,CODER_M,"You are a careful Python coding worker. Implement EXACTLY the spec.",cfg["spec"],seed=3)
            final=extract(raw,cfg["fn"]); tr=run_tests(final,cfg)
            W.record_generate(TASK,{"identity":"qwen3-coder-next@8006","run_id":"gen1","diff":final,"test_result":tr,"problems":tr.get("failures",[])},ts())
            print(f"[GENERATE] {tr.get('status')} passed={tr.get('passed')} {tr.get('n_pass')}/{tr.get('cases')}",flush=True)
            assert swap_to("qwen")[0],"qwen swap failed"
            AUD=("You are an independent code auditor (separate model from the coder). Attack the function for fail-open on malformed input, "
                 "missing required-field checks, fabricated-reference acceptance, wrong-enum acceptance, or scope expansion. "
                 "Return ONLY JSON {\"findings\":[{\"category\":\"...\",\"evidence\":\"...\"}]}.")
            af=parse_findings(chat(QWEN_EP,QWEN_M,AUD,f"CODE:\n{final}\nTEST_RESULT:\n{json.dumps(tr)}\n\nReturn JSON.",max_tokens=600,seed=41))
            findings=[{"finding_id":f"F{k}","category":"other","severity":"MAJOR","evidence":f.get("evidence",""),"status":"OPEN"} for k,f in enumerate(af)]
            W.record_audit(TASK,{"identity":"qwen3.6@8005-auditor","run_id":"aud1","findings":findings},ts())
            print(f"[AUDIT] findings={len(findings)}",flush=True)
            rework=0
            while True:
                st,_=W.derive_state(TASK)
                if st!="AUDIT_FAILED" or rework>=W.REWORK_ESCALATION_THRESHOLD: break
                assert swap_to("coder")[0],"coder swap failed (rework)"
                fb=json.dumps({"test_failures":tr.get("failures"),"audit":[f["evidence"] for f in findings]},ensure_ascii=False)[:900]
                raw=chat(CODER_EP,CODER_M,"Fix ALL findings; resubmit FULL corrected source.",cfg["spec"]+"\nPRIOR FAILED:\n"+fb,seed=4+rework)
                final=extract(raw,cfg["fn"]); tr=run_tests(final,cfg)
                W.record_regenerate(TASK,{"identity":"qwen3-coder-next@8006","run_id":f"regen{rework+1}","diff":final,"test_result":tr},ts())
                print(f"[REGEN #{rework+1}] passed={tr.get('passed')} {tr.get('n_pass')}/{tr.get('cases')}",flush=True)
                assert swap_to("qwen")[0],"qwen swap failed (re-audit)"
                af=parse_findings(chat(QWEN_EP,QWEN_M,AUD,f"CODE:\n{final}\nTEST_RESULT:\n{json.dumps(tr)}\n\nReturn JSON.",max_tokens=600,seed=42+rework))
                findings=[{"finding_id":f"F{k}","category":"other","severity":"MAJOR","evidence":f.get("evidence",""),"status":"OPEN"} for k,f in enumerate(af)]
                W.record_audit(TASK,{"identity":"qwen3.6@8005-auditor","run_id":f"aud{rework+2}","findings":findings},ts())
                print(f"[re-AUDIT] findings={len(findings)}",flush=True); rework+=1
            st,view=W.derive_state(TASK); trial["final_state"]=st
            if st=="READY_FOR_UPPER_REVIEW":
                W.record_upper_review(TASK,{"verdict":"tests pass + audit clean"},ts(),mgr)
                try:
                    W.propose_complete(TASK,[{"observed":f"{cfg['fn']} passed {tr.get('n_pass')}/{tr.get('cases')}"}],[{"proposed":f"RRI {cfg['fn']} implemented; passes tested cases","scope":"tested cases only","record_ids":[]}],[],ts(),mgr)
                    trial["completed"]=True; print("[COMPLETE]",flush=True)
                except W.WorkflowViolation as e: trial["completed"]=False; print(f"[REJECTED] {e}",flush=True)
            else: trial["completed"]=False; print(f"[NO COMPLETE] {st}",flush=True)
    finally:
        _proc("RUN_END",{"slice":name},_iso())   # F-1: run 境界 primitive(restore swap の前に閉じる)
        if not serving(QWEN_EP,QWEN_M): swap_to("qwen")
        ok=[s for s in SWAPS if s["ok"]]
        trial.update({"swap_count":len(SWAPS),"swap_latencies_s":[s["latency_s"] for s in SWAPS],"swap_failures":len([s for s in SWAPS if not s["ok"]]),"avg_swap_s":round(sum(s["latency_s"] for s in ok)/len(ok),1) if ok else None,"final_source":final,
                      "dw_task_id":CURRENT_TASK,
                      "authoritative_process_trace":f"dw.workcell.derive_process_trace({CURRENT_TASK!r}) over run_sor/events.jsonl — NOT these self-reported metrics"})
        Path(f"/home/takasan/egl/experiments/rri_{name}_slice.json").write_text(json.dumps(trial,ensure_ascii=False,indent=2))
        print(f"[DONE {name}] completed={trial.get('completed')} state={trial.get('final_state')} swaps={trial['swap_count']} failures={trial['swap_failures']} avg={trial['avg_swap_s']}s dw_task={CURRENT_TASK}",flush=True)

if __name__=="__main__":
    main(sys.argv[1])
