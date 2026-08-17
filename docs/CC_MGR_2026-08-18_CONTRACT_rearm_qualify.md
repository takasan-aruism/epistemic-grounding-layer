# 契約: 門の 再武装 資格判定(★2DER が 生成 ／ MGR は 置いただけ)

- 台帳: ITEM-2DER-EVO-0071 ／ task: TASK-2DER-E6B1597A
- ★Taka 裁定 2026-08-18: 認可の鍵を『現在の submit context』から『task 自身の証拠』へ
- ★対象は DISARMED のみ。MISSING_PROVENANCE 186 は対象外

<<<2DER:SKELETON>>>
def evaluate_gate_rearm(a, b, c, d, e, f, g, h):
    """Create a pure Python function evaluate_gate_rearm that accepts eight arguments: task_id (str), gate_task_id (str), gate_exists (bool), blocked (bool), current_role (str), is_human_gate (bool), unprocessed_findings_count (int), and material_ready (bool). The function must evaluate conditions in this exact fixed order: 1. gate_exists (else MISSING_GATE), 2. task_id == gate_task_id (else TASK_MISMATCH), 3. not blocked (else BLOCKED), 4. current_role in ['CODING_WORKER', 'INDEPENDENT_AUDITOR'] (else HUMAN_BARRIER), 5. unprocessed_findings_count == 0 (else UNDISPOSED_FINDING), 6. material_ready (else MISSING_MATERIAL). If all pass, return ('REARM', 6). On any failure, return ('REASON', check_count). The function must be deterministic, pure, and use only the Python standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from impl import evaluate_gate_rearm

def test_rearm_success():
    res = evaluate_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 0, True)
    assert res == ("REARM", 6)

def test_missing_gate():
    res = evaluate_gate_rearm("t1", "t1", False, False, "CODING_WORKER", False, 0, True)
    assert res == ("MISSING_GATE", 1)

def test_task_mismatch():
    res = evaluate_gate_rearm("t1", "t2", True, False, "CODING_WORKER", False, 0, True)
    assert res == ("TASK_MISMATCH", 2)

def test_blocked():
    res = evaluate_gate_rearm("t1", "t1", True, True, "CODING_WORKER", False, 0, True)
    assert res == ("BLOCKED", 3)

def test_human_barrier():
    res = evaluate_gate_rearm("t1", "t1", True, False, "MANAGER", False, 0, True)
    assert res == ("HUMAN_BARRIER", 4)

def test_undisposed_finding():
    res = evaluate_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 5, True)
    assert res == ("UNDISPOSED_FINDING", 5)

def test_missing_material():
    res = evaluate_gate_rearm("t1", "t1", True, False, "CODING_WORKER", False, 0, False)
    assert res == ("MISSING_MATERIAL", 6)

def test_missing_arguments():
    try:
        evaluate_gate_rearm()
        assert False, "Should raise TypeError for missing arguments"
    except TypeError:
        pass

def test_malformed_json_input():
    try:
        evaluate_gate_rearm(None, None, "not_bool", None, None, None, "not_int", None)
        assert False, "Should handle or raise on invalid types"
    except (TypeError, AttributeError):
        pass
<<<2DER:END>>>
