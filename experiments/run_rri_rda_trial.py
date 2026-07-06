#!/usr/bin/env python3
"""Instrumented A-mode trial (Candidate D の実行) = step4 RRI-through-DW の開始。

real RRI slice(research_design_audit_gate, §27-28）を DW loop に、sequential swap で流す:
GENERATE=Qwen3-Coder-Next(8006) → swap → AUDIT=Qwen3.6(8005) → (swap → REGENERATE)。
各 swap の latency / count / failure を計測(= A vs B を分ける swap 頻度の実測)。
load-bearing test = coder のコードを subprocess 実行。終了時に必ず Qwen3.6 を restore。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import socket
from pathlib import Path

sys.path.insert(0, "/home/takasan/dev-workcell")
from dw import workcell as W  # noqa: E402

QWEN_EP, QWEN_M = "http://localhost:8005/v1/chat/completions", "Qwen3.6-35B-A3B"
CODER_EP, CODER_M = "http://localhost:8006/v1/chat/completions", "Qwen3-Coder-Next"
SCRIPTS = "/home/takasan/models_trtllm"
SWAPS = []  # instrumentation


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def serving(ep, name):
    try:
        with urllib.request.urlopen(ep.replace("/chat/completions", "/models"), timeout=4) as r:
            return any(name in m.get("id", "") for m in json.load(r).get("data", []))
    except Exception:
        return False


def swap_to(target):
    """target='coder'|'qwen'。docker 履き替え + poll + 計測。返り: (ok, latency_s)。"""
    t0 = time.time()
    if target == "coder":
        sh("docker rm -f qwen36_vllm")
        sh(f"bash {SCRIPTS}/serve_codernext_vllm.sh")
        ep, name, cont = CODER_EP, CODER_M, "codernext_vllm"
    else:
        sh("docker rm -f codernext_vllm")
        sh(f"bash {SCRIPTS}/serve_qwen36_vllm.sh")
        ep, name, cont = QWEN_EP, QWEN_M, "qwen36_vllm"
    ok = False
    for _ in range(120):
        if serving(ep, name):
            ok = True
            break
        if cont not in sh("docker ps --format '{{.Names}}'").stdout:
            break  # container exited = failure
        time.sleep(5)
    lat = round(time.time() - t0, 1)
    SWAPS.append({"to": target, "latency_s": lat, "ok": ok})
    print(f"  [swap #{len(SWAPS)} -> {target}] {'OK' if ok else 'FAIL'} in {lat}s")
    return ok, lat


def chat(ep, model, system, user, max_tokens=1100, seed=0):
    body = json.dumps({"model": model, "temperature": 0, "seed": seed, "max_tokens": max_tokens,
                       "chat_template_kwargs": {"enable_thinking": False},
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(ep, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.load(r)["choices"][0]["message"].get("content") or ""


# ── RRI slice: research_design_audit_gate (§27-28) — findings dispositioned before proceeding ──
SLICE_SPEC = (
    "Implement `research_design_audit_gate(design)` for an RRI Research Design (spec sections 27-28). It decides "
    "whether a research design may proceed to an Approved RQ Set. design is a dict with: audit_findings (list of "
    "dicts, each {finding_id, severity ('MAJOR'|'MINOR'), disposition ('RESOLVED'|'REJECTED'|'MOVED_TO_GAP'|'OPEN')}), "
    "revision_ref (str, optional), rq_candidates (list). Return {\"may_proceed\": bool, \"reason\": str}. RULES: "
    "(D1) C-TOTALITY: if design is not a dict, return may_proceed False (never crash). (D2) EVERY finding with "
    "severity 'MAJOR' must have a disposition that is NOT 'OPEN' (it must be RESOLVED, REJECTED, or MOVED_TO_GAP); an "
    "OPEN MAJOR finding -> may_proceed False. A MINOR finding MAY remain OPEN. (D3) if ANY finding has disposition "
    "'RESOLVED', a non-empty revision_ref must be present (the revision that resolved it); RESOLVED findings without "
    "a revision_ref -> may_proceed False. (D4) rq_candidates must be a non-empty list else may_proceed False. "
    "Return ONLY JSON {\"source\": \"<full python source of research_design_audit_gate>\"}."
)
GOOD = {"audit_findings": [{"finding_id": "F1", "severity": "MAJOR", "disposition": "RESOLVED"}], "revision_ref": "RDRV-1", "rq_candidates": ["RQ-1"]}
CASES = [
    (GOOD, True, "MAJOR resolved + revision + rqs -> proceed"),
    ({"audit_findings": [], "rq_candidates": ["RQ-1"]}, True, "no findings -> proceed (no revision needed)"),
    ({"audit_findings": [{"finding_id": "F1", "severity": "MINOR", "disposition": "OPEN"}], "rq_candidates": ["RQ-1"]}, True, "MINOR may stay OPEN -> proceed"),
    ({"audit_findings": [{"finding_id": "F1", "severity": "MAJOR", "disposition": "OPEN"}], "rq_candidates": ["RQ-1"]}, False, "OPEN MAJOR -> reject (D2)"),
    ({"audit_findings": [{"finding_id": "F1", "severity": "MAJOR", "disposition": "RESOLVED"}], "rq_candidates": ["RQ-1"]}, False, "RESOLVED but no revision_ref -> reject (D3)"),
    ({**GOOD, "rq_candidates": []}, False, "empty rq_candidates -> reject (D4)"),
    (None, False, "non-dict -> reject no crash (D1)"),
]


def parse_findings(araw):
    """robust: 監査応答が malformed/truncated でも crash せず findings 抽出。"""
    i, j = araw.find("{"), araw.rfind("}")
    if 0 <= i < j:
        try:
            return json.loads(araw[i:j + 1]).get("findings", []) or []
        except Exception:
            pass
    return []


def extract(raw):
    i, j = raw.find("{"), raw.rfind("}")
    if 0 <= i < j:
        try:
            o = json.loads(raw[i:j + 1])
            if isinstance(o.get("source"), str) and "def research_design_audit_gate" in o["source"]:
                return o["source"]
        except Exception:
            pass
    m = re.search(r"(def research_design_audit_gate.*)", raw, re.S)
    return m.group(1) if m else None


def run_tests(source):
    if not source:
        return {"status": "no_source", "passed": False, "cases": 0, "failures": ["no source"]}
    harness = source + "\n\nimport json\n_c=" + repr(CASES) + "\n" + r"""
