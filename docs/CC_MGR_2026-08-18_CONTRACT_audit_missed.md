BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_audit_missed.md

<<<2DER:SKELETON>>>
def audit_missed(a, b):
    """Implement a pure Python function audit_missed(declared, observed) that takes two lists of strings. It must validate that both arguments are lists, contain only non-empty strings, and raise TypeError or ValueError accordingly. The function computes a list of missing keys (items in declared not in observed, preserving order and duplicates), counts for declared and observed, and a verdict string determined by: 'NO_DECLARATION' if declared is empty, 'EVIDENCE_COMPLETE' if missing is empty, 'NO_EVIDENCE' if observed is empty, else 'EVIDENCE_MISSING'. It returns a dict with keys 'verdict', 'missing', 'declared', 'observed'. Inputs must not be mutated. Case-sensitive and duplicate-aware. Standard library only. Deterministic output.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import audit_missed

def test_normal_missing():
    result = audit_missed(['a', 'b', 'c'], ['a', 'c'])
    assert result['verdict'] == 'EVIDENCE_MISSING'
    assert result['missing'] == ['b']
    assert result['declared'] == 3
    assert result['observed'] == 2

def test_evidence_complete():
    result = audit_missed(['a', 'b'], ['a', 'b', 'c'])
    assert result['verdict'] == 'EVIDENCE_COMPLETE'
    assert result['missing'] == []
    assert result['declared'] == 2
    assert result['observed'] == 3

def test_no_declaration():
    result = audit_missed([], ['a'])
    assert result['verdict'] == 'NO_DECLARATION'
    assert result['missing'] == []
    assert result['declared'] == 0
    assert result['observed'] == 1

def test_no_evidence():
    result = audit_missed(['a'], [])
    assert result['verdict'] == 'NO_EVIDENCE'
    assert result['missing'] == ['a']
    assert result['declared'] == 1
    assert result['observed'] == 0

def test_both_empty():
    result = audit_missed([], [])
    assert result['verdict'] == 'NO_DECLARATION'
    assert result['missing'] == []
    assert result['declared'] == 0
    assert result['observed'] == 0

def test_duplicates():
    result = audit_missed(['a', 'a', 'b'], ['a'])
    assert result['verdict'] == 'EVIDENCE_MISSING'
    assert result['missing'] == ['a', 'b']
    assert result['declared'] == 3
    assert result['observed'] == 1

def test_case_sensitive():
    result = audit_missed(['Key', 'key'], ['KEY', 'key'])
    assert result['verdict'] == 'EVIDENCE_MISSING'
    assert result['missing'] == ['Key']
    assert result['declared'] == 2
    assert result['observed'] == 2

def test_type_error_declared_not_list():
    try:
        audit_missed('not a list', ['a'])
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_observed_not_list():
    try:
        audit_missed(['a'], 'not a list')
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_declared_non_string():
    try:
        audit_missed([1, 'a'], ['a'])
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_type_error_observed_non_string():
    try:
        audit_missed(['a'], [1])
        assert False, 'Expected TypeError'
    except TypeError:
        pass

def test_value_error_declared_empty_string():
    try:
        audit_missed(['', 'a'], ['a'])
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_value_error_observed_empty_string():
    try:
        audit_missed(['a'], ['', 'a'])
        assert False, 'Expected ValueError'
    except ValueError:
        pass

def test_immutability():
    declared = ['a', 'b']
    observed = ['a']
    declared_copy = declared.copy()
    observed_copy = observed.copy()
    audit_missed(declared, observed)
    assert declared == declared_copy
    assert observed == observed_copy

def test_determinism():
    result1 = audit_missed(['a', 'b'], ['a'])
    result2 = audit_missed(['a', 'b'], ['a'])
    assert result1 == result2

def test_missing_order():
    result = audit_missed(['c', 'a', 'b'], ['a'])
    assert result['missing'] == ['c', 'b']
<<<2DER:END>>>
