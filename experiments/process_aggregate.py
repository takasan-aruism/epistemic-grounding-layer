#!/usr/bin/env python3
"""§10.3 deterministic process aggregate + trigger evaluation。LLM は process-cost calculator ではない。
run_sor/events.jsonl の primitive から集計し、optimization_triggers.jsonl v1 を deterministic に評価する。
出力は Process Optimizer(§16)の input。trigger が fire した時のみ LLM を呼ぶ。"""
import json, sys, os
sys.path.insert(0, "/home/takasan/dev-workcell")
os.environ["DW_DATA_DIR"] = "/home/takasan/dev-workcell/run_sor"
from dw import workcell as W
from pathlib import Path

EGL = Path("/home/takasan/egl")
# RRI deterministic-core slices は互いに独立(どのスライスも他スライスの出力を consume しない)。
# = 実タスク構造の事実(推論でなく)。batch/parallelize eligibility の根拠。
INDEPENDENCE = "all RRI deterministic-core validators are mutually independent (no slice consumes another's output)"


def all_tasks():
    return [e["task_id"] for e in W._read_events() if e["phase"] == "CREATE"]


def per_task(tid):
    state, view = W.derive_state(tid)
    tr = W.derive_process_trace(tid)
    audits = [e for e in W._read_events(tid) if e["phase"] == "AUDIT"]
    disposes = [e for e in W._read_events(tid) if e["phase"] == "DISPOSE"]
    all_disp = [d for dp in disposes for d in (dp.get("payload") or {}).get("finding_dispositions", [])]
    fcount = sum(len((a.get("payload") or {}).get("findings", [])) for a in audits)
    return {
        "task_id": tid, "final_state": state, "completed": state == "COMPLETE",
        "run_seconds": tr["run_seconds"], "model_switches": tr["switch_count"],
        "switch_seconds": tr["total_switch_seconds"], "switch_failures": tr["switch_failures"],
        "audit_rounds": len(audits), "rework_count": view["rework_count"],
        "findings_total": fcount,
        "dispositions": {v: sum(1 for d in all_disp if d.get("verdict") == v) for v in ("ACCEPTED", "PARTIAL", "REJECTED", "REMAINS")},
    }


def load_triggers():
    p = EGL / "optimization_triggers.jsonl"
    return json.loads(p.read_text().splitlines()[-1]) if p.exists() else {}


def aggregate():
    tasks = [per_task(t) for t in all_tasks()]
    n = len(tasks)
    total_run = sum(t["run_seconds"] or 0 for t in tasks)
    total_switch = sum(t["switch_seconds"] or 0 for t in tasks)
    total_switches = sum(t["model_switches"] for t in tasks)
    reworked = [t for t in tasks if t["rework_count"] > 0]
    # overhead class: model transition。ratio = switch_time / total_run_time。
    overhead_ratio = round(total_switch / total_run, 3) if total_run else None
    agg = {
        "n_tasks": n, "completed": sum(1 for t in tasks if t["completed"]),
        "total_run_seconds": round(total_run, 1), "total_switch_seconds": round(total_switch, 1),
        "total_model_switches": total_switches, "model_switch_overhead_ratio": overhead_ratio,
        "tasks_with_rework": len(reworked), "total_rework": sum(t["rework_count"] for t in tasks),
        "total_findings": sum(t["findings_total"] for t in tasks),
        "disposition_totals": {v: sum(t["dispositions"].get(v, 0) for t in tasks) for v in ("ACCEPTED", "PARTIAL", "REJECTED", "REMAINS")},
        "independence_relation": INDEPENDENCE, "executed": "serially (A-mode: one slice fully before the next)",
        "per_task": tasks,
    }
    # deterministic trigger evaluation
    cfg = load_triggers()
    fired = []
    for tr in cfg.get("triggers", []):
        tid = tr["id"]
        if tid == "DOMINANT_OVERHEAD" and overhead_ratio is not None and overhead_ratio >= 0.30:
            fired.append({"id": tid, "value": overhead_ratio, "rule": tr["rule"]})
        elif tid == "REPEATED_HIGH_COST" and total_switches >= 3:
            fired.append({"id": tid, "value": total_switches, "rule": tr["rule"]})
        elif tid == "SERIAL_INDEPENDENT_WORK" and n >= 2:
            fired.append({"id": tid, "value": f"{n} independent slices serial", "rule": tr["rule"]})
    agg["trigger_config_version"] = cfg.get("trigger_config_version")
    agg["triggers_fired"] = fired
    return agg


if __name__ == "__main__":
    a = aggregate()
    (EGL / "experiments" / "process_aggregate.json").write_text(json.dumps(a, ensure_ascii=False, indent=2))
    print(f"### deterministic process aggregate (from run_sor primitives) ###")
    print(f"  tasks={a['n_tasks']} completed={a['completed']}  total_run={a['total_run_seconds']}s switch={a['total_switch_seconds']}s")
    print(f"  model_switch_overhead_ratio={a['model_switch_overhead_ratio']}  switches={a['total_model_switches']}  rework={a['total_rework']}")
    print(f"  dispositions={a['disposition_totals']}")
    print(f"  triggers_fired={[f['id'] for f in a['triggers_fired']]}")
    print(f"  -> Process Optimizer LLM invoked only because a trigger fired: {bool(a['triggers_fired'])}")
