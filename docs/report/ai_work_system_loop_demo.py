#!/usr/bin/env python3
"""AI Work System — Full loop demonstration(bootstrap step 9)。

DS → RRI → EGL → DW → EGL → DS を一本の経路として通し、4層が1つの request を連携処理し loop が
閉じる姿を示す。層間は **versioned packet(dict 契約)** でのみ繋ぐ(module 内部へは触れない)。
本 harness は demonstration(production の integration 層は MOR で deferred=5個目の repo を今は作らない)。

⚠ SCOPE(独立 audit 2026-07-07, DE-0065 で狭めた): 本 harness が実演するのは
**DS→RRI→EGL→DW→EGL→DS の packet-level round-trip WIRING のみ**——一部 real subsystem seam と、
以下の明示的 stub/bridge/fake を混在させた一つの harness。**各接合の real property は別 record であり、
この demo はそれらを継承しない。**

demo の stub/bridge/fake(いずれも demo 固有・real でない):
- RRI Approved RQ Set = BRIDGE_STUB(RRI Research Intent §19-29 未実装)。
- EGL KNOWLEDGE_PACKET emitter = thin BRIDGE(台帳から薄く抽出)。
- DW worker/auditor = FakeWorker / FakeAuditor(live Qwen でない)。
- **EGL reverify = FIXED-SUCCESS FAKE callback**(real な独立再検証ではない。real property は step6/DE-0063 の別 record)。
- DS return edge = PROVISIONAL DIALOGUE_EVENT write。
real seam(構造として通っている): packet 契約の授受、DW workcell の state machine/gate 遷移、
RRI Context Binding+strategy(step5,8)、EGL の admission *分類ロジック*(RECORD_OCCURRENCE/BEHAVIORAL の振り分け)。
※ admission の「VERIFIED」は demo では FIXED-SUCCESS fake reverify に由来する=**demo 自身の property として使わない**。
"""
import json
import os
import sys
import tempfile

for p in ["/home/takasan/ds", "/home/takasan/rri", "/home/takasan/egl", "/home/takasan/dev-workcell"]:
    sys.path.insert(0, p)

from ds import phase0, phase1                       # noqa: E402
from rri import context_binding, request_resolution # noqa: E402
from egl import result_packet as egl_rp                        # noqa: E402
from dw import workcell, workflow, adapters          # noqa: E402

TRACE = []
def step(layer, arrow, detail):
    TRACE.append((layer, arrow, detail))
    print(f"  {layer:5} {arrow:22} {detail}")


def egl_knowledge_packet_bridge(rq_text):
    """BRIDGE: EGL 台帳から RQ に関連する KNOWLEDGE_PACKET を薄く生成(real emitter は未実装 gap)。"""
    claims, gaps, fps = [], [], []
    de = "/home/takasan/egl/DESIGN_EVIDENCE_LEDGER.jsonl"
    if os.path.exists(de):
        for line in open(de):
            if not line.strip():
                continue
            o = json.loads(line)
            if any(k in json.dumps(o, ensure_ascii=False) for k in ("Context Binding", "RRI", "select_strategy")):
                claims.append({"text": (o.get("observation", "")[:80]), "currentness": "CURRENT",
                               "record_ids": [o.get("design_evidence_id")]})
        claims = claims[-3:]
    ab = "/home/takasan/egl/audit_backlog.jsonl"
    if os.path.exists(ab):
        for line in open(ab):
            if line.strip() and "RRI" in line:
                gaps.append(json.loads(line).get("backlog_id"))
    return {"packet_type": "KNOWLEDGE_PACKET", "schema_version": "0.1", "task_context": rq_text,
            "current_claims": claims, "historical_claims": [], "open_gaps": gaps[:4],
            "related_failure_patterns": ["IMPLEMENTATION_TO_CLAIM_SCOPE_EXPANSION"],
            "non_guarantees": ["EGL KNOWLEDGE_PACKET emitter は BRIDGE(real emitter 未実装)"], "source_trace": []}


