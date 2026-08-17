# 契約: 作業単位の 組み立て(★2DER 生成 ／ MGR は 置いただけ)

- task: TASK-2DER-9B424040 ／ ★型は v0.2:84 逐語 ／ ★completion と tests は 既存部品の 返り値
- ★build_plan は 呼ぶ たびに 別の 計画を 出す=★検査の 結果が 振れる(★2026-08-18 実測)

<<<2DER:SKELETON>>>
def create_work_unit(a, b, c, d):
    """Implement a pure function `create_work_unit(id, type, source, completion)` that returns a dictionary with keys `work_unit_id`, `type`, `source`, `dependency`, `completion`, `required_tests` in that order. `work_unit_id` must be formatted as `WU-<TypePrefix>-<ID>`, where `TypePrefix` is the first 2 characters of `type` converted to uppercase romaji, or `XX` if conversion fails. `dependency` is always `[]`. `completion` is the input argument. `required_tests` is `[completion]`. Raise `ValueError` if `id < 0` or if `type`, `source`, or `completion` is an empty string. Raise `TypeError` if `id` is not an integer or if `type`, `source`, `completion` are not strings. Use only the Python standard library. The function must be deterministic and pure.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import create_work_unit

def test_valid_japanese_type():
    result = create_work_unit(1, "作業", "出所", "完了")
    assert result["work_unit_id"] == "WU-SA-0001"
    assert result["type"] == "作業"
    assert result["source"] == "出所"
    assert result["dependency"] == []
    assert result["completion"] == "完了"
    assert result["required_tests"] == ["完了"]
    keys = list(result.keys())
    assert keys == ["work_unit_id", "type", "source", "dependency", "completion", "required_tests"]

def test_valid_non_japanese_type():
    result = create_work_unit(2, "Type", "Source", "Done")
    assert result["work_unit_id"] == "WU-XX-0002"
    assert result["type"] == "Type"
    assert result["source"] == "Source"
    assert result["dependency"] == []
    assert result["completion"] == "Done"
    assert result["required_tests"] == ["Done"]

def test_id_negative():
    try:
        create_work_unit(-1, "型", "出所", "完了")
        assert False
    except ValueError:
        pass

def test_empty_type():
    try:
        create_work_unit(1, "", "出所", "完了")
        assert False
    except ValueError:
        pass

def test_empty_source():
    try:
        create_work_unit(1, "型", "", "完了")
        assert False
    except ValueError:
        pass

def test_empty_completion():
    try:
        create_work_unit(1, "型", "出所", "")
        assert False
    except ValueError:
        pass

def test_wrong_type_id():
    try:
        create_work_unit("1", "型", "出所", "完了")
        assert False
    except TypeError:
        pass

def test_wrong_type_type():
    try:
        create_work_unit(1, 123, "出所", "完了")
        assert False
    except TypeError:
        pass

def test_wrong_type_source():
    try:
        create_work_unit(1, "型", 123, "完了")
        assert False
    except TypeError:
        pass

def test_wrong_type_completion():
    try:
        create_work_unit(1, "型", "出所", 123)
        assert False
    except TypeError:
        pass

def test_short_type():
    result = create_work_unit(1, "A", "出所", "完了")
    assert result["work_unit_id"] == "WU-XX-0001"

def test_id_zero():
    result = create_work_unit(0, "型", "出所", "完了")
    assert result["work_unit_id"] == "WU-KA-0000"

def test_determinism():
    r1 = create_work_unit(1, "作業", "出所", "完了")
    r2 = create_work_unit(1, "作業", "出所", "完了")
    assert r1 == r2
<<<2DER:END>>>
