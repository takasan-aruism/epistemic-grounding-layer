#!/usr/bin/env python3
"""B-mode: property-preserving batched execution(model-switch overhead を下げる, OPT-001)。
SWAP を phase 単位に amortize: 1 swap→全 generate→1 swap→全 audit+dispose→rework subset。
**P8 保存**: audit は item ごとに SEPARATE isolated call(R.audit_once を per-item に呼ぶ、共有 context 無し)。
A-mode(per-item swap)= 2N+ swaps に対し B-mode = 2 + 2×rework_rounds swaps。実測して counterfactual を置換。"""
import os, sys, time, json, subprocess, datetime as dt
from pathlib import Path
os.environ["DW_DATA_DIR"] = "/home/takasan/dev-workcell/run_sor"   # 全 workcell 呼出が persistent SoR を使う
sys.path.insert(0, "/home/takasan/egl/experiments")
sys.path.insert(0, "/home/takasan/dev-workcell")
import run_rri_dw_slice as R
from dw import workcell as W

SCRIPTS = "/home/takasan/models_trtllm"
SLICES = ["rdec", "needval", "transform", "axis", "rqgate"]   # 独立(batch-eligible)。rda は JUDGE_REQUIRED ゆえ除外
SWAPS = []
MODEL = "qwen"
BATCH_TASK = None
def iso(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)


def swap_to(target):
    global MODEL
    t0 = time.time(); frm = MODEL
    try: W.record_process_event(BATCH_TASK, "SWAP_START", {"to": target, "from": frm}, iso())
    except Exception: pass
    if target == "coder":
        sh("docker rm -f qwen36_vllm"); sh(f"bash {SCRIPTS}/serve_codernext_vllm.sh"); ep, name, cont = R.CODER_EP, R.CODER_M, "codernext_vllm"
    else:
        sh("docker rm -f codernext_vllm"); sh(f"bash {SCRIPTS}/serve_qwen36_vllm.sh"); ep, name, cont = R.QWEN_EP, R.QWEN_M, "qwen36_vllm"
    ok = False
    for _ in range(120):
        if R.serving(ep, name): ok = True; break
        if cont not in sh("docker ps --format '{{.Names}}'").stdout: break
        time.sleep(5)
    lat = round(time.time() - t0, 1); SWAPS.append({"to": target, "latency_s": lat, "ok": ok})
    try: W.record_process_event(BATCH_TASK, "SWAP_END", {"to": target, "ok": ok}, iso())
    except Exception: pass
    if ok: MODEL = target
    print(f"  [swap #{len(SWAPS)} -> {target}] {'OK' if ok else 'FAIL'} in {lat}s", flush=True)
    return ok


def gen_slice(name, cfg, feedback=None, seed=3):
    if feedback is None:
        raw = R.chat(R.CODER_EP, R.CODER_M, "You are a careful Python coding worker. Implement EXACTLY the spec.", cfg["spec"], seed=seed)
    else:
        raw = R.chat(R.CODER_EP, R.CODER_M, "Fix ONLY these accepted issues; resubmit FULL corrected source.",
                     cfg["spec"] + "\nACCEPTED_TO_FIX:\n" + feedback, seed=seed)
    src = R.extract(raw, cfg["fn"]); tr = R.run_tests(src, cfg)
    return src, tr