def run_loop(request, snapshot, recent_utterances, conversation_length):
    print(f"### FULL LOOP — request: {request!r} ###\n")

    # ── 1) DS: 対話状態 → DIALOGUE_STATE_PACKET ───────────────────────────────
    ds_packet = phase1.dialogue_state_packet(snapshot, recent_utterances)
    step("DS", "→ DIALOGUE_STATE_PACKET", f"{len(ds_packet['threads'])} threads(states付き)")

    # ── 2) RRI: Context Binding(DS消費)→ strategy → APPROVED_RQ_SET(bridge)──
    binding = context_binding.bind_context(request, ds_packet, recent_utterances, conversation_length)
    assessment = {"context_anchoring": binding["anchoring"], "answer_determinacy": "OPEN",
                  "intent_breadth": "MULTI_AXIS", "premise_stability": "STABLE"}  # 他3軸は別 slice
    strategy = request_resolution.select_strategy(assessment)
    step("RRI", "Context Binding", f"mode={binding['context_mode']} anchoring={binding['anchoring']} refs={binding['supporting_context_refs']}")
    step("RRI", "→ strategy", strategy)
    approved_rq = {"packet_type": "APPROVED_RQ_SET", "approval_status": "BRIDGE_STUB",
                   "required_rqs": [f"{request} を進めるのに必要な知識は何か"], "resolved_via": strategy}
    step("RRI", "→ APPROVED_RQ_SET", f"[BRIDGE_STUB] {approved_rq['required_rqs'][0][:40]}")

    # ── 3) EGL: grounding → KNOWLEDGE_PACKET(bridge)──────────────────────────
    kp = egl_knowledge_packet_bridge(approved_rq["required_rqs"][0])
    step("EGL", "→ KNOWLEDGE_PACKET", f"[BRIDGE] {len(kp['current_claims'])} claims, gaps={kp['open_gaps']}")

    # ── 4) DW: Task 実行・独立監査・gate(real workcell, Fake adapters で決定的)──
    with tempfile.TemporaryDirectory() as d:
        os.environ["DW_DATA_DIR"] = d
        import importlib
        importlib.reload(workcell); importlib.reload(adapters); importlib.reload(workflow)
        worker = adapters.FakeWorker(identity="loop#coder", test_result={"passed": True, "cases": 2})
        auditor = adapters.FakeAuditor(identity="loop#auditor", findings=[])
        state, pkt, tr = workflow.run_standard_workflow(
            "TASK-LOOP-1", "RRI", approved_rq["required_rqs"][0], kp,
            {"narrow_goal": "loop demo task", "acceptance_criteria": ["tests pass"]},
            worker, auditor, upper_review={"verdict": "loop demo"},
            observed_results=[{"observed": "loop demo tests passed"}],
            proposed_claims=[{"proposed": "loop demo task satisfied its tested cases", "scope": "tested cases only", "record_ids": []}],
            new_gap_candidates=[])
        step("DW", "workcell", f"state={state} (independent audit gate 通過)")
        step("DW", "→ RESULT_PACKET", f"completion={pkt['completion_status'] if pkt else None} (proposed_claims のみ)")
        result_packet = pkt

    # ── 5) EGL: RESULT_PACKET 還流(real admission, DW を無条件に信じない)──────
    # ⚠ reverify は FIXED-SUCCESS FAKE(real な独立再検証でない)。real property は step6/DE-0063。
    admission = egl_rp.ingest_result_packet(result_packet, reverify=lambda: (True, "FIXED-SUCCESS FAKE reverify — NOT a real re-run"))
    adm = [f"{a['admission_status']}:{a['validation_target']}" for a in admission["admitted"]]
    step("EGL", "← RESULT_PACKET admit", f"{adm}  [reverify=FIXED-SUCCESS FAKE]  rejected={len(admission['rejected'])}")

    # ── 6) DS: 対話状態を更新して loop を閉じる ────────────────────────────────
    with tempfile.TemporaryDirectory() as d:
        os.environ["DS_DATA_DIR"] = d
        importlib.reload(phase0)
        u = phase0.record_utterance("USER", request, "loop-conv", "2026-07-06T14:00:00Z")
        ev = phase0.record_dialogue_event([u["utterance_id"]], transition_candidate="CONTINUE",
                                          focus_candidate="context binding 実装", actor="loop-orchestrator",
                                          run_meta={"strategy": strategy, "admitted": adm})
        step("DS", "← state update", f"DIALOGUE_EVENT {ev['dialogue_event_id']} (PROVISIONAL, transition={ev['transition_candidate']}) → loop 閉")

    print("\n=== packet-level round-trip WIRING closed: DS → RRI → EGL → DW → EGL → DS ===")
    print("  property = wiring のみ。各接合の real property(独立再検証=DE-0063 等)は継承しない。")
    print("  demo fakes/stubs: RRI ApprovedRQ=stub / EGL KP emitter=bridge / DW=Fake / EGL reverify=FIXED-SUCCESS fake / DS edge=provisional")
    return {"trace": [list(t) for t in TRACE], "strategy": strategy, "admission": admission}


if __name__ == "__main__":
    # DS 状態(step7 の scenario を再利用): T3=Context Binding thread が OPEN
    SNAP = {"threads": [
        {"thread_id": "T2", "topic": "プーチンの今後", "state": "PARTIALLY_CLOSED", "open_branches": ["経済"]},
        {"thread_id": "T3", "topic": "RRI Context Binding の 2モード", "state": "OPEN", "open_branches": ["既定 mode"]},
    ]}
    RECENT = [{"utterance_id": "UTT-5", "raw_text": "Context Binding の 2モードで迷ってる"}]
    res = run_loop("さっきの Context Binding、実装して", SNAP, RECENT, conversation_length=30)
    json.dump(res, open("/tmp/claude-1000/-home-takasan/4b8a476e-f5f7-4a1a-9aa8-8fb3d381d669/scratchpad/loop_run.json", "w"), ensure_ascii=False, indent=2)
