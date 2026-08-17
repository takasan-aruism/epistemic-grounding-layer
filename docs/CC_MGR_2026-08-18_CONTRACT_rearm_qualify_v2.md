# 契約: 門の 再武装 資格判定 v2(★型違反の 扱いを 依頼文に 足した 版)

- 台帳: ITEM-2DER-EVO-0071 ／ task: TASK-2DER-C17E370D
- ★v1(TASK-2DER-1D372BA4)は ★型が 違う 時の 扱いを 私が 書かず ★封印試験が 決めて 落ちた(8通過/1失敗)

<<<2DER:SKELETON>>>
def check_gate_rearm(a, b, c, d, e, f, g, h):
    """Create a pure Python function named check_gate_rearm that accepts eight parameters: task_id (str), gate_task_id (str), gate_exists (bool), blocked (bool), role (str), is_human_barrier (bool), undisposed_findings_count (int), and current_stage_material_ready (bool). The function must validate input types strictly, raising TypeError on mismatch. It must evaluate conditions in the fixed order: MISSING_GATE (gate_exists), TASK_MISMATCH (task_id == gate_task_id), BLOCKED (not blocked), HUMAN_BARRIER (role is CODING_WORKER or INDEPENDENT_AUDITOR implies machine role, otherwise human barrier check), UNDISPOSED_FINDING (undisposed_findings_count == 0), and MISSING_MATERIAL (current_stage_material_ready). If all checks pass, return ('REARM', 6). Otherwise, return the name of the first failing check and the count of checks performed up to that point. The function must be deterministic and use only the Python standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from impl import check_gate_rearm

def test_rearm_all_pass():
    res = check_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 0, True)
    assert res == ("REARM", 6)

def test_missing_gate():
    res = check_gate_rearm("t1", "t1", False, False, "CODING_WORKER", False, 0, True)
    assert res == ("MISSING_GATE", 1)

def test_task_mismatch():
    res = check_gate_rearm("t1", "t2", True, False, "CODING_WORKER", False, 0, True)
    assert res == ("TASK_MISMATCH", 2)

def test_blocked():
    res = check_gate_rearm("t1", "t1", True, True, "CODING_WORKER", False, 0, True)
    assert res == ("BLOCKED", 3)

def test_human_barrier():
    res = check_gate_rearm("t1", "t1", True, False, "MANUAL_REVIEWER", False, 0, True)
    assert res == ("HUMAN_BARRIER", 4)

def test_undisposed_finding():
    res = check_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 1, True)
    assert res == ("UNDISPOSED_FINDING", 5)

def test_missing_material():
    res = check_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 0, False)
    assert res == ("MISSING_MATERIAL", 6)

def test_type_error_invalid_task_id():
    try:
        check_gate_rearm(123, "t1", True, False, "CODING_WORKER", False, 0, True)
        assert False, "Should raise TypeError"
    except TypeError:
        pass

def test_type_error_invalid_count():
    try:
        check_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, "zero", True)
        assert False, "Should raise TypeError"
    except TypeError:
        pass

def test_type_error_invalid_bool():
    try:
        check_gate_rearm("t1", "t1", "yes", False, "CODING_WORKER", False, 0, True)
        assert False, "Should raise TypeError"
    except TypeError:
        pass

def test_missing_file_case():
    assert callable(check_gate_rearm)
    assert os.path.exists(os.path.join(os.path.dirname(__file__), "impl.py"))

def test_malformed_json_case():
    try:
        check_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 0, None)
        assert False, "Should raise TypeError"
    except TypeError:
        pass

<<<2DER:END>>>
