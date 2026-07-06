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
