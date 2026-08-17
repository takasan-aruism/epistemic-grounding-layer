# 契約: 根拠の 判定 v2(★2DER 生成 ／ ★依頼文の 穴を 塞いだ 版)

- 台帳: ITEM-2DER-EVO-0071 ／ task: TASK-2DER-C5C27913
- ★前回(TASK-2DER-06DAE71E)は ★大文字小文字の 規則を 私が 書かず ★封印試験が 勝手に 決めて 落ちた

<<<2DER:SKELETON>>>
def verify_material(a, b, c):
    """Create a function `verify_material(text, terms, count)` in `impl.py`. Inputs: `text` (str), `terms` (list of str), `count` (int or None). Logic: 1. If `text` is empty string, return `('NO_MATERIAL', count, 0)`. 2. If `count` is None, return `('UNVERIFIED', count, 0)`. 3. For each term in `terms`, count occurrences in `text` (case-sensitive, partial match). 4. Sum occurrences. 5. If sum > 0, status is `ESTABLISHED`. Else `CONDITION_NOT_MET`. 6. Return `(status, count, found_count)`. Pure function, standard library only.
    ★実装前に 引いた 名前の 検査(★機械が 書いた): ★計画が 区間を 名乗っていない(`serves_segment` が 空)=★★比べる 相手が 無い ∴ ★この 検査は 効いていない
    """
    <<<FILL: ここに実装>>>
<<<2DER:END>>>
<<<2DER:IMMUTABLE_TESTS>>>
from impl import verify_material

def test_empty_text():
    result = verify_material('', ['term'], 1)
    assert result == ('NO_MATERIAL', 1, 0)

def test_none_count():
    result = verify_material('text', ['term'], None)
    assert result == ('UNVERIFIED', None, 0)

def test_established():
    result = verify_material('apple', ['app'], 1)
    assert result == ('ESTABLISHED', 1, 1)

def test_condition_not_met():
    result = verify_material('banana', ['app'], 1)
    assert result == ('CONDITION_NOT_MET', 1, 0)

def test_case_sensitive():
    result = verify_material('Apple', ['apple'], 1)
    assert result == ('CONDITION_NOT_MET', 1, 0)

def test_partial_match():
    result = verify_material('pineapple', ['apple'], 1)
    assert result == ('ESTABLISHED', 1, 1)

def test_multiple_terms():
    result = verify_material('a b c', ['a', 'x'], 1)
    assert result == ('ESTABLISHED', 1, 1)

def test_found_count():
    result = verify_material('a a', ['a'], 1)
    assert result == ('ESTABLISHED', 1, 2)

def test_empty_terms():
    result = verify_material('text', [], 1)
    assert result == ('CONDITION_NOT_MET', 1, 0)
<<<2DER:END>>>
