#!/usr/bin/env python3
"""§2.5 F-1 counter-factual: run_sor/events.jsonl の primitive のみから Task Unit を再構成する。
trial summary JSON / convenience roll-up を一切読まない。argv[1]=task_id(省略時 SoR の最新 task)。

再構成: task history / phase timeline / model identity+switch / test result / findings /
finding dispositions / revision lineage / upper review / RESULT_PACKET basis。
"""
import json, sys
sys.path.insert(0, "/home/takasan/dev-workcell")
import os
os.environ["DW_DATA_DIR"] = "/home/takasan/dev-workcell/run_sor"
from dw import workcell as W


def latest_task():
    ev = W._read_events()
    ids = [e["task_id"] for e in ev if e["phase"] == "CREATE"]
    return ids[-1] if ids else None


def reconstruct(task_id):
    ev = W._read_events(task_id)
    if not ev:
        return None
    state, view = W.derive_state(task_id)
    trace = W.derive_process_trace(task_id)
    byphase = lambda ph: [e for e in ev if e["phase"] == ph]
    gens = byphase("GENERATE") + byphase("REGENERATE")
    audits = byphase("AUDIT")
    disposes = byphase("DISPOSE")
    r = {
        "task_id": task_id,
        "task_contract": (byphase("CREATE")[0].get("payload") or {}) if byphase("CREATE") else {},
        "plan": (byphase("PLAN")[0].get("payload") or {}).get("implementation_packet") if byphase("PLAN") else None,
        "phase_timeline": [(t["phase"], t["ts"], t.get("identity")) for t in trace["phase_timeline"]],
        "model_identities": sorted({e.get("identity") for e in gens + audits if e.get("identity")}),
        "model_switches": trace["switch_count"], "avg_switch_seconds": trace["avg_switch_seconds"],
        "run_seconds": trace["run_seconds"],
        "generator_runs": [(g.get("run_id"), g.get("identity"),
                            (g.get("payload") or {}).get("test_result", {}).get("passed")) for g in gens],
        "test_results": [(g.get("run_id"), (g.get("payload") or {}).get("test_result")) for g in gens],
        "findings": [(a.get("run_id"), [(f.get("finding_id"), f.get("category"), f.get("raw_category"))
                                        for f in (a.get("payload") or {}).get("findings", [])]) for a in audits],
        "dispositions": [[(d.get("finding_id"), d.get("verdict")) for d in (dp.get("payload") or {}).get("finding_dispositions", [])] for dp in disposes],
        "revision_lineage": [g.get("run_id") for g in byphase("REGENERATE")],
        "upper_review": (byphase("UPPER_REVIEW")[-1].get("payload") if byphase("UPPER_REVIEW") else None),
        "final_state": state, "rework_count": view["rework_count"],
        "result_packet_written": bool(byphase("COMPLETE")),
    }
    return r


def check_completeness(r):
    """再構成が summary 無しで成立しているかの検証(最低限の primitive が揃うか)。"""
    need = ["task_contract", "phase_timeline", "model_identities", "test_results", "findings", "final_state"]
    missing = [k for k in need if not r.get(k)]
    return (not missing), missing


if __name__ == "__main__":
    tid = sys.argv[1] if len(sys.argv) > 1 else latest_task()
    if not tid:
        print("no task in run_sor"); sys.exit(1)
    r = reconstruct(tid)
    ok, missing = check_completeness(r)
    print(f"### F-1 reconstruction from primitives ONLY (no summary JSON): {tid} ###\n")
    print(f"  final_state        : {r['final_state']}  (rework={r['rework_count']})")
    print(f"  model identities   : {r['model_identities']}")
    print(f"  model switches     : {r['model_switches']} (avg {r['avg_switch_seconds']}s), run {r['run_seconds']}s")
    print(f"  phase timeline     : {[p for p,_,_ in r['phase_timeline']]}")
    print(f"  generator runs     : {r['generator_runs']}")
    print(f"  findings/audit     : {r['findings']}")
    print(f"  dispositions       : {r['dispositions']}")
    print(f"  revision lineage   : {r['revision_lineage']}")
    print(f"  upper review       : {'present' if r['upper_review'] is not None else 'none'}")
    print(f"  RESULT_PACKET      : {'written (COMPLETE event)' if r['result_packet_written'] else 'not completed'}")
    print(f"\n  reconstruction complete WITHOUT summary artifact: {ok}" + (f" (missing {missing})" if missing else ""))
    print(json.dumps(r, ensure_ascii=False, indent=2))
