#!/usr/bin/env python3
"""DW→EGL RESULT_PACKET ingestion のテスト(hermetic)。EGL が DW を無条件に信じない規律を検証:
RECORD_OCCURRENCE は admit、BEHAVIORAL は独立再検証がなければ REPORTED(VERIFIED でない)、
over-claim は REJECT、gap は open gap 化。"""
import sys
from egl import result_packet as RP

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS ✅' if ok else 'FAIL ❌'}] {name}" + (f"  — {detail}" if detail else ""))


BASE_PACKET = {
    "packet_type": "RESULT_PACKET", "task_id": "TASK-X", "completion_status": "COMPLETE",
    "test_results": [{"status": "executed", "passed": True, "cases": 11, "n_pass": 11}],
    "attacker_findings": [], "new_gap_candidates": [{"gap": "axis assessment not in slice"}],
    "proposed_claims": [{"proposed": "select_strategy satisfies §9 on the tested cases",
                         "scope": "tested cases only — NOT a general correctness proof"}],
}


def t_record_occurrence_admitted():
    r = RP.ingest_result_packet(BASE_PACKET, reverify=None)
    ro = [a for a in r["admitted"] if a["validation_target"] == "RECORD_OCCURRENCE"]
    check("RECORD_OCCURRENCE(DW が記録した)は ADMITTED", ro and ro[0]["admission_status"] == "ADMITTED")


def t_behavioral_needs_egl_reverify():
    # 再検証なし → REPORTED(VERIFIED でない): EGL は DW の test_result を信じない
    r0 = RP.ingest_result_packet(BASE_PACKET, reverify=None)
    bp0 = [a for a in r0["admitted"] if a["validation_target"] == "BEHAVIORAL_PROPERTY"]
    check("BEHAVIORAL: 独立再検証なし → REPORTED(VERIFIED にしない)", bp0 and bp0[0]["admission_status"] == "REPORTED")
    # 独立再検証 OK → VERIFIED(tested scope)
    r1 = RP.ingest_result_packet(BASE_PACKET, reverify=lambda: (True, "EGL re-ran tests: 17/17 PASS"))
    bp1 = [a for a in r1["admitted"] if a["validation_target"] == "BEHAVIORAL_PROPERTY"]
    check("BEHAVIORAL: EGL 独立再検証 OK → VERIFIED(RUN_ARTIFACT)", bp1 and bp1[0]["admission_status"] == "VERIFIED")
    # 再検証 FAIL → REPORTED(昇格しない)
    r2 = RP.ingest_result_packet(BASE_PACKET, reverify=lambda: (False, "EGL re-ran tests: FAIL"))
    bp2 = [a for a in r2["admitted"] if a["validation_target"] == "BEHAVIORAL_PROPERTY"]
    check("BEHAVIORAL: 再検証 FAIL → REPORTED(VERIFIED にしない)", bp2 and bp2[0]["admission_status"] == "REPORTED")


def t_overclaim_rejected():
    pkt = dict(BASE_PACKET, proposed_claims=[{"proposed": "RRI §9 is correct", "scope": "general correctness"}])
    r = RP.ingest_result_packet(pkt, reverify=lambda: (True, "ok"))
    check("over-claim(一般正当性)は REJECTED", any("§9 is correct" in x["claim"] for x in r["rejected"]))
    check("over-claim は admitted に入らない", not any("§9 is correct" in a.get("claim", "") for a in r["admitted"]))


def t_gaps_and_nonguarantees():
    r = RP.ingest_result_packet(BASE_PACKET, reverify=lambda: (True, "ok"))
    check("new_gap_candidates → open gaps", "axis assessment not in slice" in r["gaps"])
    check("non_guarantees に『RRI overall は first-slice』を保持", any("first-slice" in n for n in r["non_guarantees"]))


if __name__ == "__main__":
    print("=== DW→EGL RESULT_PACKET ingestion(EGL は DW を無条件に信じない)===")
    print("\n[RECORD_OCCURRENCE]"); t_record_occurrence_admitted()
    print("\n[BEHAVIORAL needs EGL reverify]"); t_behavioral_needs_egl_reverify()
    print("\n[over-claim rejected]"); t_overclaim_rejected()
    print("\n[gaps + non-guarantees]"); t_gaps_and_nonguarantees()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n=== {len(RESULTS) - len(failed)}/{len(RESULTS)} PASS ===")
    if failed:
        print("FAILED: " + ", ".join(failed)); sys.exit(1)
    print("EGL admission: 記録存在は admit、behavioral は EGL 独立再検証で初めて VERIFIED、over-claim は弾く。")
