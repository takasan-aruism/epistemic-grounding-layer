# 契約: 門の 再武装 資格判定 v3(★引数 4・番号で 固定)

- 台帳: ITEM-2DER-EVO-0071 ／ task: TASK-2DER-1C235BC3
- ★v1=型違反 未記載で 落ち ／ ★v2=位置引数8個で 順序ずれ

<<<2DER:SKELETON>>>
def decide_rearm(a, b, c, d):
    """Implement a pure function `decide_rearm(gate_exists, blocked, role, findings_count)` that takes four arguments. It must check types first, raising TypeError if any argument is of the wrong type (bool, bool, str, int respectively). Then it checks conditions in order: if `gate_exists` is False, return 'MISSING_GATE'; if `blocked` is True, return 'BLOCKED'; if `role` is not 'CODING_WORKER' or 'INDEPENDENT_AUDITOR', return 'HUMAN_BARRIER'; if `findings_count` > 0, return 'UNDISPOSED_FINDING'; otherwise return 'REARM'. The function must be deterministic and use only standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import decide_rearm

def test_rearm_all_valid():
    assert decide_rearm(True, False, 'CODING_WORKER', 0) == 'REARM'
    assert decide_rearm(True, False, 'INDEPENDENT_AUDITOR', 0) == 'REARM'

def test_missing_gate():
    assert decide_rearm(False, False, 'CODING_WORKER', 0) == 'MISSING_GATE'

def test_blocked():
    assert decide_rearm(True, True, 'CODING_WORKER', 0) == 'BLOCKED'

def test_human_barrier():
    assert decide_rearm(True, False, 'UNKNOWN', 0) == 'HUMAN_BARRIER'

def test_undisposed_finding():
    assert decide_rearm(True, False, 'CODING_WORKER', 1) == 'UNDISPOSED_FINDING'

def test_type_error_gate():
    try:
        decide_rearm('yes', False, 'CODING_WORKER', 0)
        assert False
    except TypeError:
        pass

def test_type_error_blocked():
    try:
        decide_rearm(True, 'no', 'CODING_WORKER', 0)
        assert False
    except TypeError:
        pass

def test_type_error_role():
    try:
        decide_rearm(True, False, 123, 0)
        assert False
    except TypeError:
        pass

def test_type_error_findings():
    try:
        decide_rearm(True, False, 'CODING_WORKER', '1')
        assert False
    except TypeError:
        pass

def test_precedence():
    assert decide_rearm(False, True, 'UNKNOWN', 1) == 'MISSING_GATE'
    assert decide_rearm(True, True, 'UNKNOWN', 1) == 'BLOCKED'
    assert decide_rearm(True, False, 'UNKNOWN', 1) == 'HUMAN_BARRIER'
    assert decide_rearm(True, False, 'CODING_WORKER', 1) == 'UNDISPOSED_FINDING'
<<<2DER:END>>>
