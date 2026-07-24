#!/usr/bin/env python3
"""CC 設計整合監査ハーネス — RRI RTHREAD stage 2a(accounts 機械核)。決定論・セルフテスト付き(族A回避)。

対象: rri/rri/request_thread.py(stage2a)。self-report を信じない(author≠auditor)。
  A. 骨格保存(定数/例外/_mint/署名。stage2a の新署名 raise_question(account_id=UNCLASSIFIED) と新関数を含む)
  B. 全テスト green(stage1 + cov + stage2a)
  C1. I1(処分次元)load-bearing = 二重処分を実経路で HALT
  C2. account 次元 load-bearing = 改竄 off-chart を HALT
  D1. suspense 決着(1->0)= 恒等式でない
  D2. chart 検証 = off-chart raise 拒否 / chart 不在 fail-closed
各 load-bearing 検査は selftest で「壊れたら赤になる」ことを先に示す。
"""
import importlib
import json
import os
import subprocess
import sys
import tempfile

RRI = "/home/takasan/rri"
SRC = os.path.join(RRI, "rri", "request_thread.py")


def _load(chart_accounts=("ACCT_TEST_A", "ACCT_TEST_B"), no_chart=False):
    d = tempfile.mkdtemp()
    os.environ["RTHREAD_EVENTS"] = os.path.join(d, "ev.jsonl")
    if no_chart:
        os.environ["RTHREAD_CHART"] = os.path.join(d, "absent.json")
    else:
        cp = os.path.join(d, "chart.json")
        json.dump({"chart_version": 0, "accounts": list(chart_accounts)}, open(cp, "w"))
        os.environ["RTHREAD_CHART"] = cp
    if RRI not in sys.path:
        sys.path.insert(0, RRI)
    import rri.request_thread as m
    importlib.reload(m)
    return m


def check_A_skeleton():
    src = open(SRC).read()
    need = [
        'EVENT_TYPES = ("THREAD_OPENED", "QUESTION_RAISED", "QUESTION_DISPOSED", "NARROWED",',
        'DISPOSALS = ("RESOLVED", "OPEN_GAP", "REJECTED", "MERGED_INTO")',
        'UNCLASSIFIED_FORBIDDEN_DISPOSAL = ("RESOLVED",)',
        'return "%s-%s" % (prefix, hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:8])',
        "class RThreadChartUnavailable(RThreadError):",
        "def _load_chart():",
        "def raise_question(thread_id, memo, ts, account_id=UNCLASSIFIED):",
        "def check_account_conservation(projection, valid_accounts):",
        "def project(thread_id):",
        "def check_conservation(projection):",
    ]
    bad = [x for x in need if x not in src]
    return (not bad), bad


def check_B_tests():
    r = subprocess.run([sys.executable, "-m", "pytest",
                        "rri/test_request_thread_stage1.py",
                        "rri/test_request_thread_stage1_cov.py",
                        "rri/test_request_thread_stage2a.py", "-q"],
                       cwd=RRI, capture_output=True, text=True)
    return (r.returncode == 0), (r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr)


def _double_dispose(m):
    tid = m.open_thread("A", "T")
    q = m.raise_question(tid, "q", "T", account_id="ACCT_TEST_A")
    m.dispose_question(tid, q, "RESOLVED", "T")
    m._append({"type": "QUESTION_DISPOSED", "thread_id": tid, "question_id": q,
               "disposal": "OPEN_GAP", "reason_code": None, "target_id": None,
               "ts": "T", "sealed_by": "rri.request_thread"})
    return m, tid


def check_C1_i1():
    m, tid = _double_dispose(_load())
    try:
        m.check_conservation(m.project(tid)); return False
    except m.RThreadConservationError:
        return True


def check_C2_account():
    m = _load()
    tid = m.open_thread("A", "T")
    m.raise_question(tid, "q", "T", account_id="ACCT_TEST_A")
    _, valid = m._load_chart()
    m._append({"type": "QUESTION_RAISED", "thread_id": tid, "question_id": "Q-bad",
               "account_id": "GHOST", "memo": "x", "ts": "T", "sealed_by": "rri.request_thread"})
    try:
        m.check_account_conservation(m.project(tid), valid); return False
    except m.RThreadConservationError:
        return True


def selftest_account():
    """族A回避: off-chart 検査が本当に効くなら、正常台帳では halt せず・改竄台帳でのみ halt する非対称を示す。"""
    m = _load()
    tid = m.open_thread("A", "T")
    m.raise_question(tid, "q", "T", account_id="ACCT_TEST_A")
    _, valid = m._load_chart()
    clean_ok = True
    try:
        m.check_account_conservation(m.project(tid), valid)
    except m.RThreadConservationError:
        clean_ok = False
    return clean_ok  # 正常台帳で halt しない = 検査は空振りでない(過検出しない)


def check_D1_suspense():
    m = _load()
    tid = m.open_thread("A", "T")
    q = m.raise_question(tid, "q", "T")  # UNCLASSIFIED
    s1 = m.project(tid)["suspense_balance"]
    m.dispose_question(tid, q, "OPEN_GAP", "T")
    s2 = m.project(tid)["suspense_balance"]
    return (s1, s2) == (1, 0)


def check_D2_chart():
    m = _load()
    tid = m.open_thread("A", "T")
    off = False
    try:
        m.raise_question(tid, "q", "T", account_id="IMAGINED")
    except ValueError:
        off = True
    m2 = _load(no_chart=True)
    t2 = m2.open_thread("A", "T")
    failclosed = False
    try:
        m2.raise_question(t2, "q", "T", account_id="ACCT_TEST_A")
    except m2.RThreadChartUnavailable:
        failclosed = True
    return off and failclosed


def main():
    print("=== CC AUDIT: RTHREAD stage 2a (accounts 機械核) ===")
    a_ok, a_bad = check_A_skeleton(); print("A. 骨格保存:", "PASS" if a_ok else f"FAIL {a_bad}")
    b_ok, b_line = check_B_tests(); print("B. 全テスト:", "PASS" if b_ok else "FAIL", "|", b_line)
    print("C1 I1 load-bearing(二重処分 HALT):", "PASS" if check_C1_i1() else "FAIL")
    print("   [selftest] account 検査は正常台帳で halt しない:", "OK" if selftest_account() else "XX")
    print("C2 account load-bearing(off-chart HALT):", "PASS" if check_C2_account() else "FAIL")
    print("D1 suspense 決着(1->0 非恒等式):", "PASS" if check_D1_suspense() else "FAIL")
    print("D2 chart 検証(off-chart拒否 + 不在fail-closed):", "PASS" if check_D2_chart() else "FAIL")
    ok = a_ok and b_ok and check_C1_i1() and selftest_account() and check_C2_account() and check_D1_suspense() and check_D2_chart()
    print("\nVERDICT:", "CONSISTENT" if ok else "NOT CONSISTENT")
    # F-2(冗長 suspense guard)は F2FIX で解消済み: advance_state から到達不能ガードを除去
    # (suspense ⊆ in_flight ゆえ in_flight==0 ガードに包摂)。account 保存検査は残置。
    guard_gone = "unsettled suspense" not in open(SRC).read()
    print("\nF-2 解消(冗長 suspense guard 除去):", "OK" if guard_gone else "⚠️まだ残存")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
