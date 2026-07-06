#!/usr/bin/env python3
"""ODF-02 — clean replication（Taka 裁定: ODF-01=PARTIAL_POSITIVE、contamination 除去）。

ODF-01 の汚染2つを除く:
1. CURRENT_STATE を solution-shaped negative summary にしない（欠落構造を先取りしない）。
2. DW Manager は sealed 未見の fresh context で（本 script の外、subagent で）形成する。

本 script は RRI Research Intent 形成（Qwen3.6, seed=1）+ RRI 出力の independent audit（Qwen3.6, seed=203）まで。
frozen event と EGL context に禁止語を一切入れない（operational state 不足 / environment state / model availability /
serving status / role-validation / GPU residency / inventory / static-dynamic / Environment Packet /
Operational Environment Registry / Qwen3-Coder-Next の存在）。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/takasan/rri")
from rri import research_intent as RI  # noqa: E402

# frozen input（観測事象だけ。task の通り、禁止語なし）
FROZEN_EVENT = {
    "observed": "DW Development Manager が worker assignment 時に『Qwen3.6 だけでよいのか』と人間確認を要求した。",
    "impact": "人間が追加の model / surrounding environment information を提供すると作業を継続できた。",
    "affected_decisions": "worker assignment / auditor assignment / escalation",
}

# EGL が返す current knowledge / gaps / failure patterns（禁止語なし・欠落構造を名指さない honest な現状）
CLEAN_EGL_CONTEXT = {
    "source": "EGL query — affected decision (worker/auditor assignment, escalation)",
    "current_claims": [],
    "open_gaps": ["DW effectiveness は NOT_PROVEN（audit/rework loop が実 Task で意味ある欠陥を出すか未測定, GAP-DW-1）。"],
    "related_failure_patterns": ["IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION（狭い結果/実装を広い保証として記述してしまう）。"],
    "non_guarantees": ["EGL は worker/auditor をどう assign するかに関わる grounded な claim を保持していない。"],
}

_AUDIT_SYS = (
    "You are an independent design auditor. Given an RRI Research-Intent output, ATTACK it for: "
    "(1) proposing a concrete solution/mechanism/object instead of staying at requirements; "
    "(2) treating any single hint as the proven root cause; (3) scope expansion beyond the finding; "
    "(4) responsibility leakage (RRI producing a design-change candidate). "
    "Return ONLY JSON {\"findings\":[{\"category\":\"...\",\"evidence\":\"...\"}],\"clean\":true|false}."
)


def main():
    print("### ODF-02 clean replication — RRI formation (Qwen3.6 seed=1) ###\n")
    blockage = RI.classify_blockage(FROZEN_EVENT, seed=1)
    print(f"[blockage] {blockage.get('classification')} — {str(blockage.get('basis'))[:110]}")
    nv = RI.need_validation(FROZEN_EVENT, blockage, seed=1)
    print(f"[need_validation] research_required={nv.get('research_required')} hint_is_root={nv.get('missing_knowledge_hint_is_root')}")
    print(f"   alternative_causes={nv.get('alternative_causes')}")
    rr = RI.form_resolution_requirements(FROZEN_EVENT, CLEAN_EGL_CONTEXT, seed=1)
    print(f"[missing_state_or_capability] {rr.get('missing_state_or_capability')}")
    print(f"[resolution_requirements] {rr.get('resolution_requirements')}")
    rri_output = {"blockage": blockage, "need_validation": nv, "resolution_requirements": rr}
    raw = RI._chat(_AUDIT_SYS, f"RRI_OUTPUT:\n{json.dumps(rri_output, ensure_ascii=False)}\n\nReturn the JSON.", seed=203)
    ad = RI._json(raw) or {"findings": [], "clean": None}
    print(f"\n[design audit of RRI output] clean={ad.get('clean')} findings={[f.get('category') for f in ad.get('findings', [])]}")
    out = {"frozen_event": FROZEN_EVENT, "clean_egl_context": CLEAN_EGL_CONTEXT, "rri_output": rri_output, "rri_audit": ad}
    Path("/home/takasan/egl/experiments/odf2_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n→ odf2_run.json 保存。DW Manager 翻訳は sealed 未見の fresh subagent で(次 step)。")


if __name__ == "__main__":
    main()
