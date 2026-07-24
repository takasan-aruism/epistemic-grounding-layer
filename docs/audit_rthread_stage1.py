#!/usr/bin/env python3
"""CC 設計整合監査ハーネス — RRI RTHREAD stage 1 v0.1（決定論・セルフテスト付き=族A回避）。

対象: rri/rri/request_thread.py（実装インスタンス作）に対する SPEC_RTHREAD_STAGE1_v0.1.md 整合監査。
監査は self-report を信じない（author≠auditor）。3 検査:
  A. 骨格保存（定数/例外/_mint/署名が §2 と byte 一致）
  B. 4 テスト green の再実行
  C. 保存則 I1 が「実イベント経路の bookkeeping バグ」を実際に検出するか（load-bearing 性）
     ↑ ここが finding。C はセルフテスト（意図的に壊した参照実装で HALT を検出できること）で空振りしないことを先に示す。

使い方: cd /home/takasan/rri && python /home/takasan/egl/docs/audit_rthread_stage1.py
"""
import importlib
import os
import subprocess
import sys
import tempfile

RRI = "/home/takasan/rri"
SRC = os.path.join(RRI, "rri", "request_thread.py")
SPEC = "/home/takasan/egl/docs/SPEC_RTHREAD_STAGE1_v0.1.md"


def _load():
    os.environ["RTHREAD_EVENTS"] = tempfile.mktemp(suffix=".jsonl")
    sys.path.insert(0, RRI)
    import rri.request_thread as m
    importlib.reload(m)
    return m


def check_A_skeleton():
    src = open(SRC).read()
    block = open(SPEC).read().split("```python", 1)[1].split("```", 1)[0]
    invariants = [
        'EVENT_TYPES = ("THREAD_OPENED", "QUESTION_RAISED", "QUESTION_DISPOSED", "NARROWED",',
        'STATES = ("SOFT", "NARROWING", "AWAITING_HUMAN", "RESOLVED", "DISPATCHABLE", "CLOSED")',
        'DISPOSALS = ("RESOLVED", "OPEN_GAP", "REJECTED", "MERGED_INTO")',
        'UNCLASSIFIED_FORBIDDEN_DISPOSAL = ("RESOLVED",)',
        '("NARROWING", "RESOLVED"): ("all_disposed", "suspense_settled", "all_gaps_presented", "thread_accepted"),',
        '("RESOLVED", "DISPATCHABLE"): ("__DEFERRED__",),',
        'return "%s-%s" % (prefix, hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:8])',
    ]
    sigs = [
        "def _append(event):", "def _read(thread_id):", "def open_thread(ds_thread_ref, ts):",
        'def raise_question(thread_id, memo, ts, account_id="DEFAULT"):',
        "def dispose_question(thread_id, question_id, disposal, ts, reason_code=None, target_id=None):",
        "def present_gaps(thread_id, question_ids, ds_delivery_receipt, ts):",
        "def human_replied(thread_id, answer_refs, ts):",
        "def advance_state(thread_id, to_state, guard_evidence, ts):",
        "def accept_thread(thread_id, residual_gaps, human_ref, ts):",
        "def project(thread_id):", "def check_conservation(projection):",
    ]
    bad = [x for x in invariants + sigs if x not in src or x not in block]
    return (not bad), bad


def check_B_tests():
    r = subprocess.run([sys.executable, "-m", "pytest", "rri/test_request_thread_stage1.py", "-q"],
                       cwd=RRI, capture_output=True, text=True)
    return (r.returncode == 0), r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr


def _double_dispose(m):
    """実イベント経路で同一問いを2度処分する（module の sole writer 経由）。"""
    tid = m.open_thread("DS-audit", "T")
    q1 = m.raise_question(tid, "q1", "T", account_id="DEFAULT")
    m.dispose_question(tid, q1, "RESOLVED", "T")
    m._append({"type": "QUESTION_DISPOSED", "thread_id": tid, "question_id": q1,
               "disposal": "OPEN_GAP", "reason_code": None, "target_id": None,
               "ts": "T", "sealed_by": "rri.request_thread"})
    return m.project(tid)


def check_C_load_bearing():
    """保存則が『実経路の二重処分』を検出できるか。検出できないなら I1 は tautology（finding）。"""
    m = _load()
    proj = _double_dispose(m)
    try:
        m.check_conservation(proj)
        detected = False  # halt しなかった = 検出できない
    except m.RThreadConservationError:
        detected = True
    return detected, proj


def selftest_C():
    """族A回避: C の検出器が『本当に壊れたら赤になる』ことを、load-bearing な参照実装で先に示す。
    独立導出版 in_flight（未処分の raised 問い数）なら二重処分で HALT するはず。"""
    m = _load()
    tid = m.open_thread("DS-self", "T")
    q1 = m.raise_question(tid, "q1", "T", account_id="DEFAULT")
    m.dispose_question(tid, q1, "RESOLVED", "T")
    m._append({"type": "QUESTION_DISPOSED", "thread_id": tid, "question_id": q1,
               "disposal": "OPEN_GAP", "reason_code": None, "target_id": None,
               "ts": "T", "sealed_by": "rri.request_thread"})
    events = m._read(tid)
    raised_qids = [e["question_id"] for e in events if e.get("type") == "QUESTION_RAISED"]
    disposed_qids = {e["question_id"] for e in events if e.get("type") == "QUESTION_DISPOSED"}
    disposal_events = sum(1 for e in events if e.get("type") == "QUESTION_DISPOSED")
    in_flight_indep = sum(1 for q in raised_qids if q not in disposed_qids)
    # load-bearing I1: raised == Σdisposal_events + in_flight_indep
    ok = (len(raised_qids) == disposal_events + in_flight_indep)
    return (not ok)  # 独立導出なら不成立を検出できる=True が期待


def main():
    print("=== CC AUDIT: RTHREAD stage 1 v0.1 ===")
    a_ok, a_bad = check_A_skeleton()
    print("A. 骨格保存:", "PASS" if a_ok else f"FAIL {a_bad}")
    b_ok, b_line = check_B_tests()
    print("B. 4テスト:", "PASS" if b_ok else "FAIL", "|", b_line)
    self_ok = selftest_C()
    print("   [selftest C] 独立導出の参照実装は二重処分を検出できる:", "OK(空振りしない)" if self_ok else "XX")
    detected, proj = check_C_load_bearing()
    print("C. 保存則 load-bearing:", "PASS" if detected else "FAIL(tautology)",
          "| 二重処分 projection:", {k: proj[k] for k in ("raised_total", "resolved", "open_gap", "in_flight_count")})
    verdict = a_ok and b_ok and self_ok and detected
    print("\nVERDICT:", "CONSISTENT" if verdict else "NOT CONSISTENT — finding(s) below")
    if not detected:
        print("  F-1 (HIGH): I1 は project() の plug in_flight により実経路では恒等式。二重処分/幻処分を検出せず。"
              " 起源=§2 骨格 project docstring（設計=CC-α 責）。実装は骨格に忠実。")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
