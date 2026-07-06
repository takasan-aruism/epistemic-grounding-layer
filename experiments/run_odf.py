#!/usr/bin/env python3
"""ODF experiment — frozen operational event を RRI Research Intent 形成(Qwen3.6)に通す(TASK-ODF-08）。

Amendment B の責任境界: RRI(Qwen3.6)は blockage 分類 → Need Validation → RESOLUTION_REQUIREMENTS まで。
design candidate は作らない(それは DW Manager=Claude が別途、grounded requirements から翻訳)。
AUDIT は Qwen3.6 別 seed(別 run/context, §D)。sealed human candidate は開けない。current_system_state に
解決案を入れない(honest current-state のみ)。
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "/home/takasan/rri")
from rri import research_intent as RI  # noqa: E402

# 凍結入力(task の通り、hint を足さない=pre-seed しない)
FROZEN_EVENT = {
    "origin": "DW",
    "observed_event": "DW Development Manager が利用可能な model / worker 選択を確信できず、Qwen3.6 だけで十分かを確認する必要が生じた。",
    "decision_affected": "worker assignment / auditor assignment / escalation",
    "known_impact": "human が周辺の environment / model 情報を手動で補った。",
}

# EGL の grounded current-system-state(解決案を含めない honest な現状のみ)
CURRENT_STATE = {
    "source": "EGL/DW ledgers",
    "facts": [
        "DW DE-0004: 直近の live coder/auditor は汎用 Qwen3.6-35B-A3B(localhost:8005 で serve される唯一の model)。coding 専用 model は不使用。",
        "EGL/DW に、利用可能な運用 model / worker が何か・その serving / role-validation 状態・GPU residency を表す object は存在しない。",
        "DW の worker/auditor assignment は現在、人間が周辺情報を手で与えることに依存している。",
    ],
    "open_gaps": ["DW effectiveness NOT_PROVEN", "model exists ≠ role validated(role validation は実 Task 結果からのみ)"],
    "non_guarantees": ["single-Qwen auditor blind spot"],
}

_AUDIT_SYS = (
    "You are an independent design auditor. Given an RRI Research-Intent output, ATTACK it for: "
    "(1) did it propose a concrete solution/mechanism/registry instead of staying at requirements? "
    "(2) did it treat any single missing_knowledge_hint as the proven root cause? "
    "(3) scope expansion beyond the operational finding? "
    "(4) responsibility leakage (RRI producing a design-change candidate). "
    "Return ONLY JSON {\"findings\":[{\"category\":\"...\",\"evidence\":\"...\"}],\"clean\":true|false}."
)


def audit(rri_output, seed=202):
    raw = RI._chat(_AUDIT_SYS, f"RRI_OUTPUT:\n{json.dumps(rri_output, ensure_ascii=False)}\n\nReturn the JSON.", seed=seed)
    o = RI._json(raw) or {"findings": [], "clean": None, "_raw": raw[:120]}
    return o


def main():
    print("### ODF experiment — RRI Research Intent formation (Qwen3.6, seed=0) ###\n")
    blockage = RI.classify_blockage(FROZEN_EVENT)
    print(f"[blockage] {blockage.get('classification')} — {str(blockage.get('basis'))[:100]}")
    nv = RI.need_validation(FROZEN_EVENT, blockage)
    print(f"[need_validation] research_required={nv.get('research_required')} hint_is_root={nv.get('missing_knowledge_hint_is_root')}")
    print(f"   alternative_causes={nv.get('alternative_causes')}")
    rr = RI.form_resolution_requirements(FROZEN_EVENT, CURRENT_STATE)
    print(f"[missing_state_or_capability] {rr.get('missing_state_or_capability')}")
    print(f"[resolution_requirements] {rr.get('resolution_requirements')}")
    rri_output = {"blockage": blockage, "need_validation": nv, "resolution_requirements": rr}
    ad = audit(rri_output)
    print(f"\n[design audit] clean={ad.get('clean')} findings={[f.get('category') for f in ad.get('findings', [])]}")
    for f in ad.get("findings", []):
        print(f"   - {f.get('category')}: {str(f.get('evidence'))[:120]}")
    out = {"frozen_event": FROZEN_EVENT, "current_state": CURRENT_STATE, "rri_output": rri_output, "design_audit": ad}
    Path("/home/takasan/egl/experiments/odf_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n→ odf_run.json 保存。DW Manager 翻訳 + 測定 + seal 比較は Claude が別途(system role action として記録)。")


if __name__ == "__main__":
    main()
