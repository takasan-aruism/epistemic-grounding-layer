# 契約: 複数役の 振り分け(★2DER が 生成 ／ MGR は 置いただけ)

- 台帳: ITEM-2DER-EVO-0071 ／ task: TASK-2DER-E0E11C86 ／ ★根拠=v0.2 L65-66(Worker 集合・相互検算)

<<<2DER:SKELETON>>>
def find_roles(a):
    """Implement a pure function `find_roles(text: str) -> List[Tuple[str, str]]` in `impl.py`. The function must scan `text` for the keywords '経路', '環境', '契約', '失敗', '外部'. Map them to 'ROUTE', 'ENV', 'SUCCESS', 'FAILURE', 'EXTERNAL' respectively. Return a list of tuples `(word, role)` for every occurrence found. The list must be sorted by the fixed order of keywords: 経路, 環境, 契約, 失敗, 外部. If no keywords are found, return an empty list. The function must be deterministic and use only the standard library.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
import os
import json

from impl import find_roles


def test_empty_input():
    result = find_roles("")
    assert result == []


def test_no_keywords():
    result = find_roles("こんにちは世界")
    assert result == []


def test_single_keyword():
    result = find_roles("経路探索")
    assert result == [("経路", "ROUTE")]


def test_multiple_keywords_order():
    result = find_roles("外部環境失敗")
    expected = [("環境", "ENV"), ("失敗", "FAILURE"), ("外部", "EXTERNAL")]
    assert result == expected


def test_duplicate_keywords():
    result = find_roles("経路経路")
    assert result == [("経路", "ROUTE"), ("経路", "ROUTE")]


def test_all_keywords():
    text = "経路環境契約失敗外部"
    result = find_roles(text)
    expected = [
        ("経路", "ROUTE"),
        ("環境", "ENV"),
        ("契約", "SUCCESS"),
        ("失敗", "FAILURE"),
        ("外部", "EXTERNAL"),
    ]
    assert result == expected


def test_missing_file():
    assert not os.path.exists("nonexistent_file.txt")


def test_malformed_json():
    try:
        json.loads("{invalid}")
        assert False
    except json.JSONDecodeError:
        assert True

<<<2DER:END>>>
