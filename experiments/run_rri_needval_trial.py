#!/usr/bin/env python3
"""Instrumented A-mode trial (Candidate D の実行) = step4 RRI-through-DW の開始。

real RRI slice(validate_research_need, §19-20）を DW loop に、sequential swap で流す:
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


# ── RRI slice: validate_research_need (§19-20) — Need Validation before research ──
SLICE_SPEC = (
    "Implement `validate_research_need(need)` for RRI Need Validation (spec sections 19-20). A system-originated "
    "RESEARCH_NEED may enter Research Design ONLY if it has been validated. need is a dict with: need_id (str), "
    "origin_system (str), decision_to_support (str), blocked_state (str), nec (dict = Need Explanation Contract with "
    "validated (bool), origin_decision (str), observed_block_refs (list), alternative_causes (list), "
    "research_requirement_summary (str)). Return {\"may_enter\": bool, \"reason\": str}. RULES: (N1) C-TOTALITY: "
    "if need is not a dict, return may_enter False (never crash). (N2) nec must be present and a dict else may_enter "
    "False (a need without a Need Explanation Contract is not validated). (N3) nec['validated'] must be exactly True "
    "else may_enter False. (N4) nec['alternative_causes'] must be a NON-EMPTY list — Need Validation must have "
    "considered non-research causes (do not trust the need's own hint as the sole root cause); empty -> may_enter "
    "False. (N5) nec['observed_block_refs'] must be a non-empty list (the block must be real/observed) else "
    "may_enter False. (N6) decision_to_support must be a non-empty string else may_enter False. "
    "Return ONLY JSON {\"source\": \"<full python source of validate_research_need>\"}."
)
GOOD_NEC = {"validated": True, "origin_decision": "WORKER_ASSIGNMENT", "observed_block_refs": ["DWSTATE-1"], "alternative_causes": ["adapter unavailable", "policy undefined"], "research_requirement_summary": "no role-validation state exists"}
GOOD = {"need_id": "RNEED-1", "origin_system": "DW", "decision_to_support": "WORKER_ASSIGNMENT", "blocked_state": "PLANNING", "nec": GOOD_NEC}
CASES = [
    (GOOD, True, "validated NEC + alternatives + observed block -> may enter"),
    ({**GOOD, "nec": {**GOOD_NEC, "validated": False}}, False, "nec not validated -> reject (N3)"),
    ({**GOOD, "nec": {**GOOD_NEC, "alternative_causes": []}}, False, "no alternative_causes considered -> reject (N4)"),
    ({k: v for k, v in GOOD.items() if k != "nec"}, False, "missing nec -> reject (N2)"),
    ({**GOOD, "nec": {**GOOD_NEC, "observed_block_refs": []}}, False, "no observed block -> reject (N5)"),
    ({**GOOD, "decision_to_support": ""}, False, "empty decision_to_support -> reject (N6)"),
    (None, False, "non-dict -> reject no crash (N1)"),
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
            if isinstance(o.get("source"), str) and "def validate_research_need" in o["source"]:
                return o["source"]
        except Exception:
            pass
    m = re.search(r"(def validate_research_need.*)", raw, re.S)
    return m.group(1) if m else None


def run_tests(source):
    if not source:
        return {"status": "no_source", "passed": False, "cases": 0, "failures": ["no source"]}
    harness = source + "\n\nimport json\n_c=" + repr(CASES) + "\n" + r"""
_r=[]
for need,exp,lbl in _c:
    try:
        out=validate_research_need(need)
        ok=(isinstance(out,dict) and out.get("may_enter")==exp)
        _r.append({"lbl":lbl,"ok":ok,"got":(out.get("may_enter") if isinstance(out,dict) else "NOT_DICT")})
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
    trial = {"mode": "A (sequential swap)", "task": "RRI validate_research_need (§19-20)", "swaps": SWAPS}
    final_source = None
    try:
        print("### Instrumented A-mode trial: RRI validate_iec through DW ###\n")
        with tempfile.TemporaryDirectory() as dd:
            os.environ["DW_DATA_DIR"] = dd
            import importlib
            importlib.reload(W)
            TASK, mgr = "TASK-RRI-NEEDVAL-01", "claude-manager"
            tk = [0]
            def ts():
                tk[0] += 1
                return f"2026-07-07T12:00:{tk[0]:02d}Z"
            kp = {"packet_type": "KNOWLEDGE_PACKET", "related_failure_patterns": ["IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION"]}
            W.create_task(TASK, "RRI", "implement validate_research_need (§19-20, Need Validation before research + C-TOTALITY)", kp, ts(), mgr)
            W.record_plan(TASK, {"narrow_goal": "validate_research_need: N2 nec present / N3 validated True / N4 alternative_causes considered / N5 observed block / N6 decision_to_support / N1 C-TOTALITY"}, ts(), mgr)

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
                    pkt = W.propose_complete(TASK, [{"observed": f"validate_research_need passed {tr.get('n_pass')}/{tr.get('cases')} load-bearing tests"}],
                                             [{"proposed": "RRI validate_research_need (§19-20) implemented; passes tested need-validation + C-TOTALITY cases", "scope": "tested cases only", "record_ids": []}], [], ts(), mgr)
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
        Path("/home/takasan/egl/experiments/rri_needval_trial.json").write_text(json.dumps(trial, ensure_ascii=False, indent=2))
        print(f"\n=== instrumentation ===")
        print(f"  swaps: {trial['swap_count']} (failures {trial['swap_failures']}), latencies {trial['swap_latencies_s']}s, avg {trial['avg_swap_s']}s")
        print(f"  completed: {trial.get('completed')}  final_state: {trial.get('final_state')}")
        print(f"  → swaps/item = {trial['swap_count']} (this item). A vs B は複数 item で判断。")


if __name__ == "__main__":
    main()
