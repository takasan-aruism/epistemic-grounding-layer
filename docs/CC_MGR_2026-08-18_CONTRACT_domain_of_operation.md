BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_domain_of_operation.md

<<<2DER:SKELETON>>>
def get_domain(a, b):
    """Create a pure function get_domain(operation_name, domain_mapping) that takes an operation name string and a domain mapping dictionary. The function must validate that operation_name is a non-empty string and domain_mapping is a dict with list values. It should return the first domain name where the operation is listed, 'NO_DOMAIN' if not found or if the dict is empty, and raise TypeError or ValueError as specified.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import get_domain

def test_valid_mapping():
    mapping = {"A": ["op1"], "B": ["op2"]}
    assert get_domain("op1", mapping) == "A"
    assert get_domain("op2", mapping) == "B"

def test_multiple_domains():
    mapping = {"B": ["op1"], "A": ["op1"]}
    assert get_domain("op1", mapping) == "B"

def test_not_found():
    mapping = {"A": ["op1"]}
    assert get_domain("op2", mapping) == "NO_DOMAIN"

def test_empty_dict():
    assert get_domain("op1", {}) == "NO_DOMAIN"

def test_empty_string():
    try:
        get_domain("", {"A": ["op1"]})
        assert False
    except ValueError:
        pass

def test_invalid_op_type():
    try:
        get_domain(123, {"A": ["op1"]})
        assert False
    except TypeError:
        pass

def test_invalid_mapping_type():
    try:
        get_domain("op1", "string")
        assert False
    except TypeError:
        pass

def test_invalid_value_type():
    try:
        get_domain("op1", {"A": "string"})
        assert False
    except TypeError:
        pass
<<<2DER:END>>>