def main():
    global BATCH_TASK
    os.makedirs("/home/takasan/dev-workcell/run_sor", exist_ok=True)
    BATCH_TASK = f"BATCH-RRI-{int(time.time())}"
    W.create_task(BATCH_TASK, "RRI", "batched B-mode process container", {"related_failure_patterns": []}, iso(), "claude-manager")
    W.record_process_event(BATCH_TASK, "RUN_START", {"mode": "B (batched)", "slices": SLICES}, iso())
    print(f"### B-mode batched run: {SLICES} ###\n")
    tasks, cfgs, src, tr = {}, {}, {}, {}
    for s in SLICES:
        cfgs[s] = R.SLICES[s]
        tasks[s] = f"{cfgs[s]['task']}-BATCH-{int(time.time())}-{s}"
        W.create_task(tasks[s], "RRI", cfgs[s]["goal"], {"related_failure_patterns": ["IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION"]}, iso(), "claude-manager")
        W.record_plan(tasks[s], {"narrow_goal": cfgs[s]["goal"]}, iso(), "claude-manager")

    # ── PHASE GENERATE: 1 swap, all N generated (no swaps between) ──
    assert swap_to("coder"), "coder swap failed"
    for s in SLICES:
        src[s], tr[s] = gen_slice(s, cfgs[s])
        W.record_generate(tasks[s], {"identity": "qwen3-coder-next@8006", "run_id": "gen1", "diff": src[s], "test_result": tr[s], "problems": tr[s].get("failures", [])}, iso())
        print(f"  [GEN {s}] {tr[s].get('status')} passed={tr[s].get('passed')} {tr[s].get('n_pass')}/{tr[s].get('cases')}", flush=True)

    # ── PHASE AUDIT + DISPOSE: 1 swap, each item audited in a SEPARATE isolated call (P8) ──
    assert swap_to("qwen"), "qwen swap failed"
    for s in SLICES:
        findings = R.audit_once(src[s], tr[s], cfgs[s], "aud1", seed=41)   # P8: isolated per-item call
        W.record_audit(tasks[s], {"identity": "qwen3.6@8005-auditor", "run_id": "aud1", "findings": findings}, iso())
        st, view = W.derive_state(tasks[s])
        if st == "DISPOSITION_REQUIRED":
            disp = R.dispose_findings(src[s], cfgs[s], W._latest_findings(view))
            W.record_disposition(tasks[s], disp, iso(), "claude-manager")
            acc = sum(1 for d in disp if d["verdict"] == "ACCEPTED")
            print(f"  [AUD {s}] findings={len(findings)} dispose {acc} ACCEPTED", flush=True)
        else:
            print(f"  [AUD {s}] findings={len(findings)} state={st}", flush=True)

    # ── PHASE REWORK: subset only, 2 swaps per round (amortized over the subset) ──
    rounds = 0
    while rounds < W.REWORK_ESCALATION_THRESHOLD:
        rework = [s for s in SLICES if W.derive_state(tasks[s])[0] == "READY_FOR_REGENERATE"]
        if not rework:
            break
        print(f"  [REWORK round {rounds+1}] subset={rework}", flush=True)
        assert swap_to("coder"), "coder swap failed (rework)"
        for s in rework:
            items = W.rework_items(tasks[s])
            fb = json.dumps({"test_failures": tr[s].get("failures"), "accepted_to_fix": [i.get("finding") for i in items]}, ensure_ascii=False, default=str)[:1100]
            src[s], tr[s] = gen_slice(s, cfgs[s], feedback=fb, seed=4 + rounds)
            W.record_regenerate(tasks[s], {"identity": "qwen3-coder-next@8006", "run_id": f"regen{rounds+1}", "diff": src[s], "test_result": tr[s], "resolved_findings": [i["finding_id"] for i in items]}, iso())
        assert swap_to("qwen"), "qwen swap failed (re-audit)"
        for s in rework:
            findings = R.audit_once(src[s], tr[s], cfgs[s], f"aud{rounds+2}", seed=41 + rounds + 1)
            W.record_audit(tasks[s], {"identity": "qwen3.6@8005-auditor", "run_id": f"aud{rounds+2}", "findings": findings}, iso())
            st, view = W.derive_state(tasks[s])
            if st == "DISPOSITION_REQUIRED":
                disp = R.dispose_findings(src[s], cfgs[s], W._latest_findings(view))
                W.record_disposition(tasks[s], disp, iso(), "claude-manager")
        rounds += 1

    # ── COMPLETE each (upper review + gate) ──
    results = {}
    for s in SLICES:
        st, view = W.derive_state(tasks[s])
        if st == "READY_FOR_UPPER_REVIEW":
            W.record_upper_review(tasks[s], {"verdict": "tests pass + audit clean"}, iso(), "claude-manager")
            try:
                W.propose_complete(tasks[s], [{"observed": f"{cfgs[s]['fn']} passed"}], [{"proposed": f"RRI {cfgs[s]['fn']} (B-mode)", "scope": "tested cases only", "record_ids": []}], [], iso(), "claude-manager")
                results[s] = "COMPLETE"
            except W.WorkflowViolation as e:
                results[s] = f"REJECTED:{e}"
        else:
            results[s] = st
    W.record_process_event(BATCH_TASK, "RUN_END", {}, iso())

    # ── measure ──
    n = len(SLICES); a_mode_swaps = 2 * n            # A-mode: per-item generate+audit swap(rework 別)
    b_mode_swaps = len(SWAPS)
    okswaps = [x["latency_s"] for x in SWAPS if x["ok"]]
    avg = round(sum(okswaps) / len(okswaps), 1) if okswaps else None
    out = {"mode": "B (batched)", "slices": SLICES, "results": results,
           "b_mode_swaps": b_mode_swaps, "a_mode_swaps_baseline": a_mode_swaps,
           "swap_latencies_s": [x["latency_s"] for x in SWAPS], "avg_swap_s": avg,
           "measured_switch_time_saved_s": round((a_mode_swaps - b_mode_swaps) * avg, 1) if avg else None,
           "rework_rounds": rounds, "completed": sum(1 for v in results.values() if v == "COMPLETE"),
           "batch_task": BATCH_TASK, "swap_reduction": f"{a_mode_swaps} (A per-item) -> {b_mode_swaps} (B batched)",
           "authoritative_trace": f"dw.workcell.derive_process_trace({BATCH_TASK!r})"}
    Path("/home/takasan/egl/experiments/rri_batch_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n=== MEASURED B-mode ===")
    print(f"  swaps: A per-item baseline {a_mode_swaps} -> B batched {b_mode_swaps}  (avg {avg}s/swap)")
    print(f"  measured switch-time saved: {out['measured_switch_time_saved_s']}s (rework rounds={rounds})")
    print(f"  results: {results}")
    # restore qwen if needed
    if not R.serving(R.QWEN_EP, R.QWEN_M):
        swap_to("qwen")
    print("\n-> rri_batch_run.json 保存")


if __name__ == "__main__":
    main()
