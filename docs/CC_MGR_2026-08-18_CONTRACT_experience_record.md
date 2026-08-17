# 契約: 経験の 記録(§20 還流)の 形(★2DER 生成 ／ MGR は 置いただけ)

- 台帳: ITEM-2DER-EVO-0072 ／ task: TASK-2DER-35FEC468 ／ ★Taka 承認 2026-08-18
- ★5鍵は v0.2 §20 逐語(required materials / Worker構成 / 成功経路 / 失敗型 / 検証面)に対応

<<<2DER:SKELETON>>>
def compile_experience_record(a, b, c, d, e):
    """Create a pure function named compile_experience_record that takes exactly five list arguments: required_materials, worker_roles, success_paths, failure_types, and verification. Each list must contain only strings. If any argument is not a list, raise TypeError. If any element in any list is not a string, raise TypeError. Deduplicate each list while preserving the original order of first occurrence. If all five lists are empty after deduplication, raise ValueError. Return a dictionary with keys exactly in the order: required_materials, worker_roles, success_paths, failure_types, verification, mapping to the deduplicated lists. The function must be deterministic and use only the Python standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import compile_experience_record

def test_valid_input():
    result = compile_experience_record(["a", "b"], ["x"], ["s1"], ["f1"], ["v1"])
    assert result == {"required_materials": ["a", "b"], "worker_roles": ["x"], "success_paths": ["s1"], "failure_types": ["f1"], "verification": ["v1"]}

def test_deduplication():
    result = compile_experience_record(["a", "a", "b"], ["x", "x"], ["s1", "s1"], ["f1"], ["v1"])
    assert result == {"required_materials": ["a", "b"], "worker_roles": ["x"], "success_paths": ["s1"], "failure_types": ["f1"], "verification": ["v1"]}

def test_empty_lists():
    try:
        compile_experience_record([], [], [], [], [])
        assert False, "Expected ValueError"
    except ValueError:
        pass

def test_non_list_input():
    try:
        compile_experience_record("not a list", [], [], [], [])
        assert False, "Expected TypeError"
    except TypeError:
        pass

def test_non_string_element():
    try:
        compile_experience_record([1, 2], [], [], [], [])
        assert False, "Expected TypeError"
    except TypeError:
        pass

def test_order_preservation():
    result = compile_experience_record(["c", "a", "b", "a"], ["y", "x", "y"], ["p1", "p2", "p1"], ["f1"], ["v1"])
    assert result["required_materials"] == ["c", "a", "b"]
    assert result["worker_roles"] == ["y", "x"]
    assert result["success_paths"] == ["p1", "p2"]
    assert list(result.keys()) == ["required_materials", "worker_roles", "success_paths", "failure_types", "verification"]

def test_determinism():
    r1 = compile_experience_record(["a"], ["x"], ["s"], ["f"], ["v"])
    r2 = compile_experience_record(["a"], ["x"], ["s"], ["f"], ["v"])
    assert r1 == r2
<<<2DER:END>>>