_r=[]
for design,exp,lbl in _c:
    try:
        out=research_design_audit_gate(design)
        ok=(isinstance(out,dict) and out.get("may_proceed")==exp)
        _r.append({"lbl":lbl,"ok":ok,"got":(out.get("may_proceed") if isinstance(out,dict) else "NOT_DICT")})
    except Exception as e:
        _r.append({"lbl":lbl,"ok":False,"got":"CRASH:%s"%type(e).__name__})
print(json.dumps(_r))
"""
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "c.py"
        f.write_text(harness)
        p = subprocess.run([sys.executable, str(f)], capture_output=True, text=True, timeout=15)
    if p.returncode != 0:
        return {"status": "error", "passed": False, "cases": len(CASES), "failures": [p.stderr.strip()[:200]]}
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"status": "unparseable", "passed": False, "cases": len(CASES), "failures": [p.stdout[:150]]}
    fails = [r for r in res if not r["ok"]]
    return {"status": "executed", "passed": not fails, "cases": len(res), "n_pass": len(res) - len(fails),
            "failures": [{"lbl": r["lbl"], "got": r["got"]} for r in fails]}


def main():
    trial = {"mode": "A (sequential swap)", "task": "RRI research_design_audit_gate (§27-28)", "swaps": SWAPS}
    final_source = None
    try:
        print("### Instrumented A-mode trial: RRI validate_iec through DW ###\n")
        with tempfile.TemporaryDirectory() as dd:
            os.environ["DW_DATA_DIR"] = dd
            import importlib
            importlib.reload(W)
            TASK, mgr = "TASK-RRI-RDA-01", "claude-manager"
            tk = [0]
            def ts():
                tk[0] += 1
                return f"2026-07-07T12:00:{tk[0]:02d}Z"
            kp = {"packet_type": "KNOWLEDGE_PACKET", "related_failure_patterns": ["IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION"]}
            W.create_task(TASK, "RRI", "implement research_design_audit_gate (§27-28, findings dispositioned before proceeding)", kp, ts(), mgr)
            W.record_plan(TASK, {"narrow_goal": "research_design_audit_gate: D1 C-TOTALITY / D2 MAJOR must be dispositioned (no OPEN) / D3 RESOLVED needs revision_ref / D4 rq_candidates"}, ts(), mgr)

            # GENERATE (Coder-Next)
            assert swap_to("coder")[0], "coder swap failed"
            raw = chat(CODER_EP, CODER_M, "You are a careful Python coding worker. Implement EXACTLY the spec.", SLICE_SPEC, seed=3)
            final_source = extract(raw)
            tr = run_tests(final_source)
            W.record_generate(TASK, {"identity": "qwen3-coder-next@8006", "run_id": "gen1", "diff": final_source, "test_result": tr, "problems": tr.get("failures", [])}, ts())
            print(f"[GENERATE Coder-Next] test={tr.get('status')} passed={tr.get('passed')} {tr.get('n_pass')}/{tr.get('cases')}")

            # AUDIT (Qwen3.6) — swap
            assert swap_to("qwen")[0], "qwen swap failed"
            AUD = ("You are an independent code auditor (separate model from the coder). Attack validate_iec for: R3 "
                   "fabricated basis_ref allowed, R4 fail-open/crash on malformed, missing required-field check, wrong "
                   "strategy accepted, or scope expansion. Return ONLY JSON {\"findings\":[{\"category\":\"...\",\"evidence\":\"...\"}]}.")
            araw = chat(QWEN_EP, QWEN_M, AUD, f"CODE:\n{final_source}\nTEST_RESULT:\n{json.dumps(tr)}\n\nReturn JSON.", max_tokens=600, seed=41)
            af = parse_findings(araw)
            findings = [{"finding_id": f"F{k}", "category": (f.get("category", "other") or "other").lower().replace(" ", "_")[:40] if isinstance(f.get("category"), str) else "other", "severity": "MAJOR", "evidence": f.get("evidence", ""), "status": "OPEN"} for k, f in enumerate(af)]
            for f in findings:
                if f["category"] not in W.FINDING_CATEGORIES:
                    f["category"] = "scope_expansion" if "scope" in f["category"] else "other"
            W.record_audit(TASK, {"identity": "qwen3.6@8005-auditor", "run_id": "aud1", "findings": findings}, ts())
            print(f"[AUDIT Qwen3.6] findings={[f['category'] for f in findings]}")

            rework = 0
            while True:
                state, _ = W.derive_state(TASK)
                if state != "AUDIT_FAILED" or rework >= W.REWORK_ESCALATION_THRESHOLD:
                    break
                assert swap_to("coder")[0], "coder swap failed (rework)"
                fb = json.dumps({"test_failures": tr.get("failures"), "audit": [f["evidence"] for f in findings]}, ensure_ascii=False)[:900]
                raw = chat(CODER_EP, CODER_M, "Fix ALL findings; resubmit FULL corrected source.", SLICE_SPEC + "\nPRIOR FAILED:\n" + fb, seed=3 + rework + 1)
                final_source = extract(raw)
                tr = run_tests(final_source)
                W.record_regenerate(TASK, {"identity": "qwen3-coder-next@8006", "run_id": f"regen{rework+1}", "diff": final_source, "test_result": tr}, ts())
                print(f"[REGENERATE #{rework+1} Coder-Next] passed={tr.get('passed')} {tr.get('n_pass')}/{tr.get('cases')}")
                assert swap_to("qwen")[0], "qwen swap failed (re-audit)"
                araw = chat(QWEN_EP, QWEN_M, AUD, f"CODE:\n{final_source}\nTEST_RESULT:\n{json.dumps(tr)}\n\nReturn JSON.", max_tokens=600, seed=41 + rework + 1)
                af = parse_findings(araw)
                findings = [{"finding_id": f"F{k}", "category": "other", "severity": "MAJOR", "evidence": f.get("evidence", ""), "status": "OPEN"} for k, f in enumerate(af)]
                W.record_audit(TASK, {"identity": "qwen3.6@8005-auditor", "run_id": f"aud{rework+2}", "findings": findings}, ts())
                print(f"[re-AUDIT Qwen3.6] findings={len(findings)}")
                rework += 1

            state, view = W.derive_state(TASK)
            print(f"\n[state] {state}")
            trial["final_state"] = state
            if state == "READY_FOR_UPPER_REVIEW":
                W.record_upper_review(TASK, {"verdict": "tests pass + audit clean"}, ts(), mgr)
                try:
                    pkt = W.propose_complete(TASK, [{"observed": f"research_design_audit_gate passed {tr.get('n_pass')}/{tr.get('cases')} load-bearing tests"}],
                                             [{"proposed": "RRI research_design_audit_gate (§27-28) implemented; passes tested finding-disposition + C-TOTALITY cases", "scope": "tested cases only", "record_ids": []}], [], ts(), mgr)
                    trial["completed"] = True
                    print("[COMPLETE] RESULT_PACKET (proposed_claims only)")
                except W.WorkflowViolation as e:
                    trial["completed"] = False
                    print(f"[COMPLETE REJECTED] {e}")
            else:
                trial["completed"] = False
                print(f"[NO COMPLETE] {state}")
    finally:
        # 必ず Qwen3.6 を restore（downstream engine）
        if not serving(QWEN_EP, QWEN_M):
            print("\n[restore] swapping back to Qwen3.6…")
            swap_to("qwen")
        # instrumentation summary
        swaps_ok = [s for s in SWAPS if s["ok"]]
        trial["swap_count"] = len(SWAPS)
        trial["swap_latencies_s"] = [s["latency_s"] for s in SWAPS]
        trial["swap_failures"] = len([s for s in SWAPS if not s["ok"]])
        trial["avg_swap_s"] = round(sum(s["latency_s"] for s in swaps_ok) / len(swaps_ok), 1) if swaps_ok else None
        trial["final_source"] = final_source
        Path("/home/takasan/egl/experiments/rri_rda_trial.json").write_text(json.dumps(trial, ensure_ascii=False, indent=2))
        print(f"\n=== instrumentation ===")
        print(f"  swaps: {trial['swap_count']} (failures {trial['swap_failures']}), latencies {trial['swap_latencies_s']}s, avg {trial['avg_swap_s']}s")
        print(f"  completed: {trial.get('completed')}  final_state: {trial.get('final_state')}")
        print(f"  → swaps/item = {trial['swap_count']} (this item). A vs B は複数 item で判断。")


if __name__ == "__main__":
    main()
