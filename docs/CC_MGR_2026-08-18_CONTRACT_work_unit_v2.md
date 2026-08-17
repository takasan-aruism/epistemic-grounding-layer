# 契約: 作業単位の 組み立て v2(★2DER 生成 ／ MGR は 置いただけ)

- task: TASK-2DER-1666D642 ／ ★v1 は Worker が 空を返した(★型の ローマ字変換を 私が 要求した)
- ★v2 は 略号を 呼び手が 渡す=★難しさを 依頼文から 外した

<<<2DER:SKELETON>>>
def assemble_work_unit(a, b, c, d):
    """Implement a function `assemble_work_unit(id_num, type_code, source, completion)` that returns a dictionary with keys `work_unit_id`, `type`, `source`, `dependency`, `completion`, `required_tests` in that order. `work_unit_id` is formatted as `WU-{type_code}-{id_num:04d}`. `type` is `type_code`. `source` is `source`. `dependency` is `[]`. `completion` is `completion`. `required_tests` is `[completion]`. Raise `ValueError` if `id_num < 0`, `type_code` is not exactly 2 uppercase ASCII letters, `source` is empty, or `completion` is empty. Raise `TypeError` if `id_num` is not an integer (excluding bool), or if `type_code`, `source`, or `completion` are not strings. The function must be pure and deterministic.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import assemble_work_unit

def test_valid_input():
    res = assemble_work_unit(3, "CO", "SRC", "DONE")
    assert res["work_unit_id"] == "WU-CO-0003"
    assert res["type"] == "CO"
    assert res["source"] == "SRC"
    assert res["dependency"] == []
    assert res["completion"] == "DONE"
    assert res["required_tests"] == ["DONE"]
    assert list(res.keys()) == ["work_unit_id", "type", "source", "dependency", "completion", "required_tests"]

def test_id_num_negative():
    try:
        assemble_work_unit(-1, "CO", "SRC", "DONE")
        assert False
    except ValueError:
        pass

def test_type_code_invalid():
    try:
        assemble_work_unit(1, "c", "SRC", "DONE")
        assert False
    except ValueError:
        pass
    try:
        assemble_work_unit(1, "ABC", "SRC", "DONE")
        assert False
    except ValueError:
        pass
    try:
        assemble_work_unit(1, "12", "SRC", "DONE")
        assert False
    except ValueError:
        pass

def test_source_empty():
    try:
        assemble_work_unit(1, "CO", "", "DONE")
        assert False
    except ValueError:
        pass

def test_completion_empty():
    try:
        assemble_work_unit(1, "CO", "SRC", "")
        assert False
    except ValueError:
        pass

def test_id_num_type_error():
    try:
        assemble_work_unit("1", "CO", "SRC", "DONE")
        assert False
    except TypeError:
        pass
    try:
        assemble_work_unit(1.0, "CO", "SRC", "DONE")
        assert False
    except TypeError:
        pass
    try:
        assemble_work_unit(True, "CO", "SRC", "DONE")
        assert False
    except TypeError:
        pass

def test_type_code_type_error():
    try:
        assemble_work_unit(1, 12, "SRC", "DONE")
        assert False
    except TypeError:
        pass

def test_source_type_error():
    try:
        assemble_work_unit(1, "CO", 123, "DONE")
        assert False
    except TypeError:
        pass

def test_completion_type_error():
    try:
        assemble_work_unit(1, "CO", "SRC", 123)
        assert False
    except TypeError:
        pass

def test_pure_function():
    r1 = assemble_work_unit(1, "CO", "SRC", "DONE")
    r2 = assemble_work_unit(1, "CO", "SRC", "DONE")
    assert r1 == r2
    assert r1 is not r2
<<<2DER:END>>>
