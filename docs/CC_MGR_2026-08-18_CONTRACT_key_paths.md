BUILD_CAPABILITY: CC_MGR_2026-08-18_CONTRACT_key_paths.md

<<<2DER:SKELETON>>>
def key_paths(a, b):
    """Implement key_paths(value, max_depth) in impl.py. Args: value (any), max_depth (int, not bool). Returns: sorted unique list of path strings. Logic: If max_depth <= 0, return []. If value is empty dict/list, return []. If value is dict, for each key, path is parent + '.' + key; recurse into value with depth-1. If value is list, only first element; path is parent + '[]' + element_path; recurse into first element with depth-1. If leaf, path is str(value). If depth reached, keep path and stop. Sort results. Raise TypeError if max_depth not int or is bool. Pure function, standard library only.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>

<<<2DER:IMMUTABLE_TESTS>>>
import os
import json
from impl import key_paths

def test_basic_dict():
    assert key_paths({"a": 1}, 1) == ["a"]

def test_basic_list():
    assert key_paths([1], 1) == ["[]1"]

def test_nested_dict():
    assert key_paths({"a": {"b": 2}}, 2) == ["a", "a.b"]

def test_nested_list():
    assert key_paths([[1]], 2) == ["[]", "[][]1"]

def test_leaf():
    assert key_paths(10, 1) == ["10"]

def test_empty_dict():
    assert key_paths({}, 1) == []

def test_empty_list():
    assert key_paths([], 1) == []

def test_max_depth_zero():
    assert key_paths({"a": 1}, 0) == []

def test_type_error():
    try:
        key_paths({}, "a")
        assert False
    except TypeError:
        pass

def test_bool_rejected():
    try:
        key_paths({}, True)
        assert False
    except TypeError:
        pass

def test_uniqueness():
    assert key_paths({"a": 1, "a": 2}, 1) == ["a"]

def test_file_exists():
    assert os.path.exists("impl.py")

def test_json_error():
    try:
        json.loads("bad json")
        assert False
    except json.JSONDecodeError:
        pass

<<<2DER:END>>>
