"""DW → EGL 還流: DW の RESULT_PACKET を EGL の通常 admission 規律で ingest(認知スタック step 6)。

DW は確定しない(proposed_claims のみ)。EGL が currentness / validation_target / scope / admission を付ける。
**核心規律**(EGL DE-0005 / DE-0059): DW の self-reported test_result を behavioral truth として無条件に信じない。
VALIDATION_TARGET 軸で分ける:
- RECORD_OCCURRENCE:「DW RESULT_PACKET が X を記録した」= 記録存在(PRIMARY evidence=file)→ ADMITTED 可。
- BEHAVIORAL_PROPERTY:「実装が実際に X の通り振る舞う」= EGL が *独立に再実行* して初めて VERIFIED。
  再検証なし/失敗なら REPORTED(DW-reported、record 単独では behavioral を確立しない)。
- over-claim(tested scope を超える一般正当性)= REJECTED(RRI overall は依然 first-slice)。
"""
import re
from egl import validation_target as VT


def ingest_result_packet(packet, reverify=None):
    """packet=DW RESULT_PACKET(dict)。reverify: () -> (ok:bool, detail:str)(EGL 独立再検証)。
    返り: {task, admitted, rejected, gaps, non_guarantees}。EGL は自動昇格しない・over-claim を弾く。"""
    task = packet.get("task_id")
    admitted, rejected, gaps = [], [], []

    # (1) RECORD_OCCURRENCE — RESULT_PACKET が完了・test 結果・監査を *記録した*(記録存在)
    tr = packet.get("test_results") or []
    dw_pass = sum((t or {}).get("n_pass", 0) for t in tr if isinstance(t, dict))
    ro_ok = VT.target_problem("RECORD_OCCURRENCE", {"RECORD"}) is None
    admitted.append({
        "validation_target": "RECORD_OCCURRENCE",
        "claim": f"DW RESULT_PACKET {task} records completion_status={packet.get('completion_status')}, "
                 f"{dw_pass} DW-run passing test cases, {len(packet.get('attacker_findings') or [])} independent-audit findings",
        "evidence_kinds": ["RECORD"],
        "admission_status": "ADMITTED" if ro_ok else "REJECTED",
        "source_class": "SECONDARY",   # DW report は EGL にとって外部 system の二次報告
        "scope": "record-existence only(内容の外部真偽ではない)",
    })

    # (2) BEHAVIORAL_PROPERTY — proposed_claims。EGL 独立再検証がなければ VERIFIED にしない
    rv = reverify() if reverify else None      # (ok, detail)
    for pc in packet.get("proposed_claims", []):
        text = pc.get("proposed", "")
        scope = pc.get("scope", "") or ""
        if not re.search(r"tested", scope + " " + text, re.I):
            rejected.append({"claim": text, "reason": "scope が tested-cases を超える一般正当性 → EGL は admit しない(RRI overall は first-slice)"})
            continue
        if rv and rv[0]:
            ek = {"RUN_ARTIFACT"}
            status = "VERIFIED" if VT.target_problem("BEHAVIORAL_PROPERTY", ek) is None else "REPORTED"
            admitted.append({"validation_target": "BEHAVIORAL_PROPERTY", "claim": text, "scope": scope,
                             "evidence_kinds": ["EGL_INDEPENDENT_REVERIFY(RUN_ARTIFACT)"],
                             "admission_status": status, "source_class": "PRIMARY", "egl_reverify": rv[1]})
        else:
            admitted.append({"validation_target": "BEHAVIORAL_PROPERTY", "claim": text, "scope": scope,
                             "evidence_kinds": ["RECORD(DW-reported)"], "admission_status": "REPORTED",
                             "source_class": "SECONDARY",
                             "note": "DW-reported、EGL 独立再検証なし/失敗 → BEHAVIORAL は record 単独で確立しない",
                             "egl_reverify": (rv[1] if rv else "not attempted")})

    for g in packet.get("new_gap_candidates", []):
        gaps.append(g.get("gap") if isinstance(g, dict) else g)

    non_guarantees = [
        "single-Qwen auditor blind spot(DW §7 既知弱点)",
        "admission は EGL 再検証した tested-cases scope のみ(§9 一般正当性でない)",
        "RRI overall は依然 first-slice / NOT_IMPLEMENTED",
    ]
    return {"task": task, "admitted": admitted, "rejected": rejected, "gaps": gaps,
            "non_guarantees": non_guarantees}


def admit_forward_claims(claims, source_trace=None, reverify=None):
    """ITEM-2DER-EVO-0001 (DE-0190): FORWARD-path admission. Qualify the EGL grounding claims that seed a
    DW KNOWLEDGE_PACKET with a validation-target verdict BEFORE the DW task is created — so DW is seeded with
    admitted knowledge, not raw answer_question output. Deterministic (no :8005), same discipline as the
    return-path ingest: source-backed statement -> RECORD_OCCURRENCE ADMITTED; behavioural assertion without
    EGL reverify -> REPORTED; over-claim -> REJECTED.
    """
    import json
    from egl import de_admission as DEA
    has_source = bool(source_trace)
    qualified, admitted, reported, rejections = [], [], [], []
    for c in (claims or []):
        text = (c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)).lower()
        hard = [t for t in DEA.HARD_REJECT if t in text]
        if hard:
            rejections.append({"claim": c, "reason": "over-claim (ceiling): " + ", ".join(hard)})
            qualified.append({"claim": c, "admission_status": "REJECTED", "validation_target": None})
            continue
        beh = [t for t in DEA.BEHAVIORAL_MARKERS if t in text]
        if beh:
            rv = reverify() if reverify else None
            status = "VERIFIED" if (rv and rv[0]) else "REPORTED"
            (admitted if status == "VERIFIED" else reported).append(c)
            qualified.append({"claim": c, "admission_status": status, "validation_target": "BEHAVIORAL_PROPERTY"})
            continue
        if has_source and VT.target_problem("RECORD_OCCURRENCE", {"RECORD"}) is None:
            admitted.append(c)
            qualified.append({"claim": c, "admission_status": "ADMITTED", "validation_target": "RECORD_OCCURRENCE"})
        else:
            reported.append(c)
            qualified.append({"claim": c, "admission_status": "REPORTED", "validation_target": "RECORD_OCCURRENCE",
                              "note": "no source_trace -> record occurrence not established"})
    return {"qualified_claims": qualified, "admitted": admitted, "reported": reported,
            "rejected": [r["claim"] for r in rejections], "rejections": rejections,
            "summary": {"admitted": len(admitted), "reported": len(reported), "rejected": len(rejections)},
            "non_guarantee": "forward admission = validation-target qualification of grounding claims; "
                             "not independent reverification (BEHAVIORAL stays REPORTED)"}
