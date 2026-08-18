BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_audit_missed_v2.md

<<<2DER:SKELETON>>>
def audit_missed(a, b):
    """Create a function audit_missed(declared_keys, observed_keys) that takes two lists of strings. It must validate that inputs are lists of non-empty strings, raising TypeError or ValueError as appropriate. It computes a 'missing' list of keys present in declared_keys but not in observed_keys, preserving declared_keys order. It returns a dict with keys 'verdict', 'missing', 'declared', 'observed'. 'declared' and 'observed' are the lengths. 'verdict' is determined by: 'NO_DECLARATION' if declared_keys is empty; 'EVIDENCE_COMPLETE' if missing is empty; 'NO_EVIDENCE' if observed_keys is empty; else 'EVIDENCE_MISSING'. The function must be pure and case-sensitive.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import audit_missed

def test_no_declaration():
    res = audit_missed([], ["k1"])
    assert res["verdict"] == "NO_DECLARATION"
    assert res["missing"] == []
    assert res["declared"] == 0
    assert res["observed"] == 1

def test_evidence_complete():
    res = audit_missed(["k1", "k2"], ["k1", "k2"])
    assert res["verdict"] == "EVIDENCE_COMPLETE"
    assert res["missing"] == []
    assert res["declared"] == 2
    assert res["observed"] == 2

def test_no_evidence():
    res = audit_missed(["k1"], [])
    assert res["verdict"] == "NO_EVIDENCE"
    assert res["missing"] == ["k1"]
    assert res["declared"] == 1
    assert res["observed"] == 0

def test_evidence_missing():
    res = audit_missed(["k1", "k2"], ["k1"])
    assert res["verdict"] == "EVIDENCE_MISSING"
    assert res["missing"] == ["k2"]
    assert res["declared"] == 2
    assert res["observed"] == 1

def test_missing_preserves_order():
    res = audit_missed(["b", "a", "c"], ["a"])
    assert res["missing"] == ["b", "c"]

def test_duplicates_in_declared():
    res = audit_missed(["k", "k"], ["k"])
    assert res["missing"] == ["k"]

def test_duplicates_in_observed():
    res = audit_missed(["k"], ["k", "k"])
    assert res["missing"] == []

def test_case_sensitive():
    res = audit_missed(["K"], ["k"])
    assert res["missing"] == ["K"]

def test_no_modification():
    declared = ["k"]
    observed = ["k"]
    audit_missed(declared, observed)
    assert declared == ["k"]
    assert observed == ["k"]

def test_type_error_not_list():
    try:
        audit_missed("k", [])
        assert False
    except TypeError:
        pass

def test_type_error_element():
    try:
        audit_missed([1], [])
        assert False
    except TypeError:
        pass

def test_value_error_empty_string():
    try:
        audit_missed([""], [])
        assert False
    except ValueError:
        pass

def test_empty_observed_with_missing():
    res = audit_missed(["k1", "k2"], [])
    assert res["verdict"] == "NO_EVIDENCE"
    assert res["missing"] == ["k1", "k2"]

<<<2DER:END>>>
