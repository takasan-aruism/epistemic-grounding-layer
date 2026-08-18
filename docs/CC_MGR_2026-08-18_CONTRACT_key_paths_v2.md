BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_key_paths_v2.md

<<<2DER:SKELETON>>>
def key_paths_v2(a, b):
    """Implement key_paths_v2(data, depth) that extracts all key paths from a nested structure. Paths are built by joining keys with dots; root keys have no prefix. Dictionaries trigger path creation and recursion; lists contribute only their first element; other values terminate the branch. Depth counts top-level keys as 1; recursion stops when depth equals the limit. Return a sorted, deduplicated list of path strings. Raise TypeError if depth is not an integer or is a boolean. Return empty list for non-dict input, empty dict, or depth <= 0. Do not mutate input. Pure function using only standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
from impl import key_paths_v2

def test_basic_dict():
    assert key_paths_v2({"a": 1}, 1) == ["a"]

def test_nested_dict():
    assert key_paths_v2({"a": {"b": 1}}, 2) == ["a", "a.b"]

def test_list_first_item():
    assert key_paths_v2({"a": [1]}, 2) == ["a"]

def test_empty_list():
    assert key_paths_v2({"a": []}, 2) == ["a"]

def test_depth_limit():
    assert key_paths_v2({"a": {"b": {"c": 1}}}, 2) == ["a", "a.b"]

def test_depth_zero():
    assert key_paths_v2({"a": 1}, 0) == []

def test_not_dict():
    assert key_paths_v2("string", 1) == []

def test_empty_dict():
    assert key_paths_v2({}, 1) == []

def test_type_error():
    try:
        key_paths_v2({"a": 1}, 1.5)
        assert False
    except TypeError:
        pass

def test_boolean_not_int():
    try:
        key_paths_v2({"a": 1}, True)
        assert False
    except TypeError:
        pass

def test_sorted_unique():
    assert key_paths_v2({"a": 1, "b": 1}, 1) == ["a", "b"]

def test_no_modification():
    d = {"a": 1}
    key_paths_v2(d, 1)
    assert d == {"a": 1}
<<<2DER:END>>>
